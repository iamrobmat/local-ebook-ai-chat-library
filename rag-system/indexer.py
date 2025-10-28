"""
Indexer module for processing EPUB books and generating embeddings.
Scans EPUB files, chunks text, generates embeddings, and stores in ChromaDB.
"""
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import hashlib
import json
from datetime import datetime
import time

import chromadb
from chromadb.config import Settings
from openai import OpenAI
from tqdm import tqdm

from config import SystemConfig, get_config
from epub_parser import EPUBParser, BookMetadata, Chapter


@dataclass
class TextChunk:
    """Represents a chunk of text for embedding."""
    text: str
    chunk_type: str  # "chapter" or "paragraph"
    book_title: str
    book_author: str
    chapter_title: Optional[str] = None
    chapter_number: Optional[int] = None
    chunk_index: int = 0
    word_count: int = 0

    def to_metadata(self) -> Dict:
        """Convert to ChromaDB metadata format."""
        return {
            "chunk_type": self.chunk_type,
            "book_title": self.book_title,
            "book_author": self.book_author,
            "chapter_title": self.chapter_title or "",
            "chapter_number": self.chapter_number or 0,
            "chunk_index": self.chunk_index,
            "word_count": self.word_count
        }

    def to_id(self) -> str:
        """Generate unique ID for this chunk."""
        base = f"{self.book_author}_{self.book_title}_{self.chunk_type}"
        if self.chunk_type == "chapter":
            return f"{base}_ch{self.chapter_number}"
        else:
            return f"{base}_ch{self.chapter_number}_p{self.chunk_index}"


class IndexStatus:
    """Manages the index status JSON file."""

    def __init__(self, status_file: Path):
        self.status_file = status_file
        self.data = self._load()

    def _load(self) -> Dict:
        """Load status from file."""
        if self.status_file.exists():
            with open(self.status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "indexed_books": {},
            "total_indexed": 0,
            "last_update": None
        }

    def save(self):
        """Save status to file."""
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def is_indexed(self, book_key: str, file_hash: str) -> bool:
        """Check if book is already indexed with current hash."""
        if book_key not in self.data["indexed_books"]:
            return False
        return self.data["indexed_books"][book_key].get("file_hash") == file_hash

    def add_book(self, book_key: str, file_path: str, file_hash: str,
                 chapters: int, paragraphs: int):
        """Add or update book in index."""
        self.data["indexed_books"][book_key] = {
            "indexed_at": datetime.now().isoformat(),
            "chapters": chapters,
            "paragraphs": paragraphs,
            "file_hash": file_hash,
            "file_path": str(file_path)
        }
        self.data["total_indexed"] = len(self.data["indexed_books"])
        self.data["last_update"] = datetime.now().isoformat()

    def get_stats(self) -> Dict:
        """Get indexing statistics."""
        total_chapters = sum(b.get("chapters", 0) for b in self.data["indexed_books"].values())
        total_paragraphs = sum(b.get("paragraphs", 0) for b in self.data["indexed_books"].values())
        return {
            "total_books": self.data["total_indexed"],
            "total_chapters": total_chapters,
            "total_paragraphs": total_paragraphs,
            "last_update": self.data["last_update"]
        }


class Chunker:
    """Handles text chunking according to strategy."""

    def __init__(self, config: SystemConfig):
        self.config = config

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (words * 1.3)."""
        return int(len(text.split()) * 1.3)

    def chunk_chapter(self, chapter: Chapter, metadata: BookMetadata) -> List[TextChunk]:
        """
        Chunk a chapter into appropriate sizes.

        Args:
            chapter: Chapter object
            metadata: Book metadata

        Returns:
            List of TextChunk objects
        """
        chunks = []
        tokens = self._estimate_tokens(chapter.content)

        # If chapter is within limits, return as single chunk
        if (tokens >= self.config.chunking.chapter_min_tokens and
            tokens <= self.config.chunking.chapter_max_tokens):
            chunks.append(TextChunk(
                text=chapter.content,
                chunk_type="chapter",
                book_title=metadata.title,
                book_author=metadata.author,
                chapter_title=chapter.title,
                chapter_number=chapter.chapter_number,
                chunk_index=0,
                word_count=chapter.word_count
            ))

        # Also create paragraph chunks
        paragraphs = chapter.content.split('\n\n')
        current_chunk = []
        current_tokens = 0
        chunk_index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_tokens = self._estimate_tokens(para)

            # If adding this paragraph exceeds max, save current chunk
            if (current_tokens + para_tokens > self.config.chunking.paragraph_max_tokens and
                current_chunk):
                chunk_text = ' '.join(current_chunk)
                if self._estimate_tokens(chunk_text) >= self.config.chunking.paragraph_min_tokens:
                    chunks.append(TextChunk(
                        text=chunk_text,
                        chunk_type="paragraph",
                        book_title=metadata.title,
                        book_author=metadata.author,
                        chapter_title=chapter.title,
                        chapter_number=chapter.chapter_number,
                        chunk_index=chunk_index,
                        word_count=len(chunk_text.split())
                    ))
                    chunk_index += 1
                current_chunk = []
                current_tokens = 0

            current_chunk.append(para)
            current_tokens += para_tokens

        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            if self._estimate_tokens(chunk_text) >= self.config.chunking.paragraph_min_tokens:
                chunks.append(TextChunk(
                    text=chunk_text,
                    chunk_type="paragraph",
                    book_title=metadata.title,
                    book_author=metadata.author,
                    chapter_title=chapter.title,
                    chapter_number=chapter.chapter_number,
                    chunk_index=chunk_index,
                    word_count=len(chunk_text.split())
                ))

        return chunks


class EmbeddingGenerator:
    """Generates embeddings using OpenAI API."""

    def __init__(self, config: SystemConfig):
        self.config = config
        self.client = OpenAI(api_key=config.openai.api_key)

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate number of tokens in text.
        Simple approximation: 1 token ≈ 4 characters for English.
        """
        return len(text) // 4

    def _split_into_token_limited_batches(self, texts: List[str], max_tokens: int = 5500) -> List[List[str]]:
        """
        Split texts into batches that don't exceed token limit.

        Args:
            texts: List of text strings
            max_tokens: Maximum tokens per batch (default 5500, safe margin below 8192 limit)

        Returns:
            List of batches
        """
        batches = []
        current_batch = []
        current_tokens = 0

        for text in texts:
            text_tokens = self._estimate_tokens(text)

            # If single text exceeds limit, truncate it
            if text_tokens > max_tokens:
                # Truncate to fit within limit
                chars_limit = max_tokens * 4
                text = text[:chars_limit]
                text_tokens = max_tokens

            # If adding this text would exceed limit, start new batch
            if current_tokens + text_tokens > max_tokens and current_batch:
                batches.append(current_batch)
                current_batch = [text]
                current_tokens = text_tokens
            else:
                current_batch.append(text)
                current_tokens += text_tokens

        # Add final batch
        if current_batch:
            batches.append(current_batch)

        return batches

    def _generate_embeddings_with_adaptive_batching(self, texts: List[str], max_tokens: int) -> List[List[float]]:
        """
        Generate embeddings with a specific token limit.

        Args:
            texts: List of text strings
            max_tokens: Maximum tokens per batch

        Returns:
            List of embedding vectors
        """
        embeddings = []
        batches = self._split_into_token_limited_batches(texts, max_tokens=max_tokens)

        for batch in batches:
            for attempt in range(self.config.openai.max_retries):
                try:
                    response = self.client.embeddings.create(
                        model=self.config.openai.embedding_model,
                        input=batch
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    embeddings.extend(batch_embeddings)
                    break

                except Exception as e:
                    if attempt == self.config.openai.max_retries - 1:
                        raise
                    time.sleep(2 ** attempt)

        return embeddings

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts with adaptive batch sizing.

        Automatically reduces batch size if token limit is exceeded.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        # Try different token limits (adaptive chunking)
        token_limits = [5500, 4000, 3000, 2000, 1500]

        last_error = None
        for max_tokens in token_limits:
            try:
                return self._generate_embeddings_with_adaptive_batching(texts, max_tokens)
            except Exception as e:
                error_msg = str(e)
                last_error = e

                # If it's a token limit error, try with smaller chunks
                if "maximum context length" in error_msg or "token" in error_msg.lower():
                    if max_tokens != token_limits[-1]:  # Not the last limit
                        continue  # Try next smaller limit

                # For other errors or last limit - re-raise
                raise

        # Should never reach here, but just in case
        raise last_error


class BookIndexer:
    """Main indexer class for processing EPUB books."""

    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or get_config()

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.config.paths.chromadb_dir)
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.config.chromadb.collection_name,
            metadata={"hnsw:space": self.config.chromadb.distance_metric}
        )

        # Initialize components
        self.chunker = Chunker(self.config)
        self.embedding_generator = EmbeddingGenerator(self.config)
        self.index_status = IndexStatus(self.config.paths.index_status_file)

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _find_epub_files(self) -> List[Path]:
        """Find all EPUB files in the books directory."""
        epub_files = []

        # Search recursively for .epub files
        for path in self.config.paths.books_root.rglob("*.epub"):
            # Skip files in rag-system folder
            if "rag-system" not in str(path):
                epub_files.append(path)

        return sorted(epub_files)

    def _get_book_key(self, metadata: BookMetadata) -> str:
        """Generate unique key for book."""
        return f"{metadata.author}/{metadata.title}"

    def index_book(self, epub_path: Path, force: bool = False) -> Tuple[int, int]:
        """
        Index a single EPUB book.

        Args:
            epub_path: Path to EPUB file
            force: Force reindexing even if already indexed

        Returns:
            Tuple of (chapters_count, paragraphs_count)
        """
        # Calculate file hash
        file_hash = self._calculate_file_hash(epub_path)

        # Parse EPUB
        parser = EPUBParser(epub_path)
        metadata = parser.get_metadata()
        chapters = parser.extract_chapters()

        book_key = self._get_book_key(metadata)

        # Check if already indexed
        if not force and self.index_status.is_indexed(book_key, file_hash):
            return (0, 0)  # Already indexed

        # Process chapters into chunks
        all_chunks = []
        for chapter in chapters:
            chunks = self.chunker.chunk_chapter(chapter, metadata)
            all_chunks.extend(chunks)

        if not all_chunks:
            return (0, 0)

        # Generate embeddings
        texts = [chunk.text for chunk in all_chunks]
        embeddings = self.embedding_generator.generate_embeddings(texts)

        # Prepare for ChromaDB
        ids = [chunk.to_id() for chunk in all_chunks]
        metadatas = [chunk.to_metadata() for chunk in all_chunks]

        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        # Update status
        chapter_chunks = sum(1 for c in all_chunks if c.chunk_type == "chapter")
        paragraph_chunks = sum(1 for c in all_chunks if c.chunk_type == "paragraph")

        self.index_status.add_book(
            book_key=book_key,
            file_path=str(epub_path),
            file_hash=file_hash,
            chapters=chapter_chunks,
            paragraphs=paragraph_chunks
        )
        self.index_status.save()

        return (chapter_chunks, paragraph_chunks)

    def index_library(self, force: bool = False, show_progress: bool = True) -> Dict:
        """
        Index entire library of EPUB books.

        Args:
            force: Force reindexing of all books
            show_progress: Show progress bar

        Returns:
            Dict with indexing statistics
        """
        epub_files = self._find_epub_files()

        stats = {
            "total_found": len(epub_files),
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "total_chapters": 0,
            "total_paragraphs": 0
        }

        iterator = tqdm(epub_files, desc="Indexing books") if show_progress else epub_files

        for epub_path in iterator:
            try:
                chapters, paragraphs = self.index_book(epub_path, force=force)

                if chapters == 0 and paragraphs == 0:
                    stats["skipped"] += 1
                else:
                    stats["processed"] += 1
                    stats["total_chapters"] += chapters
                    stats["total_paragraphs"] += paragraphs

                if show_progress:
                    iterator.set_postfix({
                        "processed": stats["processed"],
                        "skipped": stats["skipped"]
                    })

            except Exception as e:
                stats["failed"] += 1
                print(f"\nError indexing {epub_path.name}: {e}")

        return stats

    def update_index(self, show_progress: bool = True) -> Dict:
        """
        Update index with only new or changed books.

        Args:
            show_progress: Show progress bar

        Returns:
            Dict with update statistics
        """
        return self.index_library(force=False, show_progress=show_progress)

    def clear_index(self):
        """Clear the entire index (use with caution!)."""
        self.chroma_client.delete_collection(self.config.chromadb.collection_name)
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.config.chromadb.collection_name,
            metadata={"hnsw:space": self.config.chromadb.distance_metric}
        )
        self.index_status.data = {
            "indexed_books": {},
            "total_indexed": 0,
            "last_update": None
        }
        self.index_status.save()

    def get_status(self) -> Dict:
        """Get current indexing status."""
        return self.index_status.get_stats()


if __name__ == "__main__":
    """Test indexer with a sample book."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python indexer.py <path_to_epub>")
        sys.exit(1)

    epub_path = Path(sys.argv[1])

    try:
        print("Initializing indexer...")
        indexer = BookIndexer()

        print(f"Indexing {epub_path.name}...")
        chapters, paragraphs = indexer.index_book(epub_path, force=True)

        print(f"\nSuccess!")
        print(f"  Chapter chunks: {chapters}")
        print(f"  Paragraph chunks: {paragraphs}")
        print(f"  Total chunks: {chapters + paragraphs}")

        status = indexer.get_status()
        print(f"\nOverall status:")
        print(f"  Total books: {status['total_books']}")
        print(f"  Total chapters: {status['total_chapters']}")
        print(f"  Total paragraphs: {status['total_paragraphs']}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

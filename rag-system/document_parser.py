"""
Document parser module using PyMuPDF (fitz).
Extracts chapters and text content from PDF and MOBI files.
"""
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import re

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError(
        "PyMuPDF is required for document parsing. Install it with: pip install PyMuPDF"
    )


@dataclass
class Chapter:
    """Represents a chapter from a document."""
    title: str
    content: str
    chapter_number: int
    word_count: int

    def __str__(self) -> str:
        return f"Chapter {self.chapter_number}: {self.title} ({self.word_count} words)"


@dataclass
class BookMetadata:
    """Metadata extracted from document."""
    title: str
    author: str
    language: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"


class DocumentParser:
    """Parser for PDF and MOBI files using PyMuPDF."""

    def __init__(self, doc_path: Path):
        """
        Initialize document parser.

        Args:
            doc_path: Path to the document file (PDF or MOBI)

        Raises:
            FileNotFoundError: If document file doesn't exist
            Exception: If document file cannot be read
        """
        if not doc_path.exists():
            raise FileNotFoundError(f"Document file not found: {doc_path}")

        self.doc_path = doc_path
        self.doc = None
        self._load_document()

    def _load_document(self):
        """Load the document."""
        try:
            self.doc = fitz.open(str(self.doc_path))
        except Exception as e:
            raise Exception(f"Failed to read document {self.doc_path}: {e}")

    def get_metadata(self) -> BookMetadata:
        """
        Extract metadata from the document.

        Returns:
            BookMetadata: Book metadata
        """
        metadata = self.doc.metadata

        # Get title (fallback to filename if not in metadata)
        title = metadata.get('title', '') or self.doc_path.stem
        if not title or title.strip() == '':
            title = self.doc_path.stem

        # Get author
        author = metadata.get('author', '') or "Unknown Author"
        if not author or author.strip() == '':
            author = "Unknown Author"

        # Get other metadata
        language = None  # Usually not in PDF/MOBI metadata
        publisher = metadata.get('producer', None)

        # Try to find ISBN in metadata
        isbn = None
        keywords = metadata.get('keywords', '')
        if 'isbn' in keywords.lower():
            isbn_match = re.search(r'isbn[:\s]*([0-9\-]+)', keywords, re.IGNORECASE)
            if isbn_match:
                isbn = isbn_match.group(1)

        return BookMetadata(
            title=title,
            author=author,
            language=language,
            publisher=publisher,
            isbn=isbn
        )

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw text from document

        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove hyphenation at line breaks
        text = re.sub(r'-\s+', '', text)

        # Clean up common artifacts
        text = re.sub(r'\x00', '', text)  # Remove null bytes
        text = re.sub(r'\ufeff', '', text)  # Remove BOM

        text = text.strip()
        return text

    def _detect_chapter_breaks(self, text: str) -> List[tuple[int, str, str]]:
        """
        Detect chapter breaks in text using common patterns.

        Args:
            text: Full text content

        Returns:
            List of (position, chapter_num, title) tuples
        """
        chapters = []

        # Common chapter patterns (case-insensitive)
        patterns = [
            r'(?m)^Chapter\s+(\d+|[IVXLCDM]+)[:\.\s]+(.+?)$',
            r'(?m)^CHAPTER\s+(\d+|[IVXLCDM]+)[:\.\s]+(.+?)$',
            r'(?m)^(\d+)\.\s+([A-Z][A-Za-z\s]{3,50})$',  # Numbered sections
            r'(?m)^([IVXLCDM]+)\.\s+([A-Z][A-Za-z\s]{3,50})$',  # Roman numeral sections
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                pos = match.start()
                chapter_num = match.group(1)
                chapter_title = match.group(2).strip() if len(match.groups()) > 1 else f"Chapter {chapter_num}"
                # Clean title (remove newlines, excessive spaces)
                chapter_title = re.sub(r'\s+', ' ', chapter_title)
                chapters.append((pos, chapter_num, chapter_title))

        # Sort by position
        chapters.sort(key=lambda x: x[0])

        # Remove duplicates (same position)
        unique_chapters = []
        last_pos = -1
        for pos, num, title in chapters:
            if pos != last_pos:
                unique_chapters.append((pos, num, title))
                last_pos = pos

        return unique_chapters

    def extract_chapters(self) -> List[Chapter]:
        """
        Extract all chapters from the document.

        Returns:
            List[Chapter]: List of chapters with content
        """
        # Extract full text
        full_text = ""
        for page in self.doc:
            full_text += page.get_text()

        # Clean the text
        full_text = self._clean_text(full_text)

        # Detect chapter breaks
        chapter_breaks = self._detect_chapter_breaks(full_text)

        chapters = []

        if chapter_breaks:
            # Split by detected chapters
            for i, (pos, num, title) in enumerate(chapter_breaks):
                # Get content from this chapter to next (or end)
                if i < len(chapter_breaks) - 1:
                    next_pos = chapter_breaks[i + 1][0]
                    content = full_text[pos:next_pos]
                else:
                    content = full_text[pos:]

                # Clean content
                content = self._clean_text(content)

                # Skip if too short
                if len(content) < 100:
                    continue

                word_count = len(content.split())

                chapters.append(Chapter(
                    title=title,
                    content=content,
                    chapter_number=i + 1,
                    word_count=word_count
                ))
        else:
            # No chapters detected - split by page chunks
            pages_per_chunk = 10
            total_pages = len(self.doc)

            for i in range(0, total_pages, pages_per_chunk):
                chunk_text = ""
                end_page = min(i + pages_per_chunk, total_pages)

                for page_num in range(i, end_page):
                    chunk_text += self.doc[page_num].get_text()

                chunk_text = self._clean_text(chunk_text)

                if len(chunk_text) < 100:
                    continue

                word_count = len(chunk_text.split())
                chapter_num = (i // pages_per_chunk) + 1

                chapters.append(Chapter(
                    title=f"Pages {i+1}-{end_page}",
                    content=chunk_text,
                    chapter_number=chapter_num,
                    word_count=word_count
                ))

        return chapters

    def extract_full_text(self) -> str:
        """
        Extract all text from the document as a single string.

        Returns:
            str: Full document text
        """
        full_text = ""
        for page in self.doc:
            full_text += page.get_text()
        return self._clean_text(full_text)

    def split_into_paragraphs(self, text: str, min_length: int = 50) -> List[str]:
        """
        Split text into paragraphs.

        Args:
            text: Text to split
            min_length: Minimum paragraph length in characters

        Returns:
            List[str]: List of paragraphs
        """
        # Split by double newlines or multiple spaces
        paragraphs = re.split(r'\n\n+|\r\n\r\n+', text)

        # Clean and filter paragraphs
        cleaned = []
        for para in paragraphs:
            para = para.strip()
            if len(para) >= min_length:
                cleaned.append(para)

        return cleaned

    def __del__(self):
        """Clean up: close the document."""
        if self.doc:
            self.doc.close()


def parse_document(doc_path: Path) -> tuple[BookMetadata, List[Chapter]]:
    """
    Convenience function to parse a document file (PDF or MOBI).

    Args:
        doc_path: Path to document file

    Returns:
        tuple: (BookMetadata, List[Chapter])
    """
    parser = DocumentParser(doc_path)
    metadata = parser.get_metadata()
    chapters = parser.extract_chapters()
    return metadata, chapters


if __name__ == "__main__":
    """Test document parser with a sample file."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python document_parser.py <path_to_pdf_or_mobi>")
        sys.exit(1)

    doc_path = Path(sys.argv[1])

    try:
        parser = DocumentParser(doc_path)
        metadata = parser.get_metadata()

        print(f"\n=== Book Metadata ===")
        print(f"Title: {metadata.title}")
        print(f"Author: {metadata.author}")
        print(f"Publisher: {metadata.publisher}")

        chapters = parser.extract_chapters()
        print(f"\n=== Chapters ({len(chapters)}) ===")
        for chapter in chapters[:5]:  # Show first 5
            print(f"  {chapter}")
            print(f"    Preview: {chapter.content[:100]}...")

        total_words = sum(ch.word_count for ch in chapters)
        print(f"\nTotal words: {total_words:,}")
        print(f"Total pages: {len(parser.doc)}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

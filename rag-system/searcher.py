"""
Semantic search module for querying the EPUB books database.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass

import chromadb
from openai import OpenAI

from config import SystemConfig, get_config


@dataclass
class SearchResult:
    """Represents a single search result."""
    book_title: str
    book_author: str
    chapter_title: str
    chapter_number: int
    chunk_type: str
    text: str
    similarity: float
    word_count: int

    def format_preview(self, max_length: int = 200) -> str:
        """Format text preview with ellipsis if needed."""
        if len(self.text) <= max_length:
            return self.text
        return self.text[:max_length] + "..."

    def __str__(self) -> str:
        """String representation of search result."""
        chunk_label = "Chapter" if self.chunk_type == "chapter" else "Paragraph"
        return (
            f"{self.book_title} - {self.book_author}\n"
            f"  {chunk_label}: {self.chapter_title} (Ch. {self.chapter_number})\n"
            f"  Similarity: {self.similarity:.3f}\n"
            f"  Preview: {self.format_preview()}"
        )


class BookSearcher:
    """Semantic search engine for EPUB books."""

    def __init__(self, config: Optional[SystemConfig] = None):
        """
        Initialize the searcher.

        Args:
            config: System configuration (optional)
        """
        self.config = config or get_config()

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.config.paths.chromadb_dir)
        )

        try:
            self.collection = self.chroma_client.get_collection(
                name=self.config.chromadb.collection_name
            )
        except Exception:
            raise RuntimeError(
                f"Collection '{self.config.chromadb.collection_name}' not found. "
                "Please run indexing first."
            )

        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=self.config.openai.api_key)

    def _generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for search query.

        Args:
            query: Search query text

        Returns:
            Embedding vector
        """
        response = self.openai_client.embeddings.create(
            model=self.config.openai.embedding_model,
            input=query
        )
        return response.data[0].embedding

    def _parse_result(self, result_data: Dict) -> SearchResult:
        """
        Parse ChromaDB result into SearchResult object.

        Args:
            result_data: Dictionary with result data

        Returns:
            SearchResult object
        """
        metadata = result_data["metadata"]
        return SearchResult(
            book_title=metadata["book_title"],
            book_author=metadata["book_author"],
            chapter_title=metadata["chapter_title"],
            chapter_number=metadata["chapter_number"],
            chunk_type=metadata["chunk_type"],
            text=result_data["document"],
            similarity=1 - result_data["distance"],  # Convert distance to similarity
            word_count=metadata["word_count"]
        )

    def search(
        self,
        query: str,
        n_results: Optional[int] = None,
        chunk_type: Optional[str] = None,
        author: Optional[str] = None,
        book_title: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search for books matching the query.

        Args:
            query: Search query text
            n_results: Number of results to return (default from config)
            chunk_type: Filter by chunk type ("chapter" or "paragraph")
            author: Filter by author name (partial match)
            book_title: Filter by book title (partial match)

        Returns:
            List of SearchResult objects, sorted by similarity
        """
        # Set default n_results
        if n_results is None:
            n_results = self.config.default_search_results

        # Cap at maximum
        n_results = min(n_results, self.config.max_search_results)

        # Generate query embedding
        query_embedding = self._generate_query_embedding(query)

        # Build where filter
        where_filter = {}
        if chunk_type:
            where_filter["chunk_type"] = chunk_type

        # For text filters (author, title), we need to handle partial matches differently
        # ChromaDB doesn't support LIKE queries, so we'll filter post-query
        where = where_filter if where_filter else None

        # Query ChromaDB
        # Request more results if we need to post-filter
        query_n = n_results * 3 if (author or book_title) else n_results

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=query_n,
            where=where
        )

        # Parse results
        search_results = []
        for i in range(len(results["ids"][0])):
            result_data = {
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            }
            search_results.append(self._parse_result(result_data))

        # Post-filter by author and book_title (case-insensitive partial match)
        if author:
            author_lower = author.lower()
            search_results = [
                r for r in search_results
                if author_lower in r.book_author.lower()
            ]

        if book_title:
            title_lower = book_title.lower()
            search_results = [
                r for r in search_results
                if title_lower in r.book_title.lower()
            ]

        # Limit to n_results after filtering
        search_results = search_results[:n_results]

        return search_results

    def search_by_book(
        self,
        book_title: str,
        query: str,
        n_results: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Search within a specific book.

        Args:
            book_title: Book title to search in
            query: Search query
            n_results: Number of results

        Returns:
            List of SearchResult objects
        """
        return self.search(
            query=query,
            n_results=n_results,
            book_title=book_title
        )

    def search_by_author(
        self,
        author: str,
        query: str,
        n_results: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Search within books by a specific author.

        Args:
            author: Author name to filter by
            query: Search query
            n_results: Number of results

        Returns:
            List of SearchResult objects
        """
        return self.search(
            query=query,
            n_results=n_results,
            author=author
        )

    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the indexed collection.

        Returns:
            Dict with collection statistics
        """
        count = self.collection.count()

        # Get sample to analyze
        if count > 0:
            sample = self.collection.get(limit=min(1000, count))

            # Count by chunk type
            chapter_count = sum(
                1 for m in sample["metadatas"]
                if m.get("chunk_type") == "chapter"
            )
            paragraph_count = sum(
                1 for m in sample["metadatas"]
                if m.get("chunk_type") == "paragraph"
            )

            # Get unique books
            unique_books = set(
                f"{m['book_author']} - {m['book_title']}"
                for m in sample["metadatas"]
            )

            return {
                "total_chunks": count,
                "chapters": chapter_count,
                "paragraphs": paragraph_count,
                "estimated_books": len(unique_books),
                "sample_size": len(sample["ids"])
            }

        return {
            "total_chunks": 0,
            "chapters": 0,
            "paragraphs": 0,
            "estimated_books": 0,
            "sample_size": 0
        }


def format_results(results: List[SearchResult], show_full: bool = False) -> str:
    """
    Format search results for display.

    Args:
        results: List of SearchResult objects
        show_full: Show full text instead of preview

    Returns:
        Formatted string
    """
    if not results:
        return "No results found."

    output = [f"Found {len(results)} result(s):\n"]

    for i, result in enumerate(results, 1):
        output.append(f"\n{i}. {result.book_title} - {result.book_author}")
        output.append(f"   Chapter: {result.chapter_title} (Ch. {result.chapter_number})")
        output.append(f"   Type: {result.chunk_type.capitalize()}")
        output.append(f"   Similarity: {result.similarity:.3f}")

        if show_full:
            output.append(f"   Text: {result.text}")
        else:
            output.append(f"   Preview: {result.format_preview()}")

    return "\n".join(output)


if __name__ == "__main__":
    """Test searcher with a sample query."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python searcher.py <query> [--author <name>] [--book <title>] [--type chapter|paragraph]")
        sys.exit(1)

    query = sys.argv[1]

    # Parse optional arguments
    author = None
    book_title = None
    chunk_type = None

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--author" and i + 1 < len(sys.argv):
            author = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--book" and i + 1 < len(sys.argv):
            book_title = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--type" and i + 1 < len(sys.argv):
            chunk_type = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    try:
        print("Initializing searcher...")
        searcher = BookSearcher()

        print(f"Searching for: '{query}'")
        if author:
            print(f"  Author filter: {author}")
        if book_title:
            print(f"  Book filter: {book_title}")
        if chunk_type:
            print(f"  Type filter: {chunk_type}")

        results = searcher.search(
            query=query,
            author=author,
            book_title=book_title,
            chunk_type=chunk_type,
            n_results=10
        )

        print("\n" + "="*80)
        print(format_results(results))

        # Show stats
        stats = searcher.get_collection_stats()
        print("\n" + "="*80)
        print("Collection statistics:")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Chapters: {stats['chapters']}")
        print(f"  Paragraphs: {stats['paragraphs']}")
        print(f"  Books (estimated): {stats['estimated_books']}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

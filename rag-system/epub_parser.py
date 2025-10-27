"""
EPUB parser module using ebooklib.
Extracts chapters and text content from EPUB files.
"""
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import re

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import html2text


@dataclass
class Chapter:
    """Represents a chapter from an EPUB book."""
    title: str
    content: str
    chapter_number: int
    word_count: int

    def __str__(self) -> str:
        return f"Chapter {self.chapter_number}: {self.title} ({self.word_count} words)"


@dataclass
class BookMetadata:
    """Metadata extracted from EPUB book."""
    title: str
    author: str
    language: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"


class EPUBParser:
    """Parser for EPUB files using ebooklib."""

    def __init__(self, epub_path: Path):
        """
        Initialize EPUB parser.

        Args:
            epub_path: Path to the EPUB file

        Raises:
            FileNotFoundError: If EPUB file doesn't exist
            Exception: If EPUB file cannot be read
        """
        if not epub_path.exists():
            raise FileNotFoundError(f"EPUB file not found: {epub_path}")

        self.epub_path = epub_path
        self.book = None
        self._load_book()

    def _load_book(self):
        """Load the EPUB book."""
        try:
            self.book = epub.read_epub(str(self.epub_path))
        except Exception as e:
            raise Exception(f"Failed to read EPUB file {self.epub_path}: {e}")

    def get_metadata(self) -> BookMetadata:
        """
        Extract metadata from the EPUB book.

        Returns:
            BookMetadata: Book metadata
        """
        # Get title
        title = self.book.get_metadata('DC', 'title')
        title = title[0][0] if title else self.epub_path.stem

        # Get author
        author = self.book.get_metadata('DC', 'creator')
        author = author[0][0] if author else "Unknown Author"

        # Get language
        language = self.book.get_metadata('DC', 'language')
        language = language[0][0] if language else None

        # Get publisher
        publisher = self.book.get_metadata('DC', 'publisher')
        publisher = publisher[0][0] if publisher else None

        # Get ISBN
        isbn = self.book.get_metadata('DC', 'identifier')
        isbn = isbn[0][0] if isbn else None

        return BookMetadata(
            title=title,
            author=author,
            language=language,
            publisher=publisher,
            isbn=isbn
        )

    def _html_to_text(self, html_content: str) -> str:
        """
        Convert HTML content to plain text.

        Args:
            html_content: HTML content string

        Returns:
            str: Plain text content
        """
        # Use BeautifulSoup for cleaning
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(['script', 'style', 'meta', 'link']):
            script.decompose()

        # Get text
        text = soup.get_text(separator=' ', strip=True)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def _extract_chapter_title(self, item) -> str:
        """
        Extract chapter title from EPUB item.

        Args:
            item: EPUB item

        Returns:
            str: Chapter title
        """
        # Try to get title from item
        if hasattr(item, 'title') and item.title:
            return item.title

        # Try to extract from content
        try:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            # Look for h1, h2, h3 headers
            for tag in ['h1', 'h2', 'h3', 'title']:
                header = soup.find(tag)
                if header:
                    title = header.get_text(strip=True)
                    if title:
                        return title
        except:
            pass

        # Fallback to filename
        if hasattr(item, 'file_name'):
            return Path(item.file_name).stem

        return "Untitled Chapter"

    def extract_chapters(self) -> List[Chapter]:
        """
        Extract all chapters from the EPUB book.

        Returns:
            List[Chapter]: List of chapters with content
        """
        chapters = []
        chapter_number = 0

        # Get all document items (chapters)
        items = list(self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

        for item in items:
            try:
                # Get HTML content
                html_content = item.get_content().decode('utf-8')

                # Convert to plain text
                text_content = self._html_to_text(html_content)

                # Skip if content is too short (likely not a chapter)
                if len(text_content) < 100:
                    continue

                # Extract chapter title
                title = self._extract_chapter_title(item)

                # Count words
                word_count = len(text_content.split())

                chapter_number += 1
                chapters.append(Chapter(
                    title=title,
                    content=text_content,
                    chapter_number=chapter_number,
                    word_count=word_count
                ))

            except Exception as e:
                print(f"Warning: Failed to parse item {item}: {e}")
                continue

        return chapters

    def extract_full_text(self) -> str:
        """
        Extract all text from the book as a single string.

        Returns:
            str: Full book text
        """
        chapters = self.extract_chapters()
        return "\n\n".join(chapter.content for chapter in chapters)

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


def parse_epub(epub_path: Path) -> tuple[BookMetadata, List[Chapter]]:
    """
    Convenience function to parse an EPUB file.

    Args:
        epub_path: Path to EPUB file

    Returns:
        tuple: (BookMetadata, List[Chapter])
    """
    parser = EPUBParser(epub_path)
    metadata = parser.get_metadata()
    chapters = parser.extract_chapters()
    return metadata, chapters


if __name__ == "__main__":
    """Test EPUB parser with a sample book."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python epub_parser.py <path_to_epub>")
        sys.exit(1)

    epub_path = Path(sys.argv[1])

    try:
        parser = EPUBParser(epub_path)
        metadata = parser.get_metadata()

        print(f"\n=== Book Metadata ===")
        print(f"Title: {metadata.title}")
        print(f"Author: {metadata.author}")
        print(f"Language: {metadata.language}")

        chapters = parser.extract_chapters()
        print(f"\n=== Chapters ({len(chapters)}) ===")
        for chapter in chapters[:5]:  # Show first 5
            print(f"  {chapter}")
            print(f"    Preview: {chapter.content[:100]}...")

        total_words = sum(ch.word_count for ch in chapters)
        print(f"\nTotal words: {total_words:,}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

#!/usr/bin/env python3
"""
E-book Compiler - Creates thematic EPUB books from search results.

This module allows users to compile custom e-books by searching their library
for specific topics and combining relevant passages into a new EPUB file.

Legal Notice:
- Generated e-books are for PERSONAL USE ONLY
- All passages include full citations (book, author, chapter)
- Fragment sizes are limited to comply with fair use principles
- Do NOT distribute generated e-books containing copyrighted content
"""
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from ebooklib import epub

from config import SystemConfig, get_config
from searcher import BookSearcher, SearchResult


class EbookCompiler:
    """Compiles thematic e-books from search results."""

    def __init__(self, config: Optional[SystemConfig] = None):
        """
        Initialize the e-book compiler.

        Args:
            config: System configuration (optional)
        """
        self.config = config or get_config()
        self.searcher = BookSearcher(config=self.config)

    def compile_ebook(
        self,
        query: str,
        output_path: str,
        n_results: int = 50,
        min_similarity: float = 0.7,
        max_fragment_length: int = 500,
        title: Optional[str] = None,
        group_by: str = "book",  # "book" or "topic"
        chunk_type: Optional[str] = None
    ) -> Path:
        """
        Compile an e-book from search results.

        Args:
            query: Search query to find relevant passages
            output_path: Path where to save the EPUB file
            n_results: Number of search results to include
            min_similarity: Minimum similarity score (0.0-1.0)
            max_fragment_length: Maximum characters per fragment
            title: E-book title (default: based on query)
            group_by: How to organize chapters ("book" or "topic")
            chunk_type: Filter by chunk type ("chapter" or "paragraph")

        Returns:
            Path to the generated EPUB file
        """
        # Search for relevant passages
        print(f"Searching for: '{query}'")
        results = self.searcher.search(
            query=query,
            n_results=n_results,
            chunk_type=chunk_type
        )

        # Filter by minimum similarity
        results = [r for r in results if r.similarity >= min_similarity]

        if not results:
            raise ValueError(
                f"No results found with similarity >= {min_similarity}. "
                "Try lowering the min_similarity or changing the query."
            )

        print(f"Found {len(results)} relevant passages (similarity >= {min_similarity})")

        # Generate e-book
        book_title = title or self._generate_title(query)
        epub_book = self._create_epub(
            title=book_title,
            query=query,
            results=results,
            max_fragment_length=max_fragment_length,
            group_by=group_by
        )

        # Save to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        epub.write_epub(str(output_path), epub_book)
        print(f"✓ E-book saved to: {output_path}")

        return output_path

    def _generate_title(self, query: str) -> str:
        """
        Generate e-book title from query.

        Args:
            query: Search query

        Returns:
            E-book title
        """
        # Capitalize first letter of each word
        title = query.title()

        # Add subtitle with date
        date_str = datetime.now().strftime("%B %Y")
        return f"{title}: A Curated Collection ({date_str})"

    def _create_epub(
        self,
        title: str,
        query: str,
        results: List[SearchResult],
        max_fragment_length: int,
        group_by: str
    ) -> epub.EpubBook:
        """
        Create EPUB book from search results.

        Args:
            title: Book title
            query: Original search query
            results: List of search results
            max_fragment_length: Max characters per fragment
            group_by: Grouping strategy ("book" or "topic")

        Returns:
            EpubBook object
        """
        book = epub.EpubBook()

        # Set metadata
        book.set_identifier(f"ebook-compiler-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        book.set_title(title)
        book.set_language("pl")  # Polish by default
        book.add_author("Compiled from Personal Library")
        book.add_metadata(
            "DC",
            "description",
            f"A curated collection of passages about: {query}\n\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"Total passages: {len(results)}"
        )
        book.add_metadata("DC", "publisher", "Local E-book Compiler")
        book.add_metadata("DC", "rights", "PERSONAL USE ONLY - Not for distribution")

        # Add CSS stylesheet
        style_css = self._create_stylesheet()
        book.add_item(style_css)

        # Create introduction chapter
        intro_chapter = self._create_intro_chapter(query, results)
        book.add_item(intro_chapter)

        # Group results and create chapters
        if group_by == "book":
            chapters = self._create_chapters_by_book(results, max_fragment_length)
        else:
            chapters = self._create_chapters_by_topic(results, max_fragment_length)

        for chapter in chapters:
            book.add_item(chapter)

        # Create legal disclaimer chapter
        disclaimer_chapter = self._create_disclaimer_chapter()
        book.add_item(disclaimer_chapter)

        # Define Table of Contents
        toc_items = [intro_chapter] + chapters + [disclaimer_chapter]
        book.toc = tuple(toc_items)

        # Add navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Define reading order (spine)
        book.spine = ["nav", intro_chapter] + chapters + [disclaimer_chapter]

        return book

    def _create_stylesheet(self) -> epub.EpubItem:
        """
        Create CSS stylesheet for the e-book.

        Returns:
            EpubItem with CSS content
        """
        css_content = """
        body {
            font-family: Georgia, serif;
            line-height: 1.6;
            margin: 2em;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.3em;
        }
        h2 {
            color: #34495e;
            margin-top: 1.5em;
        }
        .fragment {
            margin: 1.5em 0;
            padding: 1em;
            background-color: #f9f9f9;
            border-left: 4px solid #3498db;
        }
        .citation {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 0.5em;
            font-style: italic;
        }
        .similarity {
            font-size: 0.85em;
            color: #27ae60;
            font-weight: bold;
        }
        .intro {
            background-color: #ecf0f1;
            padding: 1.5em;
            border-radius: 5px;
            margin: 1em 0;
        }
        .disclaimer {
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            padding: 1em;
            margin: 1em 0;
            font-size: 0.9em;
        }
        """

        style = epub.EpubItem(
            uid="style",
            file_name="style/style.css",
            media_type="text/css",
            content=css_content
        )

        return style

    def _create_intro_chapter(
        self,
        query: str,
        results: List[SearchResult]
    ) -> epub.EpubHtml:
        """
        Create introduction chapter.

        Args:
            query: Search query
            results: Search results

        Returns:
            EpubHtml chapter
        """
        # Count unique books
        unique_books = set((r.book_title, r.book_author) for r in results)

        # Calculate average similarity
        avg_similarity = sum(r.similarity for r in results) / len(results)

        content = f"""
        <html>
        <head>
            <link rel="stylesheet" href="style/style.css" type="text/css"/>
        </head>
        <body>
            <h1>Introduction</h1>

            <div class="intro">
                <p><strong>Search Query:</strong> {query}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
                <p><strong>Total Passages:</strong> {len(results)}</p>
                <p><strong>Source Books:</strong> {len(unique_books)}</p>
                <p><strong>Average Relevance:</strong> {avg_similarity:.1%}</p>
            </div>

            <h2>About This E-book</h2>
            <p>
                This e-book was automatically compiled from your personal library using
                semantic search technology. Each passage was selected based on its relevance
                to your query: <em>"{query}"</em>.
            </p>

            <p>
                The passages are organized by source book, with full citations provided for
                each fragment. All content is sourced from books in your personal collection.
            </p>

            <h2>How to Use</h2>
            <ul>
                <li>Each chapter represents passages from a single source book</li>
                <li>Passages are sorted by relevance (similarity score)</li>
                <li>Citations include book title, author, and chapter information</li>
                <li>Use this as a starting point for deeper exploration of topics</li>
            </ul>

            <div class="disclaimer">
                <strong>⚠️ Legal Notice:</strong> This e-book is for PERSONAL USE ONLY.
                It contains excerpts from copyrighted works in your personal library.
                Do not distribute or share this file.
            </div>
        </body>
        </html>
        """

        chapter = epub.EpubHtml(
            title="Introduction",
            file_name="intro.xhtml",
            lang="pl"
        )
        chapter.content = content

        return chapter

    def _create_chapters_by_book(
        self,
        results: List[SearchResult],
        max_fragment_length: int
    ) -> List[epub.EpubHtml]:
        """
        Create chapters grouped by source book.

        Args:
            results: Search results
            max_fragment_length: Max characters per fragment

        Returns:
            List of EpubHtml chapters
        """
        # Group results by book
        books = defaultdict(list)
        for result in results:
            book_key = (result.book_author, result.book_title)
            books[book_key].append(result)

        # Create chapter for each book
        chapters = []
        for i, ((author, title), book_results) in enumerate(books.items(), 1):
            # Sort by similarity (highest first)
            book_results.sort(key=lambda x: x.similarity, reverse=True)

            content = self._format_book_chapter(
                author=author,
                title=title,
                results=book_results,
                max_fragment_length=max_fragment_length
            )

            chapter = epub.EpubHtml(
                title=f"{title} - {author}",
                file_name=f"chapter_{i:03d}.xhtml",
                lang="pl"
            )
            chapter.content = content
            chapters.append(chapter)

        return chapters

    def _format_book_chapter(
        self,
        author: str,
        title: str,
        results: List[SearchResult],
        max_fragment_length: int
    ) -> str:
        """
        Format chapter content for a single book.

        Args:
            author: Book author
            title: Book title
            results: Search results from this book
            max_fragment_length: Max characters per fragment

        Returns:
            HTML content
        """
        # Build fragments
        fragments_html = []
        for i, result in enumerate(results, 1):
            # Truncate text if needed
            text = result.text
            if len(text) > max_fragment_length:
                text = text[:max_fragment_length] + "..."

            # Escape HTML special characters
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            # Format as HTML
            fragment_html = f"""
            <div class="fragment">
                <p>{text}</p>
                <div class="citation">
                    <span class="similarity">Relevance: {result.similarity:.1%}</span><br/>
                    Chapter: {result.chapter_title} (Ch. {result.chapter_number})<br/>
                    Type: {result.chunk_type.capitalize()}, {result.word_count} words
                </div>
            </div>
            """
            fragments_html.append(fragment_html)

        # Build full chapter HTML
        content = f"""
        <html>
        <head>
            <link rel="stylesheet" href="style/style.css" type="text/css"/>
        </head>
        <body>
            <h1>{title}</h1>
            <h2>by {author}</h2>

            <p><em>{len(results)} relevant passage(s) found</em></p>

            {''.join(fragments_html)}
        </body>
        </html>
        """

        return content

    def _create_chapters_by_topic(
        self,
        results: List[SearchResult],
        max_fragment_length: int
    ) -> List[epub.EpubHtml]:
        """
        Create chapters grouped by topic (future feature).

        Args:
            results: Search results
            max_fragment_length: Max characters per fragment

        Returns:
            List of EpubHtml chapters
        """
        # For now, just use book grouping
        # Future: Use GPT to cluster by sub-topics
        return self._create_chapters_by_book(results, max_fragment_length)

    def _create_disclaimer_chapter(self) -> epub.EpubHtml:
        """
        Create legal disclaimer chapter.

        Returns:
            EpubHtml chapter
        """
        # Get current timestamp
        generated_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        content = f"""
        <html>
        <head>
            <link rel="stylesheet" href="style/style.css" type="text/css"/>
        </head>
        <body>
            <h1>Legal Disclaimer</h1>

            <div class="disclaimer">
                <h2>⚠️ Personal Use Only</h2>
                <p>
                    This e-book was automatically compiled from your personal library for
                    <strong>PERSONAL, EDUCATIONAL, and RESEARCH purposes ONLY</strong>.
                </p>

                <h2>Copyright Notice</h2>
                <p>
                    All passages in this e-book are excerpts from copyrighted works.
                    Each passage is clearly cited with its source (book title, author,
                    and chapter).
                </p>

                <p>
                    <strong>You may NOT:</strong>
                </p>
                <ul>
                    <li>Distribute this e-book to others</li>
                    <li>Share this e-book publicly online or offline</li>
                    <li>Use this e-book for commercial purposes</li>
                    <li>Remove or modify citation information</li>
                </ul>

                <h2>Fair Use</h2>
                <p>
                    This compilation is believed to constitute fair use under copyright law
                    for personal educational purposes. Fragment sizes are limited, and all
                    sources are properly cited.
                </p>

                <h2>Your Responsibility</h2>
                <p>
                    You are responsible for ensuring that your use of this e-book complies
                    with applicable copyright laws in your jurisdiction. The compiler tool
                    assumes no liability for misuse.
                </p>

                <h2>Generated By</h2>
                <p>
                    <strong>Local E-book AI Chat Library</strong><br/>
                    An open-source tool for personal library management<br/>
                    Generated: {generated_time}
                </p>
            </div>
        </body>
        </html>
        """

        chapter = epub.EpubHtml(
            title="Legal Disclaimer",
            file_name="disclaimer.xhtml",
            lang="pl"
        )
        chapter.content = content

        return chapter


if __name__ == "__main__":
    """Test the compiler with a sample query."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python ebook_compiler.py <query> <output_file.epub>")
        print("Example: python ebook_compiler.py 'stoicism' stoicism_collection.epub")
        sys.exit(1)

    query = sys.argv[1]
    output = sys.argv[2]

    try:
        compiler = EbookCompiler()

        result_path = compiler.compile_ebook(
            query=query,
            output_path=output,
            n_results=50,
            min_similarity=0.7
        )

        print(f"\n✓ Success! E-book created: {result_path}")
        print("\n⚠️  Remember: This e-book is for PERSONAL USE ONLY.")
        print("    Do not distribute or share it.")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

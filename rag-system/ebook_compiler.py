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
from openai import OpenAI

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
        self.openai_client = OpenAI(api_key=self.config.openai.api_key)

    def compile_ebook(
        self,
        query: str,
        output_path: str,
        n_results: int = 50,
        min_similarity: float = 0.7,
        max_fragment_length: int = 500,
        title: Optional[str] = None,
        group_by: str = "book",  # "book" or "topic"
        chunk_type: Optional[str] = None,
        translate: bool = False  # Translate to Polish
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

        # Translate fragments if requested
        if translate:
            print(f"Translating {len(results)} fragments to Polish...")
            print("This may take several minutes...")
            results = self._translate_results(results)
            print("✓ Translation complete!")

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

    def _translate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Translate search results to Polish using GPT-5-nano.

        Args:
            results: List of search results

        Returns:
            List of search results with translated text
        """
        from tqdm import tqdm

        translated_results = []

        # Translate in batches for efficiency
        for i, result in enumerate(tqdm(results, desc="Translating"), 1):
            try:
                # Truncate text BEFORE translation (max 3000 chars to avoid API limits)
                text_to_translate = result.text
                max_length = 3000  # Safe limit for GPT-5-nano
                if len(text_to_translate) > max_length:
                    text_to_translate = text_to_translate[:max_length] + "..."
                    print(f"\n⚠️  Fragment {i} truncated: {len(result.text)} → {len(text_to_translate)} chars")

                # Translate the text
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",  # Using GPT-4o-mini (GPT-5-nano returns empty responses)
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional translator. Translate the following English text to Polish. Maintain the original meaning, tone, and formatting. Only output the translation, nothing else."
                        },
                        {
                            "role": "user",
                            "content": text_to_translate  # Use truncated text
                        }
                    ],
                    temperature=0.3,
                    max_tokens=4000
                )

                translated_text = response.choices[0].message.content.strip() if response.choices[0].message.content else ""

                # Create new SearchResult with translated text
                translated_result = SearchResult(
                    book_title=result.book_title,
                    book_author=result.book_author,
                    chapter_title=result.chapter_title,
                    chapter_number=result.chapter_number,
                    chunk_type=result.chunk_type,
                    text=translated_text,  # Use translated text
                    similarity=result.similarity,
                    word_count=result.word_count
                )
                translated_results.append(translated_result)

            except Exception as e:
                print(f"\n⚠️  Translation failed for fragment {i}: {e}")
                print("Using original English text for this fragment.")
                translated_results.append(result)  # Keep original if translation fails

        return translated_results

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

        # Create Table of Contents chapter (before content chapters)
        toc_chapter = self._create_toc_chapter(chapters)
        book.add_item(toc_chapter)

        for chapter in chapters:
            book.add_item(chapter)

        # Create legal disclaimer chapter
        disclaimer_chapter = self._create_disclaimer_chapter()
        book.add_item(disclaimer_chapter)

        # Define Table of Contents
        toc_items = [intro_chapter, toc_chapter] + chapters + [disclaimer_chapter]
        book.toc = tuple(toc_items)

        # Add navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Define reading order (spine)
        book.spine = ["nav", intro_chapter, toc_chapter] + chapters + [disclaimer_chapter]

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
            <h1>Wprowadzenie</h1>

            <div class="intro">
                <p><strong>Zapytanie:</strong> {query}</p>
                <p><strong>Wygenerowano:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
                <p><strong>Liczba fragmentów:</strong> {len(results)}</p>
                <p><strong>Książki źródłowe:</strong> {len(unique_books)}</p>
                <p><strong>Średnie dopasowanie:</strong> {avg_similarity:.1%}</p>
            </div>

            <h2>O tym e-booku</h2>
            <p>
                Ten e-book został automatycznie skompilowany z Twojej osobistej biblioteki
                przy użyciu technologii semantic search. Każdy fragment został wybrany na
                podstawie jego trafności do zapytania: <em>"{query}"</em>.
            </p>

            <p>
                Fragmenty są zorganizowane według książek źródłowych, z pełnymi cytatami
                dla każdego fragmentu. Cała treść pochodzi z książek z Twojej osobistej kolekcji.
            </p>

            <h2>Jak używać</h2>
            <ul>
                <li>Każdy rozdział zawiera fragmenty z jednej książki źródłowej</li>
                <li>Fragmenty są sortowane według trafności (współczynnik podobieństwa)</li>
                <li>Cytaty zawierają tytuł książki, autora i informacje o rozdziale</li>
                <li>Użyj tego jako punktu wyjścia do głębszej eksploracji tematów</li>
            </ul>

            <div class="disclaimer">
                <strong>⚠️ Uwaga prawna:</strong> Ten e-book jest TYLKO DO UŻYTKU OSOBISTEGO.
                Zawiera fragmenty dzieł chronionych prawem autorskim z Twojej osobistej biblioteki.
                Nie rozpowszechniaj ani nie udostępniaj tego pliku.
            </div>
        </body>
        </html>
        """

        chapter = epub.EpubHtml(
            title="Wprowadzenie",
            file_name="intro.xhtml",
            lang="pl"
        )
        chapter.content = content

        return chapter

    def _create_toc_chapter(self, chapters: List[epub.EpubHtml]) -> epub.EpubHtml:
        """
        Create Table of Contents chapter as a full page.

        Args:
            chapters: List of content chapters

        Returns:
            EpubHtml chapter with TOC
        """
        # Build TOC items
        toc_items_html = []
        for i, chapter in enumerate(chapters, 1):
            toc_items_html.append(
                f'<li><a href="{chapter.file_name}">{i}. {chapter.title}</a></li>'
            )

        content = f"""
        <html>
        <head>
            <link rel="stylesheet" href="style/style.css" type="text/css"/>
            <style>
                .toc {{
                    margin: 2em 0;
                }}
                .toc h1 {{
                    text-align: center;
                    margin-bottom: 1em;
                }}
                .toc ol {{
                    list-style: decimal;
                    padding-left: 2em;
                    line-height: 1.8;
                }}
                .toc li {{
                    margin: 0.5em 0;
                }}
                .toc a {{
                    text-decoration: none;
                    color: #2c3e50;
                }}
                .toc a:hover {{
                    text-decoration: underline;
                    color: #3498db;
                }}
            </style>
        </head>
        <body>
            <div class="toc">
                <h1>Spis treści</h1>
                <p><em>Łącznie {len(chapters)} książek źródłowych</em></p>
                <ol>
                    {''.join(toc_items_html)}
                </ol>
            </div>
        </body>
        </html>
        """

        chapter = epub.EpubHtml(
            title="Spis treści",
            file_name="toc_page.xhtml",
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

            # Get chapter titles from results for TOC
            chapter_titles = list(set(r.chapter_title for r in book_results))
            if len(chapter_titles) == 1:
                # Single chapter - use its title
                toc_title = f"{chapter_titles[0]} ({title})"
            else:
                # Multiple chapters - use book title with count
                toc_title = f"{title} ({len(chapter_titles)} rozdziałów)"

            content = self._format_book_chapter(
                author=author,
                title=title,
                results=book_results,
                max_fragment_length=max_fragment_length
            )

            chapter = epub.EpubHtml(
                title=toc_title,
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

            # Translate chunk type to Polish
            chunk_type_pl = "Rozdział" if result.chunk_type == "chapter" else "Paragraf"

            # Format as HTML
            fragment_html = f"""
            <div class="fragment">
                <p>{text}</p>
                <div class="citation">
                    <span class="similarity">Trafność: {result.similarity:.1%}</span><br/>
                    Rozdział: {result.chapter_title} (Rozdz. {result.chapter_number})<br/>
                    Typ: {chunk_type_pl}, {result.word_count} słów
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
            <h2>autor: {author}</h2>

            <p><em>Znaleziono {len(results)} trafny(ch) fragment(ów)</em></p>

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
            <h1>Zastrzeżenia prawne</h1>

            <div class="disclaimer">
                <h2>⚠️ Tylko do użytku osobistego</h2>
                <p>
                    Ten e-book został automatycznie skompilowany z Twojej osobistej biblioteki
                    <strong>WYŁĄCZNIE do celów OSOBISTYCH, EDUKACYJNYCH i BADAWCZYCH</strong>.
                </p>

                <h2>Prawa autorskie</h2>
                <p>
                    Wszystkie fragmenty w tym e-booku to fragmenty dzieł chronionych prawem autorskim.
                    Każdy fragment jest wyraźnie oznaczony źródłem (tytuł książki, autor i rozdział).
                </p>

                <p>
                    <strong>NIE wolno Ci:</strong>
                </p>
                <ul>
                    <li>Dystrybuować tego e-booka innym osobom</li>
                    <li>Udostępniać tego e-booka publicznie online lub offline</li>
                    <li>Używać tego e-booka do celów komercyjnych</li>
                    <li>Usuwać lub modyfikować informacji o źródłach</li>
                </ul>

                <h2>Fair Use</h2>
                <p>
                    Ta kompilacja jest uznawana za fair use zgodnie z prawem autorskim
                    dla osobistych celów edukacyjnych. Rozmiary fragmentów są ograniczone,
                    a wszystkie źródła są odpowiednio cytowane.
                </p>

                <h2>Twoja odpowiedzialność</h2>
                <p>
                    Jesteś odpowiedzialny za zapewnienie, że Twoje użycie tego e-booka
                    jest zgodne z obowiązującymi przepisami prawa autorskiego w Twojej jurysdykcji.
                    Narzędzie kompilatora nie ponosi odpowiedzialności za niewłaściwe użycie.
                </p>

                <h2>Wygenerowano przez</h2>
                <p>
                    <strong>Local E-book AI Chat Library</strong><br/>
                    Narzędzie open-source do zarządzania osobistą biblioteką<br/>
                    Wygenerowano: {generated_time}
                </p>
            </div>
        </body>
        </html>
        """

        chapter = epub.EpubHtml(
            title="Zastrzeżenia prawne",
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

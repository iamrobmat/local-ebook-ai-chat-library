#!/usr/bin/env python3
"""
Command-line interface for the EPUB Books RAG System.
"""
import sys
from pathlib import Path

import click

from config import get_config
from indexer import BookIndexer
from searcher import BookSearcher, format_results


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    EPUB Books RAG System - Semantic search for your book library.

    Use this CLI to index your EPUB books and perform semantic searches.
    """
    pass


@cli.command()
def init():
    """Initialize the system and verify configuration."""
    click.echo("Initializing EPUB Books RAG System...")

    try:
        config = get_config()
        click.echo(f"✓ Configuration loaded successfully")
        click.echo(f"  Books directory: {config.paths.books_root}")
        click.echo(f"  Data directory: {config.paths.data_dir}")
        click.echo(f"  ChromaDB directory: {config.paths.chromadb_dir}")

        # Create directories
        config.paths.data_dir.mkdir(parents=True, exist_ok=True)
        click.echo(f"✓ Data directory created")

        # Test OpenAI connection
        from openai import OpenAI
        client = OpenAI(api_key=config.openai.api_key)
        response = client.embeddings.create(
            model=config.openai.embedding_model,
            input="test"
        )
        click.echo(f"✓ OpenAI API connection successful")
        click.echo(f"  Model: {config.openai.embedding_model}")
        click.echo(f"  Embedding dimensions: {len(response.data[0].embedding)}")

        click.echo("\n✓ System initialized successfully!")
        click.echo("\nNext steps:")
        click.echo("  1. Run 'python cli.py index --full' to index your library")
        click.echo("  2. Run 'python cli.py search \"your query\"' to search")

    except Exception as e:
        click.echo(f"✗ Initialization failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--full', is_flag=True, help='Index all books (including already indexed)')
@click.option('--force', is_flag=True, help='Force reindexing (same as --full)')
@click.option('--book', type=str, help='Index specific book by path')
def index(full, force, book):
    """Index EPUB books in the library."""
    try:
        indexer = BookIndexer()

        if book:
            # Index single book
            book_path = Path(book)
            if not book_path.exists():
                click.echo(f"✗ Book not found: {book}", err=True)
                sys.exit(1)

            click.echo(f"Indexing {book_path.name}...")
            chapters, paragraphs = indexer.index_book(book_path, force=True)

            if chapters == 0 and paragraphs == 0:
                click.echo("✓ Book was already indexed (use --force to reindex)")
            else:
                click.echo(f"✓ Indexed successfully!")
                click.echo(f"  Chapter chunks: {chapters}")
                click.echo(f"  Paragraph chunks: {paragraphs}")
                click.echo(f"  Total chunks: {chapters + paragraphs}")

        else:
            # Index library
            force_reindex = full or force

            if force_reindex:
                click.echo("Indexing entire library (this may take a while)...")
            else:
                click.echo("Updating index with new books...")

            stats = indexer.index_library(force=force_reindex, show_progress=True)

            click.echo(f"\n✓ Indexing complete!")
            click.echo(f"  Total books found: {stats['total_found']}")
            click.echo(f"  Processed: {stats['processed']}")
            click.echo(f"  Skipped (already indexed): {stats['skipped']}")
            if stats['failed'] > 0:
                click.echo(f"  Failed: {stats['failed']}")
            click.echo(f"  Total chapter chunks: {stats['total_chapters']}")
            click.echo(f"  Total paragraph chunks: {stats['total_paragraphs']}")

    except Exception as e:
        click.echo(f"✗ Indexing failed: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
def update():
    """Update index with new or changed books."""
    try:
        indexer = BookIndexer()

        click.echo("Scanning for new or changed books...")
        stats = indexer.update_index(show_progress=True)

        if stats['processed'] == 0:
            click.echo("\n✓ No new books found. Index is up to date.")
        else:
            click.echo(f"\n✓ Update complete!")
            click.echo(f"  New books indexed: {stats['processed']}")
            click.echo(f"  Total chapter chunks: {stats['total_chapters']}")
            click.echo(f"  Total paragraph chunks: {stats['total_paragraphs']}")

    except Exception as e:
        click.echo(f"✗ Update failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('query')
@click.option('--top', '-n', default=10, help='Number of results to return')
@click.option('--level', type=click.Choice(['chapter', 'paragraph', 'both']),
              default='both', help='Search in chapters, paragraphs, or both')
@click.option('--author', type=str, help='Filter by author name')
@click.option('--book', type=str, help='Filter by book title')
@click.option('--full', is_flag=True, help='Show full text instead of preview')
def search(query, top, level, author, book, full):
    """Search for books matching the query."""
    try:
        searcher = BookSearcher()

        # Determine chunk_type filter
        chunk_type = None if level == 'both' else level

        click.echo(f"Searching for: '{query}'")
        if author:
            click.echo(f"  Author filter: {author}")
        if book:
            click.echo(f"  Book filter: {book}")
        if level != 'both':
            click.echo(f"  Level: {level}")

        results = searcher.search(
            query=query,
            n_results=top,
            chunk_type=chunk_type,
            author=author,
            book_title=book
        )

        click.echo("\n" + "="*80)
        click.echo(format_results(results, show_full=full))

    except RuntimeError as e:
        click.echo(f"✗ {e}", err=True)
        click.echo("\nPlease run 'python cli.py index --full' first.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Search failed: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
def status():
    """Show indexing status and statistics."""
    try:
        # Try to get status from indexer
        indexer = BookIndexer()
        stats = indexer.get_status()

        click.echo("=== Index Status ===\n")
        click.echo(f"Total books indexed: {stats['total_books']}")
        click.echo(f"Total chapter chunks: {stats['total_chapters']}")
        click.echo(f"Total paragraph chunks: {stats['total_paragraphs']}")
        click.echo(f"Total chunks: {stats['total_chapters'] + stats['total_paragraphs']}")

        if stats['last_update']:
            from datetime import datetime
            last_update = datetime.fromisoformat(stats['last_update'])
            click.echo(f"Last update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            click.echo("Last update: Never")

        # Try to get collection stats
        try:
            searcher = BookSearcher()
            collection_stats = searcher.get_collection_stats()

            click.echo("\n=== Collection Statistics ===\n")
            click.echo(f"Total chunks in database: {collection_stats['total_chunks']}")
            click.echo(f"Chapter chunks: {collection_stats['chapters']}")
            click.echo(f"Paragraph chunks: {collection_stats['paragraphs']}")

            # Calculate database size
            config = get_config()
            db_path = config.paths.chromadb_dir
            if db_path.exists():
                total_size = sum(f.stat().st_size for f in db_path.rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)
                click.echo(f"Database size: {size_mb:.1f} MB")

        except RuntimeError:
            click.echo("\n(Collection not yet created - run indexing first)")

    except Exception as e:
        click.echo(f"✗ Failed to get status: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to clear the entire index?')
def clear():
    """Clear the entire index (use with caution!)."""
    try:
        indexer = BookIndexer()
        indexer.clear_index()
        click.echo("✓ Index cleared successfully")

    except Exception as e:
        click.echo(f"✗ Failed to clear index: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('book_path', type=click.Path(exists=True))
def reindex(book_path):
    """Reindex a specific book."""
    try:
        indexer = BookIndexer()
        book_path = Path(book_path)

        click.echo(f"Reindexing {book_path.name}...")
        chapters, paragraphs = indexer.index_book(book_path, force=True)

        click.echo(f"✓ Reindexed successfully!")
        click.echo(f"  Chapter chunks: {chapters}")
        click.echo(f"  Paragraph chunks: {paragraphs}")
        click.echo(f"  Total chunks: {chapters + paragraphs}")

    except Exception as e:
        click.echo(f"✗ Reindexing failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('question')
@click.option('--top', '-n', default=5, help='Number of passages to use for context')
def ask(question, top):
    """Ask a question and get an AI-generated answer based on your books."""
    try:
        from answerer import BookAnswerer

        click.echo(f"Pytanie: {question}\n")
        click.echo("Przeszukuję książki i generuję odpowiedź...\n")

        answerer = BookAnswerer()
        answer = answerer.ask(question, n_results=top)

        # Display answer
        click.echo("=" * 70)
        click.echo("ODPOWIEDŹ:")
        click.echo("=" * 70)
        click.echo(answer.text)
        click.echo()

        # Display sources
        if answer.sources:
            click.echo("=" * 70)
            click.echo(f"ŹRÓDŁA ({len(answer.sources)} fragmentów):")
            click.echo("=" * 70)
            for i, source in enumerate(answer.sources, 1):
                click.echo(f"\n[{i}] \"{source.book_title}\" - {source.book_author}")
                if source.chapter_title:
                    click.echo(f"    Rozdział: {source.chapter_title}")
                click.echo(f"    Podobieństwo: {source.similarity:.3f}")
                click.echo(f"    Typ: {source.chunk_type}")
                # Show preview of the text
                preview = source.text[:200] + "..." if len(source.text) > 200 else source.text
                click.echo(f"    Podgląd: {preview}")

    except Exception as e:
        click.echo(f"✗ Nie udało się wygenerować odpowiedzi: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--top', '-n', default=5, help='Number of passages to use per question')
def chat(top):
    """Start an interactive chat session with your book library."""
    try:
        from answerer import InteractiveChatSession

        session = InteractiveChatSession()

        click.echo("\n" + "=" * 70)
        click.echo("📚 Lokalny czat AI z książkami")
        click.echo("=" * 70)
        click.echo("Zapytaj mnie o cokolwiek z Twoich książek!")
        click.echo("\nKomendy:")
        click.echo("  /sources  - Pokaż wszystkie książki użyte w rozmowie")
        click.echo("  /clear    - Wyczyść historię rozmowy")
        click.echo("  exit      - Wyjdź z czatu")
        click.echo("=" * 70 + "\n")

        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                # Handle exit
                if user_input.lower() in ['exit', 'quit', 'q', 'wyjście', 'wyjdź']:
                    click.echo("\nDo zobaczenia! 👋")
                    break

                # Handle commands
                if user_input.startswith('/'):
                    if user_input == '/sources':
                        sources = session.get_all_sources()
                        if sources:
                            click.echo(f"\n📚 Książki użyte w tej rozmowie:")
                            for i, source in enumerate(sources, 1):
                                click.echo(f"  {i}. {source}")
                        else:
                            click.echo("\nŻadne książki nie zostały jeszcze użyte.")
                        click.echo()
                        continue

                    elif user_input == '/clear':
                        session.clear_history()
                        click.echo("\n✓ Historia rozmowy wyczyszczona.\n")
                        continue

                    else:
                        click.echo(f"\nNieznana komenda: {user_input}")
                        click.echo("Dostępne komendy: /sources, /clear, exit\n")
                        continue

                # Get AI response
                click.echo()
                response, sources = session.chat(user_input, n_results=top)

                click.echo(f"🤖 Asystent: {response}\n")

                # Show sources for this answer
                if sources:
                    click.echo(f"   📖 Źródła: ", nl=False)
                    source_list = [f"{s.book_title}" for s in sources[:3]]
                    click.echo(", ".join(source_list))
                    if len(sources) > 3:
                        click.echo(f"   ... i {len(sources) - 3} więcej")
                    click.echo()

            except KeyboardInterrupt:
                click.echo("\n\nPrzerwano. Wpisz 'exit' aby zakończyć lub kontynuuj rozmowę.")
                click.echo()
                continue

            except EOFError:
                click.echo("\n\nDo zobaczenia! 👋")
                break

    except Exception as e:
        click.echo(f"\n✗ Sesja czatu nie powiodła się: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()

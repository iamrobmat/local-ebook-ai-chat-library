# Changelog

All notable changes to the EPUB Books RAG System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2025-10-27] - Podstawowe moduły systemu RAG

#### Dodano
- **`.gitignore`** - konfiguracja Git (ignoruje ChromaDB, .env, pliki książek)
- **`rag-system/requirements.txt`** - zależności Python:
  - chromadb>=0.4.0 (embedded vector database)
  - ebooklib>=0.18 (parsowanie EPUB)
  - openai>=1.0.0 (API dla embeddingów)
  - beautifulsoup4, html2text (czyszczenie HTML)
  - click, tqdm, pydantic (CLI i utilities)
- **`rag-system/config.py`** - moduł konfiguracji systemu:
  - Pydantic models dla typowanej konfiguracji
  - Automatyczne ładowanie z .env (OPENAI_API_KEY)
  - Konfiguracja chunking strategy (rozdziały: 2000-5000 tokenów, paragrafy: 300-500)
  - Paths, OpenAI, ChromaDB settings
- **`rag-system/epub_parser.py`** - parser plików EPUB:
  - Klasa EPUBParser z ebooklib wrapper
  - Ekstrakcja metadanych (tytuł, autor, język, ISBN)
  - Ekstrakcja rozdziałów z konwersją HTML → plain text
  - BeautifulSoup do czyszczenia HTML
  - Split na paragrafy
  - CLI testing mode
- **`rag-system/docs/git-changelog-flow.md`** - dokumentacja procesu Git/CHANGELOG
- **`rag-system/data/`** - folder na dane (ChromaDB, index_status.json)

#### Uzasadnienie zmian
Pierwsza implementacja core components systemu RAG:
1. **config.py** - scentralizowana konfiguracja z walidacją typów (Pydantic)
2. **epub_parser.py** - fundament do ekstrakcji tekstu z 209 książek EPUB
3. **requirements.txt** - wszystkie zależności w jednym miejscu
4. **Struktura folderów** - separacja kodu i danych

#### Podsumowanie
Zaimplementowano podstawową infrastrukturę systemu RAG. Kolejne kroki: indexer.py (chunking + embeddings), searcher.py (semantic search), cli.py (user interface).

---

### Added
- Initial project setup
- Git repository initialization
- Project structure (rag-system folder)
- Documentation (claude.md, CHANGELOG.md)

## [0.1.0] - 2025-10-27

### Added
- Project inception
- Technical specification in claude.md
- RAG system architecture design:
  - ebooklib for EPUB parsing
  - OpenAI API for embeddings (text-embedding-3-small)
  - ChromaDB for vector storage
  - 2-level chunking strategy (chapters + paragraphs)

### Planned
- CLI implementation (cli.py)
- EPUB parser wrapper (epub_parser.py)
- Indexer with OpenAI integration (indexer.py)
- Semantic search functionality (searcher.py)
- Configuration management (config.py)
- Full library indexing (209 EPUB books)

[Unreleased]: https://github.com/yourusername/books-rag/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/books-rag/releases/tag/v0.1.0

# Changelog

All notable changes to the EPUB Books RAG System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2025-10-28] - Adaptive Chunking i finalizacja indeksowania

#### Zmieniono
- **`rag-system/indexer.py`** - implementacja adaptive chunking w `EmbeddingGenerator`:
  - **DODANO** `_estimate_tokens()` - estymacja tokenów (1 token ≈ 4 znaki)
  - **DODANO** `_split_into_token_limited_batches()` - dzielenie tekstów na batche z limitem tokenów
  - **DODANO** `_generate_embeddings_with_adaptive_batching()` - generowanie embeddingów z określonym limitem
  - **ZMIENIONO** `generate_embeddings()` - automatyczne próbowanie wielu limitów tokenów [5500, 4000, 3000, 2000, 1500]
  - Automatyczne obcinanie tekstów przekraczających limit
  - Lepsze zarządzanie błędami związanymi z limitami tokenów

#### Uzasadnienie zmian
Problem z limitami tokenów OpenAI API:
1. **Problem początkowy**: 101/209 książek failowało z błędem "maximum context length 8192 tokens exceeded" (8,000-14,000 tokenów)
2. **Pierwsza próba**: Obniżenie globalnego limitu do 5500 tokenów - wciąż 50+ książek failowało
3. **Rozwiązanie finalne**: Adaptive chunking - system automatycznie próbuje różne limity tokenów dla każdej książki
4. **Efekt**:
   - Zindeksowano **191/209 książek (91% sukcesu)**
   - **7,077 chunków** (1,331 rozdziałów + 5,676 paragrafów)
   - **828 MB baza ChromaDB**
   - Tylko 8 failów (wszystkie uszkodzone pliki EPUB)
5. **Zaleta**: Różne książki mogą mieć różne rozmiary chunków - optymalizacja per książka

#### Podsumowanie
System RAG w pełni funkcjonalny. Adaptive chunking rozwiązał problem limitów tokenów OpenAI API, umożliwiając indeksowanie 91% biblioteki (191/209 książek). Pozostałe 8 niepowodzeń to uszkodzone pliki EPUB wymagające ponownego pobrania.

---

## [2025-10-27] - Pełny system RAG (indexer, searcher, CLI)

#### Dodano
- **`rag-system/indexer.py`** - moduł indeksowania książek EPUB:
  - Klasa `BookIndexer` z pełną funkcjonalnością indeksowania
  - `Chunker` - dzieli tekst na chunki według strategii (rozdziały + paragrafy)
  - `EmbeddingGenerator` - generuje embeddingi przez OpenAI API z batch processing
  - `IndexStatus` - zarządza stanem indeksowania w JSON
  - File hashing do wykrywania zmian
  - Progress bars z tqdm
  - Metody: `index_book()`, `index_library()`, `update_index()`, `clear_index()`
  - Retry logic z exponential backoff
  - CLI testing mode
- **`rag-system/searcher.py`** - moduł wyszukiwania semantycznego:
  - Klasa `BookSearcher` z semantic search przez ChromaDB
  - Generowanie query embeddings przez OpenAI
  - Filtrowanie po: autor, tytuł, chunk_type
  - Cosine similarity ranking
  - `SearchResult` dataclass z formatowaniem
  - Collection statistics
  - Post-filtering dla partial text matches
  - CLI testing mode
- **`rag-system/cli.py`** - interfejs użytkownika (Click CLI):
  - `init` - inicjalizacja i weryfikacja systemu
  - `index --full/--force/--book` - indeksowanie książek
  - `update` - aktualizacja z nowymi książkami
  - `search <query>` - wyszukiwanie semantyczne
    - Opcje: `--top`, `--level`, `--author`, `--book`, `--full`
  - `status` - statystyki i stan indeksowania
  - `clear` - czyszczenie bazy (z potwierdzeniem)
  - `reindex <book_path>` - reindeksowanie pojedynczej książki
  - Error handling i user-friendly messages
  - Progress indicators
- **`rag-system/README.md`** - pełna dokumentacja użytkownika:
  - Instrukcje instalacji i konfiguracji
  - Przykłady użycia wszystkich komend
  - Architektura systemu
  - Opis modułów
  - Rozwiązywanie problemów
  - Koszty OpenAI API
- **`.env.example`** - szablon pliku .env z OPENAI_API_KEY

#### Uzasadnienie zmian
Ukończenie implementacji funkcjonalnego systemu RAG:
1. **indexer.py** - automatyczne przetwarzanie 200+ książek EPUB z chunking, embeddings, ChromaDB storage
2. **searcher.py** - semantic search z filtrowaniem i ranking
3. **cli.py** - user-friendly interface do wszystkich operacji
4. **README.md** - kompletna dokumentacja dla użytkownika końcowego
5. **Batch processing** - optymalizacja kosztów OpenAI (100 tekstów/request)
6. **Incremental updates** - indeksowanie tylko nowych książek
7. **File hashing** - wykrywanie zmian w istniejących plikach

#### Podsumowanie
System RAG jest w pełni funkcjonalny i gotowy do użycia. Można indeksować bibliotekę 200+ książek EPUB i wykonywać semantic search w języku polskim i angielskim. Szacowany czas pierwszego indeksowania: 1-1.5h. Koszt: ~$0.50-1.00.

---

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

[Unreleased]: https://github.com/iamrobmat/local-epub-ai-chat-library/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/iamrobmat/local-epub-ai-chat-library/releases/tag/v0.1.0

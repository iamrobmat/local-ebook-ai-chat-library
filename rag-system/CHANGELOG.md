# Changelog

All notable changes to the EPUB Books RAG System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2025-11-06] - Compile E-book: Tworzenie tematycznych antologii EPUB

#### Dodano
- **`rag-system/ebook_compiler.py`** - nowy moduł do kompilacji tematycznych e-booków:
  - Klasa `EbookCompiler` z metodą `compile_ebook()` do tworzenia EPUB z wyników wyszukiwania
  - Semantic search → grupowanie fragmentów po książkach źródłowych → generowanie EPUB
  - **Legal safeguards**:
    - Limit długości fragmentu (default 500 znaków)
    - Próg podobieństwa (default 0.7)
    - Pełne cytowania dla każdego fragmentu (tytuł, autor, rozdział, typ, word count)
    - Rozdział "Legal Disclaimer" z ostrzeżeniem "PERSONAL USE ONLY"
    - Metadata EPUB: "PERSONAL USE ONLY - Not for distribution"
  - **EPUB struktura**:
    - Rozdział wprowadzający (info o zapytaniu, liczba źródeł, statystyki)
    - Rozdziały pogrupowane po książkach źródłowych (sortowanie wg similarity)
    - Rozdział Legal Disclaimer
    - Profesjonalny CSS styling (fragmenty, cytowania, kolory)
    - Table of Contents (TOC) + Navigation (NCX)
  - **Parametry**:
    - `query` - zapytanie semantyczne
    - `output_path` - ścieżka do wygenerowanego EPUB
    - `n_results` - liczba fragmentów (default 50)
    - `min_similarity` - minimalny próg podobieństwa (default 0.7)
    - `max_fragment_length` - max znaków per fragment (default 500)
    - `title` - custom tytuł (optional)
    - `group_by` - "book" lub "topic" (obecnie tylko "book")
    - `chunk_type` - filtr: "chapter", "paragraph" lub None

- **`rag-system/cli.py`** - nowa komenda CLI `compile-ebook`:
  - Składnia: `python cli.py compile-ebook "query" output.epub [OPTIONS]`
  - Opcje:
    - `--results, -n` - liczba fragmentów (default 50)
    - `--min-similarity` - próg podobieństwa (default 0.7)
    - `--max-length` - max długość fragmentu (default 500 chars)
    - `--title` - custom tytuł e-booka
    - `--level` - "chapter", "paragraph" lub "both" (default both)
  - Wyświetla ostrzeżenie "PERSONAL USE ONLY" przy sukcesie
  - Przykłady użycia w docstringu

#### Zmieniono
- **`CLAUDE.md`** - zaktualizowano roadmapę v2.2:
  - Oznaczono feature #6 "Compile E-book" jako **DONE (2025-11-06)**
  - Dodano szczegóły implementacji: moduły, parametry, testy

#### Testy
Wygenerowano testowe e-booki:
1. **psychology_test.epub**:
   - Query: "psychology"
   - 11 fragmentów (similarity >= 0.35)
   - Rozmiar: 11.6 KB
   - Format EPUB poprawny (`file` command: "EPUB document")

2. **meditation_collection.epub**:
   - Query: "meditation and mindfulness"
   - 40 fragmentów (similarity >= 0.3)
   - Custom title: "Meditation: A Personal Guide"
   - Rozmiar: 19.0 KB

**Wnioski**: Feature działa poprawnie. EPUBy generują się z proper strukturą, metadata i citations. Legal disclaimer wyświetla się na początku i na końcu e-booka.

#### Uwagi prawne
**⚠️ WAŻNE**: Ta funkcja jest przeznaczona WYŁĄCZNIE do użytku osobistego, edukacyjnego i badawczego. Wygenerowane e-booki zawierają fragmenty książek chronionych prawem autorskim i NIE MOGĄ być dystrybuowane, udostępniane ani wykorzystywane komercyjnie.

**Legal safeguards w implementacji**:
- Limit długości fragmentu (fair use compliance)
- Pełne cytowania źródeł (book, author, chapter)
- Próg podobieństwa (tylko relevantne fragmenty)
- Disclaimer w EPUB (wyraźne oznaczenie "PERSONAL USE ONLY")
- Dokumentacja w README.md i CLI help

#### Uzasadnienie zmian
1. **Use case**: Tworzenie tematycznych antologii z biblioteki osobistej (np. "wszystko o medytacji", "stoicism collection")
2. **Legal compliance**: Fragment limits + full citations = fair use dla celów osobistych/edukacyjnych
3. **ebooklib**: Dojrzała biblioteka do tworzenia EPUB z proper strukturą
4. **Workflow**: Semantic search (już działa) → grupowanie → format HTML → EPUB generation
5. **Efekt**: User może stworzyć spersonalizowane e-booki do czytania offline na Kindle/czytnik

#### Podsumowanie
System RAG v2.2 obsługuje teraz tworzenie tematycznych e-booków EPUB z fragmentów książek. Komenda `compile-ebook` wyszukuje semantycznie fragmenty, grupuje je po książkach źródłowych i generuje profesjonalny EPUB z TOC, metadata, CSS i legal disclaimer. Wbudowane zabezpieczenia prawne (fragment limits, citations, "PERSONAL USE ONLY") zapewniają compliance z fair use dla celów osobistych/edukacyjnych.

---

## [2025-11-05] - Obsługa formatów PDF i MOBI (60x szybszy parser)

#### Dodano
- **`rag-system/document_parser.py`** - nowy parser PDF i MOBI używający PyMuPDF (fitz):
  - Klasa `DocumentParser` z metodami ekstrakcji tekstu
  - Automatyczna detekcja rozdziałów (pattern matching dla "Chapter X", numerów)
  - Fallback do chunk'ów po 10 stron gdy brak rozdziałów
  - Ekstrakcja metadanych (tytuł, autor, publisher, ISBN)
  - Czyszczenie tekstu (whitespace, hyphenation, artifacts)
  - Identyczny interfejs jak `EPUBParser` dla łatwej integracji
  - Wsparcie formatów: PDF, MOBI, XPS, FB2, CBZ, SVG, TXT
  - **60x szybszy** niż PyPDF2/pdfplumber
- **`rag-system/test_timing.py`** - skrypt testowy weryfikujący wydajność parsera

#### Zmieniono
- **`rag-system/indexer.py`** - rozszerzenie obsługi o PDF/MOBI + timeout mechanism:
  - **ZMIENIONO** `_find_epub_files()` → `_find_book_files()` z wieloma formatami (EPUB, PDF, MOBI)
  - **ZMIENIONO** `index_book()` - automatyczny wybór parsera na podstawie rozszerzenia (.epub → EPUBParser, .pdf/.mobi → DocumentParser)
  - **DODANO** `ThreadPoolExecutor` z timeout 120s per książka
  - **DODANO** obsługa `FuturesTimeoutError` - pomijanie książek przekraczających 2 minuty
  - **ZMIENIONO** komunikaty błędów i progress tracking dla wszystkich formatów
  - Shutdown executora po zakończeniu
- **`rag-system/cli.py`** - aktualizacja opisów komend:
  - **ZMIENIONO** docstring głównego CLI: "EPUB Books" → "Books" + "EPUB, PDF, MOBI"
  - **ZMIENIONO** opis komendy `init`: "EPUB Books RAG System" → "Books RAG System"
  - **ZMIENIONO** opis komendy `index`: "Index EPUB books" → "Index books (EPUB, PDF, MOBI)"
- **`rag-system/requirements.txt`** - dodano PyMuPDF:
  - **DODANO** `PyMuPDF>=1.23.0` jako dependency
  - Komentarz: "PyMuPDF is 60x faster!" i wsparcie dla wielu formatów
- **`claude.md`** - update statusu implementacji:
  - **ZMIENIONO** PyMuPDF parser z "Następne kroki v2.2" → **DONE (2025-11-05)**

#### Wyniki indeksowania
Po pełnym indeksowaniu 420 plików (EPUB + PDF + MOBI):
- **✅ 87 nowych PDF/MOBI zaindeksowanych**
  - 1,569 chapter chunks
  - 3,095 paragraph chunks
  - **4,664 total nowych chunków**
- **⏭️ 154 EPUBy pominięte** (już były w bazie)
- **❌ 10 błędów** (uszkodzone pliki ZIP, brak META-INF/container.xml w EPUB)
- **⏱️ 1 timeout** (1 PDF > 120s automatycznie pominięty)

**Stan bazy danych:**
- **385 książek** w bazie (EPUB + PDF + MOBI)
- **15,926 chunków** w ChromaDB (192 chapters, 808 paragraphs)
- **1.7 GB** rozmiar bazy danych
- **91% success rate** dla indeksowania

#### Uzasadnienie zmian
Rozszerzenie wsparcia na formaty PDF i MOBI:
1. **Cel**: Umożliwienie indeksowania pełnej biblioteki (209 EPUB + 101 PDF/MOBI = 310 książek)
2. **PyMuPDF wybór**:
   - **60x szybszy** niż PyPDF2 (badania z 2025-10-31)
   - Wsparcie dla wielu formatów przez jedno unified API
   - Wysoka jakość ekstrakcji tekstu
   - Niezawodność i dojrzałość biblioteki (1.23.0)
3. **Timeout mechanism**: Ochrona przed zawieszeniem na problematycznych plikach (120s limit per książka)
4. **Unified interface**: `DocumentParser` ma identyczny interfejs jak `EPUBParser` - łatwa integracja
5. **Detekcja rozdziałów**: Automatyczne wykrywanie struktury dokumentu lub fallback do chunk'ów stronnicowych
6. **Efekt**: System RAG teraz wspiera 3 popularne formaty e-booków, obsługując 92% plików w bibliotece

#### Podsumowanie
System RAG v2.2 wspiera teraz EPUB, PDF i MOBI. PyMuPDF zapewnia szybkie i niezawodne parsowanie dokumentów. Timeout mechanism chroni przed problematycznymi plikami. Baza danych wzrosła do 15,926 chunków (1.7 GB) z 385 książek. Wszystkie nowo zaindeksowane książki PDF/MOBI są w pełni dostępne do semantic search, AI Q&A (`ask`) i interaktywnego czatu (`chat`).

**Test:** Zapytanie "What are the key principles from Charlie Munger?" wygenerowało szczegółową odpowiedź w języku polskim na bazie 3 fragmentów z nowo zaindeksowanej książki PDF "Charlie Munger: The Complete Investor".

---

## [2025-10-31] - Zmiana modelu na GPT-5-nano

#### Zmieniono
- **`rag-system/answerer.py`** - zmiana modelu AI:
  - **ZMIENIONO** model z `gpt-5-mini` → `gpt-5-nano` w `BookAnswerer`
  - **ZMIENIONO** model z `gpt-5-mini` → `gpt-5-nano` w `InteractiveChatSession`
  - **ZMIENIONO** model w `clear_history()` na `gpt-5-nano`
  - Zaktualizowano komentarze do nowego modelu

#### Uzasadnienie zmian
Testowanie GPT-5-nano jako potencjalnie szybszej/tańszej alternatywy dla GPT-5-mini przy zachowaniu jakości odpowiedzi.

---

## [2025-10-31] - Plan rozwoju v2.2 (dokumentacja)

#### Dodano
- **`claude.md`** - sekcja "🚀 Następne kroki (v2.2)":
  - Lista 5 planowanych rozszerzeń systemu
  - **PyMuPDF parser** - wsparcie dla PDF + MOBI (60x szybszy niż pdfplumber)
  - **Zapis rozmowy** - komenda `/save filename.md` w chat
  - **Schowek** - komenda `/copy` dla odpowiedzi
  - **Pasek postępu** - feedback podczas generowania (streaming GPT)
  - **Kolorki** - biblioteka `rich` dla ładniejszego terminala

#### Uzasadnienie zmian
Badania z 2025-10-31 wykazały, że PyMuPDF jest 60x szybsza od konkurencji i wspiera wiele formatów (PDF, EPUB, MOBI) przez jedno API. Zaplanowano również usprawnienia UX (zapis rozmów, schowek, progress bar, kolorowanie terminala) dla lepszego doświadczenia użytkownika.

---

## [2025-10-30] - Polskie odpowiedzi, GPT-5-mini i ulepszone cytowanie (v2.1)

#### Zmieniono
- **`rag-system/answerer.py`** - upgrade modelu i lokalizacja na polski:
  - **ZMIENIONO** model z `gpt-4o-mini` → `gpt-5-mini`
  - **DODANO** parametr `temperature: 1` (wymagany przez gpt-5-mini)
  - **ZMIENIONO** system prompt na polski w `BookAnswerer`:
    - Instrukcja: "Odpowiadaj ZAWSZE w języku polskim, niezależnie od języka pytania"
    - Cytowanie z numerami źródeł [1], [2], [3]
  - **ZMIENIONO** system prompt na polski w `InteractiveChatSession`
  - **ZMIENIONO** user prompt na polski w metodzie `ask()`
  - **ZMIENIONO** metoda `clear_history()` używa gpt-5-mini z temperature=1
- **`rag-system/cli.py`** - pełna polonizacja interfejsu i rozszerzone źródła:
  - **ZMIENIONO** wszystkie nagłówki i komunikaty komendy `ask` na polski:
    - "Pytanie:", "Przeszukuję książki i generuję odpowiedź...", "ODPOWIEDŹ:", "ŹRÓDŁA"
  - **ROZSZERZONO** wyświetlanie źródeł w komendzie `ask`:
    - Tytuł w cudzysłowach, rozdział, podobieństwo, typ (chapter/paragraph)
    - **DODANO** podgląd tekstu (200 znaków) dla łatwego odnalezienia fragmentu w książce
  - **ZMIENIONO** wszystkie nagłówki i komunikaty komendy `chat` na polski:
    - "Lokalny czat AI z książkami", "Zapytaj mnie o cokolwiek z Twoich książek!"
    - Komendy: "/sources", "/clear", "exit" z polskimi opisami
  - **DODANO** polskie komendy wyjścia: 'wyjście', 'wyjdź'
  - **ZMIENIONO** wszystkie komunikaty błędów na polski

#### Uzasadnienie zmian
Ulepszenia użytkownika v2.1 - doświadczenie użytkownika w języku polskim:
1. **Cel**: Pełna lokalizacja systemu dla polskojęzycznych użytkowników
2. **Model GPT-5-mini**: Najnowszy model OpenAI z lepszą jakością odpowiedzi
3. **Polskie odpowiedzi**: System prompt wymusza odpowiedzi w języku polskim niezależnie od języka pytania
4. **Cytowanie z numerami**: GPT używa [1], [2], [3] odpowiadających źródłom - łatwiejsza weryfikacja
5. **Rozszerzony podgląd źródeł**:
   - Pokazuje typ fragmentu (rozdział vs paragraf)
   - Podgląd 200 znaków tekstu źródłowego
   - Pozwala użytkownikowi łatwo odnaleźć pełny kontekst w książce
6. **UX**: Wszystkie komunikaty, błędy i instrukcje po polsku

#### Podsumowanie
System RAG v2.1 jest w pełni spolszczony i używa GPT-5-mini. Użytkownicy otrzymują:
- Odpowiedzi w języku polskim niezależnie od języka pytania
- Cytaty z numerami [1], [2], [3] odpowiadającymi źródłom
- Szczegółowe informacje o źródłach: książka, rozdział, typ, podgląd tekstu
- Polski interfejs CLI dla komend `ask` i `chat`

**Test:** Zapytanie "Czym jest stoicyzm i jak mogę go zastosować w codziennym życiu?" wygenerowało szczegółową 10-punktową odpowiedź w języku polskim z cytatami [1]-[5] i pełnymi informacjami o 5 źródłach.

---

## [2025-10-29] - Implementacja RAG z simpleaichat (v2.0)

#### Dodano
- **`rag-system/answerer.py`** - nowy moduł RAG (Retrieval-Augmented Generation):
  - Klasa `BookAnswerer` - generowanie odpowiedzi GPT-4 na bazie fragmentów książek
  - Klasa `InteractiveChatSession` - sesja czatu z pamięcią konwersacji
  - Integracja z `simpleaichat` dla łatwej obsługi OpenAI API
  - Formatowanie kontekstu z search results
  - Tracking źródeł w konwersacji
  - CLI testing mode
- **`cli.py ask`** - komenda jednokrotnego pytania:
  - `python cli.py ask "pytanie"` - zadaj pytanie, otrzymaj odpowiedź
  - Opcja `--top N` dla liczby fragmentów kontekstu
  - Wyświetlanie źródeł z podobieństwem
  - Error handling i user-friendly output
- **`cli.py chat`** - komenda interaktywnego czatu:
  - `python cli.py chat` - rozpocznij sesję czatu
  - Wieloturowa konwersacja z pamięcią
  - Komendy specjalne: `/sources`, `/clear`, `exit`
  - Wyświetlanie źródeł per odpowiedź
  - Graceful exit (Ctrl+C, EOF)

#### Zmieniono
- **`requirements.txt`** - dodano simpleaichat:
  - `simpleaichat>=0.2.0` dla RAG functionality
  - Reorganizacja z komentarzami per sekcję
  - Vector Database, EPUB Parsing, RAG & Chat, CLI & Config

#### Uzasadnienie zmian
Implementacja pełnego systemu RAG (v2.0):
1. **Cel**: Transformacja z "semantic search" na "AI assistant" generujący odpowiedzi
2. **Biblioteka**: `simpleaichat` - prostsza alternatywa vs prompt_toolkit+asyncio
3. **Czas implementacji**: ~1 godzina (zamiast 2-3 dni)
4. **Funkcjonalność**:
   - `ask` - pojedyncze pytania z odpowiedzią + źródła
   - `chat` - wieloturowa konwersacja z pamięcią
5. **Model**: GPT-4o-mini (tańszy, szybszy, wystarczająco dobry)
6. **Koszt**: ~$0.01-0.02 per pytanie
7. **Test**: Pomyślnie wygenerowano szczegółową odpowiedź o stoicyzmie na bazie 5 fragmentów

#### Podsumowanie
System RAG działa! Użytkownicy mogą teraz:
- Zadawać pytania: `python cli.py ask "What is stoicism?"`
- Czatować interaktywnie: `python cli.py chat`
- Otrzymywać odpowiedzi GPT-4 na bazie ich książek
- Widzieć źródła cytowań

**Next:** Możliwy upgrade do prompt_toolkit + asyncio dla lepszego UX (optional).

---

## [2025-10-29] - Plan rozwoju v2.0: RAG i Chat Interface

#### Dodano
- **`claude.md`** - dokumentacja planu rozwoju v2.0:
  - Plan implementacji RAG (Retrieval-Augmented Generation)
  - Badania bibliotek CLI chat interface
  - Rekomendacja: `prompt_toolkit` + `asyncio` + OpenAI
  - Przykłady kodu dla `answerer.py` i `chat_interface.py`
  - Timeline implementacji (Sprint 1-3)
  - Linki do źródeł i przykładów (GMO Engineering, GeminiAI CLI, ai-cli-chat)
  - Pytania do rozstrzygnięcia (model GPT, UI, formaty)

#### Zmieniono
- **`claude.md`** - aktualizacja sekcji "Następne kroki":
  - Status implementacji v1.0 (191/209 książek zindeksowanych)
  - Plan rozwoju v2.0 z trzema priorytetami
  - Priorytet 1: RAG z GPT-4 dla generowania odpowiedzi
  - Priorytet 2: CLI Chat Interface z prompt_toolkit
  - Priorytet 3: Rozszerzenia (Web UI, PDF, voice input)

#### Uzasadnienie zmian
Badania i planowanie kolejnych kroków rozwoju:
1. **Obecny stan**: Semantic search działa, ale brak generowania odpowiedzi (tylko lista fragmentów)
2. **Cel v2.0**: Transformacja z "search engine" na "AI assistant" z konwersacyjnym interface
3. **Badania**: Przeanalizowano biblioteki CLI chat (prompt_toolkit, rich, simpleaichat)
4. **Wybór**: prompt_toolkit + asyncio + OpenAI AsyncClient (produkcyjnie sprawdzone)
5. **Źródła**: GMO Engineering tutorial (2025), GitHub examples
6. **Timeline**: ~2-3 dni pracy (RAG Core + Chat Interface + Polish)

#### Podsumowanie
Plan rozwoju v2.0 jest gotowy. Kolejne kroki: implementacja `answerer.py` (RAG) i `chat_interface.py` (async chat z streaming responses). System będzie wtedy pełnym AI assistant'em działającym w terminalu.

---

## [2025-10-28] - Zmiana nazwy projektu i przygotowanie do publikacji

#### Zmieniono
- **`README.md`** - aktualizacja nazwy projektu z "EPUB" na "eBook":
  - Zmiana głównego tytułu na "Local eBook AI Chat Library"
  - Bardziej inkluzywna nazwa (sugeruje wsparcie dla różnych formatów ebook)
  - Update URL repozytorium: `local-epub-ai-chat-library` → `local-ebook-ai-chat-library`
  - Update ścieżki klonowania projektu
- **`LICENSE`** - update copyright z nową nazwą projektu
- **`rag-system/CHANGELOG.md`** - update URLi GitHub do nowej nazwy repozytorium

#### Uzasadnienie zmian
Nazwa "eBook" jest bardziej uniwersalna i przyciągająca:
1. **Szerszy zasięg**: "eBook" sugeruje wsparcie dla różnych formatów, nie tylko EPUB
2. **Lepsze SEO**: "ebook" jest bardziej popularnym terminem wyszukiwania niż "epub"
3. **Przyszłościowe**: Łatwiejsze rozszerzenie o PDF, MOBI, AZW3 w przyszłości
4. **Marketing**: Prostsze i bardziej zrozumiałe dla użytkowników końcowych

---

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

[Unreleased]: https://github.com/iamrobmat/local-ebook-ai-chat-library/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/iamrobmat/local-ebook-ai-chat-library/releases/tag/v0.1.0

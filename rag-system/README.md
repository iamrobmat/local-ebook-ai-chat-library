# EPUB Books RAG System

Lokalna baza do semantycznego przeszukiwania książek EPUB z biblioteki Calibre. System wykorzystuje embeddingi OpenAI i ChromaDB do wyszukiwania kontekstowego.

## Funkcjonalności

- 📚 Automatyczne indeksowanie książek EPUB
- 🔍 Semantyczne wyszukiwanie (nie tylko słowa kluczowe!)
- 🇵🇱 🇬🇧 Wsparcie polskiego i angielskiego
- 📊 2-poziomowe chunki: rozdziały + paragrafy
- 💾 Embedded ChromaDB (bez serwerów)
- ⚡ Szybkie wyszukiwanie (milisekundy)
- 🔄 Inkrementalne aktualizacje (tylko nowe książki)

## Wymagania

- Python 3.8+
- OpenAI API key
- Biblioteka książek EPUB (np. z Calibre)

## Instalacja

### 1. Instalacja zależności

```bash
cd rag-system
pip install -r requirements.txt
```

### 2. Konfiguracja OpenAI API

Utwórz plik `.env` w folderze głównym (`/Users/robert/Books/books/.env`):

```bash
OPENAI_API_KEY=sk-your-api-key-here
```

Lub ustaw zmienną środowiskową:

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### 3. Inicjalizacja systemu

```bash
python cli.py init
```

To sprawdzi konfigurację i utworzy niezbędne foldery.

## Użycie

### Indeksowanie książek

#### Pierwsze indeksowanie (wszystkie książki)

```bash
python cli.py index --full
```

To zindeksuje wszystkie znalezione pliki EPUB. Dla ~200 książek zajmie **1-1.5 godziny**.

#### Aktualizacja (tylko nowe książki)

```bash
python cli.py update
```

Automatycznie wykrywa i indeksuje tylko nowe lub zmienione książki.

#### Indeksowanie pojedynczej książki

```bash
python cli.py index --book "/path/to/book.epub"
```

### Wyszukiwanie

#### Podstawowe wyszukiwanie

```bash
python cli.py search "stoicism and meditation"
```

#### Wyszukiwanie z filtrem autora

```bash
python cli.py search "economics" --author "Smith"
```

#### Wyszukiwanie tylko w rozdziałach

```bash
python cli.py search "philosophy" --level chapter
```

#### Wyszukiwanie tylko w paragrafach

```bash
python cli.py search "specific quote" --level paragraph
```

#### Więcej wyników

```bash
python cli.py search "history" --top 20
```

#### Pełny tekst (bez skrótów)

```bash
python cli.py search "psychology" --full
```

#### Kombinowane filtry

```bash
python cli.py search "meditation techniques" \
  --author "Marcus" \
  --level paragraph \
  --top 15
```

### Status i statystyki

```bash
python cli.py status
```

Pokazuje:
- Liczbę zindeksowanych książek
- Liczbę chunków (rozdziały + paragrafy)
- Rozmiar bazy danych
- Datę ostatniej aktualizacji

### Czyszczenie bazy

```bash
python cli.py clear
```

⚠️ **Uwaga**: Usuwa wszystkie dane! Będzie wymagane potwierdzenie.

### Reindeksowanie książki

```bash
python cli.py reindex "/path/to/book.epub"
```

## Przykłady użycia

### Przykład 1: Znajdź książki o stoicyzmie

```bash
$ python cli.py search "stoicism and daily practice"

Found 8 results:

1. Meditations - Marcus Aurelius
   Chapter: Book 2 (Ch. 2)
   Type: Chapter
   Similarity: 0.892
   Preview: When you wake up in the morning, tell yourself: the people I deal with today will be meddling, ungrateful, arrogant...

2. The Daily Stoic - Ryan Holiday
   Chapter: January (Ch. 1)
   Type: Paragraph
   Similarity: 0.856
   Preview: The essence of Stoic philosophy is about controlling what you can...
```

### Przykład 2: Znajdź konkretny cytat u Markusa Aureliusza

```bash
$ python cli.py search "waste of remaining time" --author "Marcus" --level paragraph

Found 3 results:

1. Meditations - Marcus Aurelius
   Chapter: Book 3 (Ch. 3)
   Type: Paragraph
   Similarity: 0.912
   Preview: Don't waste the rest of your time here worrying about other people...
```

### Przykład 3: Eksploruj tematy ekonomiczne

```bash
$ python cli.py search "invisible hand and market forces" --level chapter --top 5

Found 5 results:

1. The Wealth of Nations - Adam Smith
   Chapter: Book IV, Chapter 2 (Ch. 27)
   Type: Chapter
   Similarity: 0.884
   Preview: By preferring the support of domestic to that of foreign industry...
```

## Architektura

```
┌─────────────────────────────────────────┐
│  CLI (cli.py)                           │
│  Komendy: search, index, update, status │
└────────────────┬────────────────────────┘
                 ↓
    ┌────────────┴────────────┐
    ↓                         ↓
┌──────────┐           ┌─────────────┐
│ indexer  │           │  searcher   │
│  .py     │           │  .py        │
└────┬─────┘           └──────┬──────┘
     ↓                        ↓
┌─────────────────────────────────┐
│  ChromaDB + OpenAI Embeddings   │
│  - text-embedding-3-small       │
│  - Cosine similarity search     │
└─────────────────────────────────┘
```

## Moduły

- **cli.py** - Interfejs użytkownika (Click CLI)
- **config.py** - Konfiguracja systemu (Pydantic)
- **epub_parser.py** - Parser plików EPUB (ebooklib)
- **indexer.py** - Indeksowanie i chunking
- **searcher.py** - Wyszukiwanie semantyczne
- **requirements.txt** - Zależności Python

## Konfiguracja

System używa modelu Pydantic do konfiguracji. Domyślne ustawienia:

### Chunking Strategy

- **Rozdziały**: 2000-5000 tokenów
- **Paragrafy**: 300-500 tokenów
- **Overlap**: 50 tokenów

### OpenAI

- Model: `text-embedding-3-small`
- Wymiary: 1536
- Batch size: 100

### Wyszukiwanie

- Domyślnie: 10 wyników
- Maksymalnie: 50 wyników

Konfigurację można dostosować w `config.py`.

## Struktura plików

```
books/                                   # Root biblioteki Calibre
├── .env                                # OpenAI API key
├── .gitignore
├── claude.md                           # Specyfikacja techniczna
└── rag-system/
    ├── cli.py                         # CLI interface
    ├── config.py                      # Konfiguracja
    ├── epub_parser.py                 # Parser EPUB
    ├── indexer.py                     # Indeksowanie
    ├── searcher.py                    # Wyszukiwanie
    ├── requirements.txt               # Zależności
    ├── README.md                      # Ta dokumentacja
    ├── CHANGELOG.md                   # Historia zmian
    ├── docs/
    │   └── git-changelog-flow.md     # Proces Git/CHANGELOG
    └── data/
        ├── chromadb/                  # Baza wektorowa (gitignored)
        └── index_status.json          # Status indeksowania (gitignored)
```

## Koszty OpenAI API

### text-embedding-3-small

- **Cena**: $0.02 za 1M tokenów
- **Pierwsze indeksowanie** (~200 książek): **$0.50-1.00** jednorazowo
- **Aktualizacje** (nowe książki): kilka centów per książka
- **Wyszukiwanie**: ~$0.00002 per query (praktycznie darmowe)

## Rozwiązywanie problemów

### "OPENAI_API_KEY not found"

Upewnij się, że masz plik `.env` w głównym folderze lub zmienną środowiskową:

```bash
export OPENAI_API_KEY="sk-..."
```

### "Collection not found"

Uruchom indeksowanie:

```bash
python cli.py index --full
```

### Książka nie jest znaleziona

Sprawdź, czy:
1. Plik ma rozszerzenie `.epub`
2. Plik nie jest w folderze `rag-system`
3. Uruchomiłeś `python cli.py update`

### Powolne indeksowanie

To normalne - ~15-25 sekund per książka. Dla 200 książek: 1-1.5h.

Możesz przyspieszyć przez zwiększenie `batch_size` w `config.py`.

## Rozwój

### Testowanie parsera

```bash
python epub_parser.py "/path/to/book.epub"
```

### Testowanie indexera

```bash
python indexer.py "/path/to/book.epub"
```

### Testowanie searchera

```bash
python searcher.py "your query" --author "Author Name"
```

## Licencja

Do użytku prywatnego.

## Autor

System stworzony dla lokalnego użytku z biblioteką Calibre.

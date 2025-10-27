# Baza embedowanych książek EPUB - Semantic Search

## Opis systemu
Lokalna baza do semantycznego przeszukiwania 209 książek EPUB z biblioteki Calibre. Działa bezpośrednio w Claude Code przez Python CLI.

## Lokalizacja
- **Folder książek**: `/Users/robert/Books/books/`
- **Liczba książek**: 209 plików EPUB
- **Struktura**: Katalog Calibre (Autor/Tytuł/plik.epub)

## Architektura

```
┌─────────────────────────────────────────┐
│  Claude Code (Terminal)                 │
│  Komendy: search, index, update, status │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  Python CLI (cli.py)                    │
│  - search_books("stoicyzm")             │
│  - index_library()                      │
│  - update_new_books()                   │
│  - check_status()                       │
└────────────┬────────────────────────────┘
             ↓
    ┌────────┴────────┐
    ↓                 ↓
┌─────────┐    ┌──────────────┐
│ebooklib │    │ OpenAI API   │
│(czyta   │    │(embeddings:  │
│ EPUB)   │    │text-embed-3) │
└────┬────┘    └──────┬───────┘
     ↓                ↓
┌─────────────────────────────┐
│  ChromaDB (embedded)        │
│  ./rag-system/data/chromadb │
│  - Embeddingi tekstów       │
│  - Metadata (autor, tytuł)  │
│  - Status indeksowania      │
└─────────────────────────────┘
```

## Technologie

### Core components:
- **ebooklib** - bezpośrednie czytanie EPUB (bez MCP servera)
- **OpenAI API** - `text-embedding-3-small` dla generowania embeddingów
  - Multilingual (Polski + Angielski)
  - Szybkie (~2-3 sek/książka)
  - Koszt: ~$0.50-1.00 jednorazowo dla 209 książek
- **ChromaDB** - embedded vector database (jak SQLite, bez servera)
- **Python CLI** - prosty interface w terminalu

### Chunking strategy (2-poziomowa):

**Poziom 1: Rozdziały**
- Cały tekst rozdziału (2000-5000 tokenów)
- Metadata: `chunk_type: "chapter"`
- Use case: "Znajdź rozdział o X"

**Poziom 2: Paragrafy**
- Fragmenty ~300-500 tokenów
- Metadata: `chunk_type: "paragraph"`
- Use case: "Znajdź konkretny cytat/fragment o X"

Przy wyszukiwaniu można wybrać poziom lub oba jednocześnie.

## Struktura projektu

```
books/
├── claude.md                    # Ten dokument
├── .env                        # OPENAI_API_KEY=sk-...
├── rag-system/                  # System RAG
│   ├── cli.py                  # Main CLI interface
│   ├── indexer.py              # Skanuje EPUB → chunki → embeddingi
│   ├── searcher.py             # Semantic search
│   ├── epub_parser.py          # ebooklib wrapper
│   ├── config.py               # Konfiguracja
│   ├── requirements.txt
│   └── data/
│       ├── chromadb/           # Embedded vector database
│       └── index_status.json   # Stan indeksowania
└── [Calibre folders...]        # Istniejące książki EPUB
```

## Użytkowanie

### Setup (jednorazowo):
```bash
cd /Users/robert/Books/books/rag-system
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."  # Lub w pliku .env
python cli.py init
```

### Indeksowanie (pierwsza konfiguracja):
```bash
python cli.py index --full
# Skanuje wszystkie 209 książek EPUB
# Ekstraktuje rozdziały + paragrafy
# Generuje embeddingi przez OpenAI API
# Zapisuje w ChromaDB
# Czas: ~15-30 minut
```

### Wyszukiwanie:
```bash
# Szukaj w całej bibliotece
python cli.py search "książki o stoicyzmie i medytacji"

# Szukaj tylko w rozdziałach
python cli.py search "stoicism" --level chapter

# Szukaj tylko w paragrafach
python cli.py search "stoicism" --level paragraph

# Filtruj po autorze
python cli.py search "meditation" --author "Marcus Aurelius"

# Więcej wyników
python cli.py search "economics" --top 20
```

Przykładowy output:
```
📖 Found 8 results:

1. Meditations - Marcus Aurelius (Chapter 2)
   "When you wake up in the morning, tell yourself:
   the people I deal with today will be meddling..."
   Similarity: 0.89

2. The Power of Now - Eckhart Tolle (Chapter 5)
   "The essence of meditation is to be fully present..."
   Similarity: 0.84

3. ...
```

### Aktualizacja (dodanie nowych książek):
```bash
python cli.py update
# Automatycznie znajduje nowe EPUB
# Indeksuje tylko nowe książki
# Aktualizuje index_status.json
```

### Status:
```bash
python cli.py status

# Output:
# ✅ 209/209 books indexed
# 📊 2,456 chapters, 18,942 paragraphs
# 💾 Database size: 145MB
# 🕐 Last update: 2 hours ago
```

### Auto-check przy starcie:
System automatycznie sprawdza nowe książki przy każdym uruchomieniu i informuje:
```bash
python cli.py search "..."
# 📚 Found 3 new books. Run 'python cli.py update' to index them.
#
# 📖 Searching...
```

## Plik index_status.json

Przechowuje informacje o zindeksowanych książkach:
```json
{
  "indexed_books": {
    "Marcus Aurelius/Meditations": {
      "indexed_at": "2025-10-27T10:30:00",
      "chapters": 12,
      "paragraphs": 156,
      "file_hash": "abc123...",
      "file_path": "./Marcus Aurelius/Meditations/..."
    }
  },
  "total_indexed": 209,
  "last_update": "2025-10-27T10:30:00"
}
```

## ChromaDB - embedded database

ChromaDB działa jak SQLite - żadnych serwerów:
- Automatyczne tworzenie przy pierwszym użyciu
- Lokalne przechowywanie w `./data/chromadb/`
- Szybkie wyszukiwanie (milisekundy dla 209 książek)
- Persistence automatyczny

```python
# Tak to działa pod spodem:
import chromadb
client = chromadb.PersistentClient(path="./data/chromadb")
collection = client.get_or_create_collection("books")
```

## Aktualizacja bazy

Kiedy dodajesz nowe książki do katalogu Calibre:
```bash
# System automatycznie wykryje nowe pliki
python cli.py update

# Lub pełne ponowne indeksowanie
python cli.py index --full --force
```

## Koszty OpenAI API

**text-embedding-3-small**:
- Cena: $0.02 za 1M tokenów
- Szacunek dla 209 książek: ~$0.50-1.00 jednorazowo
- Aktualizacje (nowe książki): kilka centów per książka

## Dependencies (requirements.txt)

```
chromadb>=0.4.0
ebooklib>=0.18
beautifulsoup4>=4.12.0
html2text>=2020.1.16
openai>=1.0.0
python-dotenv>=1.0.0
click>=8.1.0
tqdm>=4.66.0
pydantic>=2.0.0
```

## Wsparcie językowe

System obsługuje:
- 🇵🇱 Polski
- 🇬🇧 Angielski
- Multilingual queries (można mieszać języki w zapytaniu)

OpenAI embeddings są multilingual out-of-the-box.

## Komendy CLI - podsumowanie

```bash
python cli.py init              # Setup początkowy
python cli.py index --full      # Indeksuj wszystkie książki
python cli.py search "query"    # Wyszukiwanie semantyczne
python cli.py update            # Dodaj nowe książki
python cli.py status            # Sprawdź status bazy
python cli.py reindex "book"    # Reindeksuj konkretną książkę
python cli.py clear             # Wyczyść całą bazę (ostrożnie!)
```

## Jak to działa pod spodem

1. **Indexing**:
   - ebooklib czyta EPUB → ekstraktuje HTML
   - BeautifulSoup parsuje strukturę (rozdziały)
   - Tekst dzielony na chunks (rozdziały + paragrafy)
   - OpenAI API generuje embeddingi (1536-dimensional vectors)
   - ChromaDB zapisuje: embedding + metadata + text

2. **Searching**:
   - Query → OpenAI embedding
   - ChromaDB: cosine similarity search
   - Top-k najbardziej podobnych chunks
   - Return z metadatami (książka, autor, rozdział)

3. **Update**:
   - Scan Calibre folder
   - Porównaj z index_status.json
   - Indeksuj tylko nowe/zmienione pliki

## Następne kroki implementacji

1. Setup struktury projektu
2. Implementacja `epub_parser.py` (ebooklib wrapper)
3. Implementacja `indexer.py` (chunking + OpenAI API)
4. Implementacja `searcher.py` (ChromaDB queries)
5. Implementacja `cli.py` (user interface)
6. Testing na przykładowych książkach
7. Full indexing wszystkich 209 książek

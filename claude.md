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

## Status implementacji (2025-10-28)

### ✅ Zrealizowane (v1.0)
1. ✅ Setup struktury projektu
2. ✅ Implementacja `epub_parser.py` (ebooklib wrapper)
3. ✅ Implementacja `indexer.py` (chunking + OpenAI API + adaptive chunking)
4. ✅ Implementacja `searcher.py` (ChromaDB queries)
5. ✅ Implementacja `cli.py` (user interface)
6. ✅ Testing i optymalizacja
7. ✅ Full indexing - 191/209 książek (91% sukcesu)
8. ✅ Publikacja na GitHub: https://github.com/iamrobmat/local-ebook-ai-chat-library

**Obecna funkcjonalność: Semantic Search**
- User Query → Vector Search → Lista relevantnych fragmentów z książek
- CLI: `python cli.py search "pytanie"`

---

## 🚀 Następne kroki rozwoju (v2.0)

### Priorytet 1: RAG - Generowanie odpowiedzi (GPT-4)

**Cel:** Transformacja z "semantic search" na "AI assistant" który odpowiada na pytania na bazie książek.

**Obecny flow:**
```
User Query → Semantic Search → Lista fragmentów
```

**Docelowy flow (RAG):**
```
User Query → Semantic Search → GPT-4 + Context → Odpowiedź + Źródła
```

**Do zaimplementowania:**

#### 1. Moduł `answerer.py`
```python
class BookAnswerer:
    """Generates answers using GPT-4 based on book passages."""

    def generate_answer(self, question: str, passages: List[SearchResult]) -> Answer:
        """
        Generate answer using GPT-4 with retrieved context.

        Args:
            question: User's question
            passages: Top-k relevant passages from semantic search

        Returns:
            Answer object with text, sources, and citations
        """
```

**Funkcje:**
- Prompt engineering dla GPT-4
- Formatowanie kontekstu (top 5-10 passages)
- Generowanie odpowiedzi z cytatami
- Tracking źródeł (książka, autor, rozdział, strona)
- Error handling i fallbacks

#### 2. CLI komenda `ask`
```bash
python cli.py ask "What is stoicism?"

🤖 Answer:
Stoicism is an ancient Greek philosophy founded by Zeno of Citium around
300 BCE. The philosophy emphasizes virtue, wisdom, and living in accordance
with nature. According to Marcus Aurelius, the key principle is accepting
what we cannot control while focusing on our own thoughts and actions.

📚 Sources:
1. "Meditations" - Marcus Aurelius (Book 2, Chapter 1)
   "You have power over your mind - not outside events..."

2. "The Daily Stoic" - Ryan Holiday (Introduction)
   "Stoicism teaches us to focus only on what we can control..."
```

**Koszty:** ~$0.01-0.02 per pytanie (GPT-4o-mini) lub ~$0.05-0.10 (GPT-4)

#### 3. Konfiguracja w `config.py`
```python
class RAGConfig(BaseModel):
    llm_model: str = "gpt-4o-mini"  # lub "gpt-4"
    max_context_passages: int = 10
    temperature: float = 0.3
    max_tokens: int = 1000
    include_citations: bool = True
```

**Szacowany czas implementacji:** 2-3 godziny

---

### Priorytet 2: CLI Chat Interface - Interaktywna konwersacja

**Cel:** Wieloturowa konwersacja z AI assistant, z historią i kontekstem.

#### Biblioteki CLI Chat (badania 2025-01)

**NAJLEPSZA OPCJA: `prompt_toolkit` + `asyncio` + OpenAI**

Sprawdzony stack z produkcyjnych implementacji:
- ✅ **prompt_toolkit** - profesjonalny terminal UI
- ✅ **asyncio** - async handling dla streaming responses
- ✅ **OpenAI AsyncClient** - async API calls
- ✅ Historia komend (↑/↓), multi-line input, Vim/Emacs modes
- ✅ Slash commands (`/help`, `/clear`, `/save`)
- ✅ Session persistence (JSON files)

**Źródło:** [Building a Terminal LLM Chat App](https://recruit.gmo.jp/engineer/jisedai/blog/building-a-terminal-llm-chat-app-with-python-asyncio/) (GMO Engineering, 2025)

**Instalacja:**
```bash
pip install prompt-toolkit openai  # asyncio jest built-in
```

**Alternatywne biblioteki:**

**1. `rich` (dodatkowe formatowanie)**
- ✅ Kolorowy output, markdown rendering
- ✅ Progress bars, tables, panels
- ✅ Syntax highlighting
- Można kombinować z prompt_toolkit
```bash
pip install rich
```

**2. `simpleaichat`** (gotowiec)
- ✅ One-liner chat interface
- ✅ Minimal code complexity
- ❌ Mniej kontroli nad UI
```bash
pip install simpleaichat
```

**3. `Chainlit` / `Gradio`** (Web UI)
- ✅ Szybki prototyp z GUI
- ✅ Built-in chat components
- ❌ Nie jest CLI (wymaga browsera)

**4. `cmd` (built-in Python)**
- ✅ Zero dependencies
- ✅ Prosty REPL
- ❌ Brak zaawansowanych features
- ❌ Nie obsługuje async

**Rekomendacja końcowa:** `prompt_toolkit` + `asyncio` + `rich` (formatowanie)

### Gotowe przykłady do inspiracji:

1. **GeminiAI CLI** - https://github.com/notsopreety/geminiai
   - Session management, dynamic prompts, streaming

2. **OpenAI Terminal Chatbot** - https://www.digitalocean.com/community/tutorials/openai-terminal-chatbot
   - Tutorial DigitalOcean z przykładami

3. **ai-cli-chat** (PyPI) - https://pypi.org/project/ai-cli-chat/
   - Multi-model support, round-table discussions

#### Implementacja chat interface

```bash
python cli.py chat

╭─────────────────────────────────────────╮
│  📚 Local eBook AI Chat (RAG Mode)     │
│  Type 'help' for commands, 'exit' to quit │
╰─────────────────────────────────────────╯

You: What is stoicism?

🤖 Assistant: [streaming response...]
Stoicism is an ancient Greek philosophy...

   📖 Sources: Meditations (Marcus Aurelius), The Daily Stoic (Ryan Holiday)

You: How do stoics deal with adversity?

🤖 Assistant: [continuing from context...]
Building on the previous answer about stoicism, stoics view adversity as...

You: /sources
📚 Conversation sources (2 questions):
  1. Meditations - Marcus Aurelius
  2. The Daily Stoic - Ryan Holiday
  3. Enchiridion - Epictetus

You: /clear
✓ Conversation history cleared.

You: exit
Goodbye! 👋
```

**Features:**
- Wieloturowa konwersacja z pamięcią
- Historia poprzednich pytań jako kontekst
- Komendy specjalne:
  - `/help` - pomoc
  - `/sources` - pokaż źródła z konwersacji
  - `/clear` - wyczyść historię
  - `/save` - zapisz konwersację
  - `/exit` lub `exit` - wyjdź
- Streaming responses (opcjonalnie)
- Rich formatting (kolory, panele, markdown)

**Architektura techniczna (wg GMO Engineering):**

```python
# chat_interface.py

import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from openai import AsyncOpenAI
from pathlib import Path

class ChatInterface:
    """Interactive chat interface using prompt_toolkit + asyncio."""

    def __init__(self, answerer: BookAnswerer, config: SystemConfig):
        self.answerer = answerer
        self.config = config

        # Conversation history: {session_id: [messages]}
        self.conversations = {}
        self.current_session = "default"

        # Prompt toolkit session with history
        history_file = Path.home() / ".local/share/ebook-chat/history.txt"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        self.session = PromptSession(history=FileHistory(str(history_file)))

        # OpenAI async client
        self.client = AsyncOpenAI(api_key=config.openai.api_key)

    async def send_message(self, user_input: str) -> str:
        """Send message to LLM with conversation context."""

        # Get conversation history
        if self.current_session not in self.conversations:
            self.conversations[self.current_session] = []

        messages = self.conversations[self.current_session]

        # 1. Semantic search for context (from BookSearcher)
        search_results = await self.answerer.search_async(user_input)

        # 2. Format context from books
        context = self._format_context(search_results)

        # 3. Build messages with context
        messages.append({
            "role": "user",
            "content": f"Context from books:\n{context}\n\nQuestion: {user_input}"
        })

        # 4. Stream response from GPT-4
        full_response = ""
        async for chunk in await self.client.chat.completions.create(
            model=self.config.rag.llm_model,
            messages=messages,
            stream=True
        ):
            if chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_response += text
                print(text, end="", flush=True)  # Stream to terminal

        # 5. Save assistant response
        messages.append({"role": "assistant", "content": full_response})

        return full_response

    async def run(self):
        """Start interactive chat loop."""
        print("📚 Local eBook AI Chat")
        print("Type '/help' for commands, 'exit' to quit.\n")

        shutdown_event = asyncio.Event()

        # Handle Ctrl+C gracefully
        import signal
        signal.signal(signal.SIGINT, lambda s, f: shutdown_event.set())

        try:
            while not shutdown_event.is_set():
                # Get user input (supports multi-line with prompt_toolkit)
                try:
                    user_input = await self.session.prompt_async("You: ")
                except KeyboardInterrupt:
                    break

                if not user_input.strip():
                    continue

                # Handle slash commands
                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                    continue

                # Exit command
                if user_input.lower() in ["exit", "quit"]:
                    break

                # Send to LLM
                print("🤖 Assistant: ", end="")
                await self.send_message(user_input)
                print("\n")

        finally:
            # Save session on exit
            self._save_sessions()
            print("\nGoodbye! 👋")

    async def _handle_command(self, command: str):
        """Handle special slash commands."""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "/help":
            print("""
Available commands:
  /help              - Show this help
  /clear             - Clear conversation history
  /sources           - Show sources used in conversation
  /save [filename]   - Save conversation to file
  /sessions          - List all sessions
  /switch [session]  - Switch to different session
  exit               - Exit chat
            """)

        elif cmd == "/clear":
            self.conversations[self.current_session] = []
            print("✓ Conversation history cleared.")

        elif cmd == "/sources":
            # Show all book sources from current conversation
            sources = self._extract_sources()
            print(f"\n📚 Sources used in this conversation:")
            for i, source in enumerate(sources, 1):
                print(f"  {i}. {source}")

        elif cmd == "/save":
            filename = parts[1] if len(parts) > 1 else "conversation.md"
            self._save_conversation(filename)
            print(f"✓ Saved to {filename}")

        elif cmd == "/sessions":
            print("\nAvailable sessions:")
            for session_id in self.conversations:
                msg_count = len(self.conversations[session_id])
                marker = "→" if session_id == self.current_session else " "
                print(f"  {marker} {session_id} ({msg_count} messages)")

        else:
            print(f"Unknown command: {cmd}. Type /help for available commands.")

    def _save_sessions(self):
        """Persist sessions to JSON file."""
        sessions_file = Path.home() / ".local/share/ebook-chat/sessions.json"
        sessions_file.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(sessions_file, 'w') as f:
            json.dump(self.conversations, f, indent=2)
```

**Integracja z CLI (`cli.py`):**

```python
@cli.command()
def chat():
    """Start interactive chat with your book library (RAG mode)."""
    try:
        from chat_interface import ChatInterface

        # Initialize components
        config = get_config()
        answerer = BookAnswerer(config)
        interface = ChatInterface(answerer, config)

        # Run async event loop
        asyncio.run(interface.run())

    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
    except Exception as e:
        print(f"Error: {e}")
        raise
```

**Szacowany czas implementacji:** 2-3 godziny (z async + streaming)

---

### Priorytet 3: Rozszerzenia (opcjonalne)

#### 3.1 Streamlit/Gradio UI (Web Interface)
```bash
python cli.py ui
# → Otwiera przeglądarkę z GUI
```
- Drag & drop EPUB upload
- Wizualna historia konwersacji
- Podgląd źródeł z highlight'ami
- **Czas:** 3-4 godziny

#### 3.2 Wsparcie dla innych formatów
- PDF (PyPDF2/pdfplumber)
- MOBI (mobi)
- TXT (plain text)
- **Czas:** 2-3 godziny per format

#### 3.3 Export konwersacji
```bash
python cli.py chat --export conversation.md
```
- Export do Markdown, JSON, PDF
- **Czas:** 1 godzina

#### 3.4 Voice input (opcjonalnie)
- Whisper API dla voice-to-text
- **Czas:** 2-3 godziny

---

## Architektura RAG (v2.0)

```
┌─────────────────────────────────────────┐
│  CLI: chat / ask                         │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  BookAnswerer (answerer.py)             │
│  - Prompt engineering                    │
│  - Context management                    │
│  - Citation formatting                   │
└────────────┬────────────────────────────┘
             ↓
    ┌────────┴────────┐
    ↓                 ↓
┌──────────┐    ┌────────────┐
│ Searcher │    │ GPT-4 API  │
│ (exist.) │    │ (new)      │
└────┬─────┘    └──────┬─────┘
     ↓                 ↓
  ChromaDB      [Answer + Citations]
```

### Flow pojedynczego pytania (ask):
1. User: `python cli.py ask "What is stoicism?"`
2. Semantic Search → Top 10 passages
3. Format context for GPT-4
4. GPT-4 generates answer + citations
5. Display formatted answer + sources

### Flow konwersacji (chat):
1. User enters chat mode
2. Loop:
   - User types question
   - System adds question to history
   - Semantic search (with conversation context)
   - GPT-4 generates answer (aware of previous turns)
   - Display answer
   - Update history
3. Special commands (/sources, /clear, etc.)
4. Exit on 'exit' or Ctrl+C

---

## Koszty rozszerzenia (v2.0)

**RAG z GPT-4o-mini (rekomendowane):**
- Embedding (już policzone): ~$0.50-1.00 jednorazowo
- Answer generation: ~$0.01-0.02 per pytanie
- 100 pytań: ~$1-2
- 1000 pytań: ~$10-20

**RAG z GPT-4 (premium):**
- Answer generation: ~$0.05-0.10 per pytanie
- 100 pytań: ~$5-10

**Rekomendacja:** Zacząć od GPT-4o-mini (tańszy, szybszy, wystarczająco dobry)

---

## Dependencies do dodania (v2.0)

**requirements.txt - additions:**
```
# RAG
openai>=1.0.0  # już mamy, używamy również dla GPT-4

# CLI Chat Interface
prompt-toolkit>=3.0.0   # Interactive REPL
rich>=13.0.0            # Beautiful terminal output
pyperclip>=1.8.0        # Clipboard support (optional)

# Optional UI
streamlit>=1.20.0       # Web UI (optional)
gradio>=3.0.0          # Alternative Web UI (optional)
```

---

## Timeline implementacji

### Sprint 1: RAG Core (1 dzień)
- [ ] `answerer.py` - moduł RAG
- [ ] `cli.py ask` - komenda pojedynczego pytania
- [ ] Prompt engineering i testing
- [ ] Dokumentacja użycia

### Sprint 2: Chat Interface (1 dzień)
- [ ] `chat_interface.py` - interaktywny chat
- [ ] Integracja z prompt_toolkit + rich
- [ ] Historia konwersacji
- [ ] Komendy specjalne
- [ ] Testing UX

### Sprint 3: Polish & Docs (0.5 dnia)
- [ ] README update z przykładami RAG
- [ ] CHANGELOG update
- [ ] Testing end-to-end
- [ ] GitHub release v2.0

**Total: ~2-3 dni pracy**

---

## Pytania do rozstrzygnięcia

1. **Model GPT:** GPT-4o-mini (tańszy) czy GPT-4 (lepszy)?
2. **UI:** Tylko CLI czy też Streamlit/Gradio?
3. **Formaty:** Zostać przy EPUB czy rozszerzyć o PDF?
4. **Historia:** Zapisywać konwersacje do pliku czy tylko in-memory?
5. **Streaming:** Streamować odpowiedzi GPT (jak ChatGPT) czy całość naraz?

---

## Niezależność od narzędzi

**WAŻNE:** Projekt jest w 100% niezależny od:
- ❌ Claude Code
- ❌ Jakiegokolwiek IDE
- ❌ Specjalnych narzędzi

**Wymaga tylko:**
- ✅ Python 3.8+
- ✅ pip
- ✅ OpenAI API key

**Działa na:**
- ✅ Linux
- ✅ macOS
- ✅ Windows
- ✅ Dowolnym terminalu

---

## 🚀 Następne kroki (v2.2)

**Wyniki testu wydajności (2025-10-31):**
- Semantic search: 0.57s (2.3%) - bardzo szybki ✅
- GPT-5-mini generation: 23.57s (97.7%) - główne wąskie gardło ⚠️
- Rozwiązanie: streaming responses (pokazuj tekst na bieżąco jak ChatGPT)

1. **Streaming GPT** - priorytet #1, odpowiedź wyświetlana słowo po słowie (rozwiązuje problem wolności)
2. ✅ **PyMuPDF parser** - PDF + MOBI + inne formaty (zamiast tylko EPUB) - 60x szybszy, `pip install PyMuPDF` - **DONE (2025-11-05)**
3. **Zapis rozmowy** - `/save filename.md` w chat
4. **Schowek** - `/copy` dla ostatniej odpowiedzi
5. **Kolorki** - `rich` library dla ładniejszego terminala
6. ✅ **Compile E-book** - tworzy tematyczne e-booki z fragmentów książek - **DONE (2025-11-06)**
   - Nowa komenda CLI: `python cli.py compile-ebook "temat" output.epub`
   - Semantic search → grupowanie po książkach → generowanie EPUB
   - Proper EPUB struktura: TOC, metadata, CSS styling, citations
   - Legal safeguards: fragment limit (500 chars), full citations, "PERSONAL USE ONLY" disclaimer
   - Parametry: `--results`, `--min-similarity`, `--max-length`, `--title`, `--level`
   - Implementacja: `ebook_compiler.py` z klasą `EbookCompiler`
   - Testowane: psychology, meditation (11-40 fragmentów, 12-19 KB)

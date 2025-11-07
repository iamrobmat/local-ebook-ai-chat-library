# GUI Roadmap - Lokalna Biblioteka AI

## 🎯 Cel
Dodanie graficznego interfejsu (GUI) do istniejącej aplikacji CLI.

---

## 📊 Porównanie opcji

| | **Streamlit** | **Gradio** |
|---|---|---|
| **Czas implementacji** | 1-2h | 30 min |
| **Funkcje** | Wszystko (search, ask, chat, status, indexing) | Głównie chat + ask |
| **Wygląd** | Profesjonalny, więcej kontroli | Prosty, minimalistyczny |
| **Dla kogo** | Pełna aplikacja z wieloma funkcjami | Szybki chat interface |
| **Instalacja** | `pip install streamlit` | `pip install gradio` |
| **Uruchomienie** | `streamlit run app.py` | `python app.py` |

---

## 💡 Rekomendacja

**Streamlit** - bo masz dużo funkcji w CLI i warto wszystkie mieć w GUI.

**Gradio** - jeśli chcesz coś działającego w 30 minut i najbardziej Ci zależy na chat.

---

## 🚦 Następne kroki

1. Wybierz opcję GUI (Streamlit/Gradio)
2. Stworzyć plik? (tak/nie)

---

## 🚀 Przyszłe ulepszenia

### ✅ 1. Streaming GPT ⚡ (DONE - v2.2)
- ~~**Problem:** Odpowiedzi trwają ~23s~~
- ✓ **Zrobione:** Streaming słowo-po-słowie (5s total, natychmiastowy feedback)
- ✓ **Technologia:** OpenAI client + Iterator[str]
- ✓ **Commit:** `8df9aff` (2025-11-07)

### 2. Interactive Chat Interface (Claude Code style) 💬
- **Problem:** Za długie komendy (`python cli.py ask "pytanie"`)
- **Rozwiązanie:** `python cli.py` wchodzi od razu w chat (główny interfejs)
- **Funkcje:**
  - Slash commands: `/search`, `/compile`, `/settings`, `/help`
  - Regular text → pytanie do AI (bez prefiksu)
  - Rich formatting (panele, kolory, progress bars)
  - Autocomplete (Tab), historia (↑/↓), multi-line (Shift+Enter)
- **Technologie:**
  - `rich>=13.0.0` - formatowanie
  - `prompt-toolkit>=3.0.0` - autocomplete, historia
- **Struktura:**
  ```
  interactive_shell.py  # Główny chat
  commands/*.py         # Slash commands (search, compile, settings)
  ui/*.py              # Rich formatters, prompts
  ```
- **Czas:** 7-10h (Faza 1: podstawy 2-3h, Faza 2: komendy 2h, Faza 3: UX 2-3h)
- **Kompatybilność:** Stare komendy CLI nadal działają

### 3. Kolorki w CLI 🎨
- **Biblioteka:** `rich`
- **Funkcje:**
  - Kolorowy output
  - Markdown rendering
  - Progress bars, panels
- **Instalacja:** `pip install rich`
- **Czas:** 1-2h (częściowo w punkcie 2)

### 4. GUI - interfejs webowy 🖥️
- Wybór między Streamlit (pełna app) lub Gradio (szybki chat)
- Powyżej szczegóły obu opcji

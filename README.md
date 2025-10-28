# 🔍 Local eBook AI Chat Library

> Transform your personal eBook library into an AI-powered semantic search engine. Ask questions, find passages, and explore your books like never before.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-412991.svg)](https://openai.com/)

## ✨ What is this?

A **completely local**, privacy-focused AI search system for your EPUB book library. Instead of manually searching through hundreds of books, just ask a question in natural language and get relevant passages instantly.

Perfect for:
- 📚 Calibre users with large libraries
- 🔬 Researchers managing academic books
- 📖 Avid readers building personal knowledge bases
- 🎓 Students organizing study materials
- 💼 Professionals maintaining technical libraries

## 🎯 Key Features

- **🔒 Privacy First**: Everything runs locally. Your books never leave your machine (except for generating embeddings via OpenAI API)
- **💰 Incredibly Cheap**: ~$1 one-time cost for indexing 200 books
- **⚡ Lightning Fast**: Search results in milliseconds
- **🌍 Multilingual**: Works with English, Polish, Spanish, French, and many other languages
- **📊 Smart Chunking**: Adaptive text splitting optimized per book
- **🔄 Incremental Updates**: Only index new/changed books
- **🎨 Simple CLI**: Just 3 commands to master

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- EPUB books (Calibre library or any folder with EPUB files)

### Installation

```bash
# Clone the repository
git clone https://github.com/iamrobmat/local-ebook-ai-chat-library.git
cd local-ebook-ai-chat-library

# Install dependencies
cd rag-system
pip install -r requirements.txt

# Set up your OpenAI API key
cp ../.env.example ../.env
# Edit .env and add your OpenAI API key
```

### Usage

**1. Initialize the system:**
```bash
python cli.py init
```

**2. Index your library (one-time setup):**
```bash
# Point to your Calibre library or any folder with EPUB files
# Edit rag-system/config.py to set your books_root path
python cli.py index --full
```

This will take 15-30 minutes for ~200 books.

**3. Search your library:**
```bash
# Ask a question
python cli.py search "what is stoicism and daily practice"

# Search with filters
python cli.py search "economics" --author "Smith" --top 10

# Search only chapters or paragraphs
python cli.py search "meditation techniques" --level chapter
```

**4. Add new books:**
```bash
python cli.py update
```

## 📖 Example Queries

### Find philosophical concepts
```bash
$ python cli.py search "stoicism and daily practice"

Found 8 results:

1. Meditations - Marcus Aurelius
   Chapter: Book 2 (Ch. 2)
   Similarity: 0.892
   Preview: When you wake up in the morning, tell yourself: the people
   I deal with today will be meddling, ungrateful, arrogant...
```

### Find specific quotes
```bash
$ python cli.py search "waste of remaining time" --author "Marcus" --level paragraph

Found 3 results:

1. Meditations - Marcus Aurelius
   Chapter: Book 3 (Ch. 3)
   Similarity: 0.912
   Preview: Don't waste the rest of your time here worrying about other people...
```

### Explore topics across books
```bash
$ python cli.py search "invisible hand market forces" --top 15
```

## 📊 How It Works

```
Your EPUB Files
       ↓
  [Parse & Chunk]
       ↓
  OpenAI Embeddings (text-embedding-3-small)
       ↓
  ChromaDB (local vector database)
       ↓
  Semantic Search ✨
```

1. **Indexing**: Books are split into chapters and paragraphs
2. **Embedding**: Each chunk is converted to a 1536-dimensional vector via OpenAI
3. **Storage**: Vectors stored locally in ChromaDB (like SQLite, no server needed)
4. **Search**: Your query is embedded and compared via cosine similarity

## 💰 Cost Breakdown

Using OpenAI's `text-embedding-3-small` model:

- **Price**: $0.02 per 1M tokens
- **First indexing** (~200 books): **$0.50-$1.00** (one-time)
- **Updates** (new books): ~$0.02-$0.05 per book
- **Searching**: ~$0.00002 per query (essentially free)

**Total: Less than the cost of a coffee for a lifetime of intelligent book search!**

## 🗂️ Project Structure

```
local-ebook-ai-chat-library/
├── README.md                      # This file
├── LICENSE                        # MIT License
├── .env.example                   # Template for API key
├── CLAUDE.md                      # Technical specification
└── rag-system/
    ├── cli.py                     # Command-line interface
    ├── config.py                  # Configuration (Pydantic)
    ├── epub_parser.py             # EPUB parsing
    ├── indexer.py                 # Indexing & embeddings
    ├── searcher.py                # Semantic search
    ├── requirements.txt           # Python dependencies
    ├── README.md                  # Detailed documentation
    └── data/
        ├── chromadb/              # Vector database (auto-created)
        └── index_status.json      # Indexing state (auto-created)
```

## 🎛️ Configuration

Edit `rag-system/config.py` to customize:

- **Books location**: Point to your Calibre library or any EPUB folder
- **Chunking strategy**: Adjust chapter/paragraph token sizes
- **Search defaults**: Number of results, similarity threshold
- **OpenAI model**: Switch to other embedding models

## 🔧 Commands Reference

| Command | Description |
|---------|-------------|
| `python cli.py init` | Verify setup and create directories |
| `python cli.py index --full` | Index all books (first time) |
| `python cli.py update` | Index only new/changed books |
| `python cli.py search "query"` | Search your library |
| `python cli.py status` | View indexing statistics |
| `python cli.py clear` | Clear database (careful!) |

**Search options:**
- `--top N`: Number of results (default 10)
- `--level chapter|paragraph`: Search only chapters or paragraphs
- `--author "Name"`: Filter by author
- `--book "Title"`: Filter by book title
- `--full`: Show full text (no truncation)

## 🔐 Privacy & Security

- ✅ Books stored locally, never uploaded
- ✅ Database stored locally (ChromaDB)
- ✅ Only text chunks sent to OpenAI for embedding (required)
- ✅ No data retention by OpenAI for API calls
- ✅ No analytics, tracking, or telemetry
- ⚠️ Keep your `.env` file secure (contains API key)

## 🛠️ Troubleshooting

**"OPENAI_API_KEY not found"**
```bash
cp .env.example .env
# Edit .env and add your key
```

**"Collection not found"**
```bash
python cli.py index --full
```

**Slow indexing?**
- Normal: ~15-25 seconds per book
- For 200 books: 1-1.5 hours
- Increase `batch_size` in `config.py` to speed up (careful with rate limits)

**Book not found in search?**
1. Check file has `.epub` extension
2. Verify not in `rag-system` folder (ignored by default)
3. Run `python cli.py update`

## 🤝 Contributing

Contributions welcome! This is an open-source project designed to help people make the most of their personal libraries.

- 🐛 Report bugs via Issues
- 💡 Suggest features via Issues
- 🔧 Submit pull requests
- ⭐ Star the repo if you find it useful!

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings) - Semantic search magic
- [ChromaDB](https://www.trychroma.com/) - Embedded vector database
- [ebooklib](https://github.com/aerkalov/ebooklib) - EPUB parsing
- [Click](https://click.palletsprojects.com/) - Beautiful CLI interface

## ⭐ Star History

If this project helps you organize your reading, please consider giving it a star!

---

**Made with ❤️ for book lovers, by book lovers**

Questions? Open an issue or start a discussion!

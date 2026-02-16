# imessage-ai

Chat with your iMessage history using AI. Fully local, privacy-first, open-source.

Your iMessage data never leaves your machine. No API keys required for the default setup — just your Mac's `chat.db` + Ollama.

## Demo

> _Coming soon_

## Quick Start

```bash
brew install imessage-ai
imessage-ai setup    # indexes your chat.db
imessage-ai chat     # opens web UI at localhost:3000
```

Three commands. That's it.

## How It Works

Every Mac with iMessage stores your entire chat history in a local SQLite database (`~/Library/Messages/chat.db`). imessage-ai reads this database, chunks and embeds your conversations, and lets you search and chat with your history using an LLM.

```
chat.db → Indexer → Vector Store → LLM → Web UI
```

## Modes

### 🔒 Fully Local (Free & Private)

- **LLM:** Ollama (Llama 3, Mistral, etc.)
- **Embeddings:** Local sentence-transformers
- **Vector Store:** ChromaDB
- **Cost:** $0. Nothing leaves your machine. Ever.

### ☁️ Cloud LLM (Better Quality)

- **LLM:** OpenAI / Anthropic API
- **Embeddings:** OpenAI or local
- **Vector Store:** ChromaDB
- **Cost:** Pennies per query, smarter answers

## Features

- **AI Chat** — Ask questions about your message history in natural language
- **Conversation Browser** — Browse and search all conversations
- **Smart Search** — Filter by person, date range, group chat, keywords
- **Insights Dashboard** — Communication patterns, most texted contacts, sentiment over time, response time analytics
- **Export** — Export conversations as Markdown, JSON, or CSV
- **Privacy-first** — Everything runs locally by default. Your data stays on your machine.

## Project Structure

```
imessage-ai/
├── cli/              # CLI tool (setup, index, chat commands)
├── indexer/          # Parses chat.db, chunks messages, generates embeddings
├── server/           # API routes (FastAPI)
├── web/              # Next.js chat UI + insights dashboard
├── docker-compose.yml
├── PRD.md
└── README.md
```

## Requirements

- macOS (iMessage stores `chat.db` locally on Mac only)
- Full Disk Access permission (to read `~/Library/Messages/chat.db`)
- [Ollama](https://ollama.ai) (for local mode) or OpenAI/Anthropic API key (for cloud mode)

## Development

```bash
git clone https://github.com/bpk9/imessage-ai.git
cd imessage-ai

# Backend
cd server && pip install -r requirements.txt && uvicorn main:app --reload

# Frontend
cd web && npm install && npm run dev

# Indexer
cd indexer && pip install -r requirements.txt && python index.py
```

## Roadmap

- [x] Project scaffold & PRD
- [x] chat.db SQLite parser
- [x] Message chunking & embedding pipeline
- [x] ChromaDB vector store integration
- [ ] Ollama local LLM integration
- [ ] FastAPI backend with RAG pipeline
- [ ] Next.js web UI — chat interface
- [ ] Conversation browser & search
- [ ] Insights dashboard (patterns, sentiment, stats)
- [ ] CLI tool (`setup`, `index`, `chat`)
- [ ] Homebrew formula
- [ ] Docker Compose one-click setup
- [ ] OpenAI/Anthropic cloud mode
- [ ] Export (Markdown, JSON, CSV)

## Privacy

**Your data never leaves your machine in local mode.** The default setup uses Ollama for inference and local embeddings — zero network calls. Cloud mode is opt-in and only sends message chunks to the LLM API you configure.

No telemetry. No analytics. No accounts. Just your messages and your AI.

## License

MIT

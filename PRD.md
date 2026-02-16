# imessage-ai — Product Requirements Document

## Overview

**imessage-ai** is an open-source, privacy-first tool that lets you chat with your iMessage history using AI. It reads the local `chat.db` SQLite database on macOS, indexes conversations into a vector store, and provides a web UI for natural language search and AI-powered chat over your messages.

## Problem

- iMessage has no built-in search beyond basic keyword matching
- No way to ask contextual questions about your conversation history
- Existing AI chat tools require uploading data to cloud services
- Apple's own "Apple Intelligence" features are limited and not available on all devices
- No open-source tool exists for local iMessage AI — first-mover opportunity

## Target Users

1. **Power users / developers** — Want to search and analyze their message history programmatically
2. **Privacy-conscious users** — Want AI features without sending data to the cloud
3. **Non-technical Mac users** — Want a simple "chat with my texts" experience (Homebrew install + web UI)

## Core Principles

1. **Privacy-first** — Default mode is fully local. Nothing leaves the machine.
2. **Dead simple** — Three commands to get running. No config files for basic setup.
3. **Open-source** — MIT license, community-driven, no vendor lock-in.
4. **Mac-native** — Single platform focus = fewer edge cases, better UX.

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  chat.db     │────▶│   Indexer     │────▶│ Vector Store │────▶│   LLM (RAG)  │
│  (SQLite)    │     │  (Parser +   │     │  (ChromaDB)  │     │  (Ollama /   │
│              │     │   Embeddings)│     │              │     │   OpenAI)    │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                                                                      │
                                                                      ▼
                                          ┌──────────────┐     ┌──────────────┐
                                          │   Web UI      │◀────│   API Server │
                                          │  (Next.js)    │     │  (FastAPI)   │
                                          └──────────────┘     └──────────────┘
```

### Components

#### 1. Indexer (`indexer/`)
- **Input:** `~/Library/Messages/chat.db`
- **Parses:** `message`, `handle`, `chat`, `chat_handle_join`, `chat_message_join` tables
- **Handles:** SMS, iMessage, group chats, attachments (metadata only), reactions, threads
- **Chunking strategy:** Group messages by conversation + time window (e.g., 30-min gaps = new chunk)
- **Embeddings:** sentence-transformers locally (default) or OpenAI `text-embedding-3-small`
- **Output:** ChromaDB collection with metadata (sender, timestamp, chat_id, is_group)
- **Incremental indexing:** Track last indexed `ROWID`, only process new messages on re-index

#### 2. Vector Store (ChromaDB)
- **Local persistence** in `~/.imessage-ai/chroma/`
- **Collections:** `messages` (chunked convos), `contacts` (handle metadata)
- **Metadata filters:** sender, date range, chat type (1:1 vs group), chat name

#### 3. API Server (`server/`)
- **Framework:** FastAPI
- **Endpoints:**
  - `POST /chat` — RAG query (retrieve relevant chunks → send to LLM with context)
  - `GET /conversations` — List all conversations with metadata
  - `GET /conversations/:id` — Get messages for a conversation
  - `GET /search` — Keyword + semantic search with filters
  - `GET /insights` — Analytics and patterns
  - `POST /index` — Trigger re-index
  - `GET /status` — Index status, message count, last indexed
- **RAG pipeline:** Query → embed → retrieve top-k chunks → construct prompt with context → LLM → stream response

#### 4. Web UI (`web/`)
- **Framework:** Next.js 14 (App Router)
- **Pages:**
  - `/` — AI chat interface (main feature)
  - `/conversations` — Browse all conversations (iMessage-like sidebar)
  - `/conversations/:id` — View conversation thread
  - `/search` — Advanced search with filters
  - `/insights` — Dashboard with charts and stats
  - `/settings` — Configure LLM provider, re-index, export
- **Styling:** Tailwind CSS, shadcn/ui components
- **Real-time:** Server-sent events for streaming LLM responses

#### 5. CLI (`cli/`)
- **Language:** Python (Click)
- **Commands:**
  - `imessage-ai setup` — Check permissions, locate chat.db, run initial index
  - `imessage-ai index` — Re-index (incremental by default, `--full` for complete)
  - `imessage-ai chat` — Start web server + open browser to localhost:3000
  - `imessage-ai search <query>` — CLI search (no web UI needed)
  - `imessage-ai export <conversation> --format md|json|csv` — Export conversation
  - `imessage-ai status` — Show index stats
  - `imessage-ai config` — View/set configuration (LLM provider, model, etc.)

---

## Features (Prioritized)

### P0 — MVP
| Feature | Description |
|---------|-------------|
| chat.db parser | Read and parse all message types from SQLite |
| Message chunker | Group messages into contextual chunks by time + conversation |
| Local embeddings | Generate embeddings using sentence-transformers |
| ChromaDB storage | Store and query embedded chunks |
| RAG pipeline | Retrieve → context → LLM → response |
| Ollama integration | Local LLM inference, zero cost |
| Chat web UI | Clean chat interface to ask questions about your messages |
| CLI setup + chat | `imessage-ai setup` and `imessage-ai chat` commands |

### P1 — Core
| Feature | Description |
|---------|-------------|
| Conversation browser | iMessage-like sidebar + thread view |
| Search with filters | By person, date range, group, keyword + semantic |
| Incremental indexing | Only index new messages since last run |
| OpenAI/Anthropic mode | Cloud LLM option for better quality |
| Streaming responses | SSE for real-time LLM output |
| Homebrew formula | `brew install imessage-ai` |

### P2 — Differentiators
| Feature | Description |
|---------|-------------|
| Insights dashboard | Communication patterns, most texted, sentiment over time, response times, active hours |
| Export | Markdown, JSON, CSV per conversation or date range |
| Docker Compose | One-click setup for the full stack |
| Attachment awareness | Display image/video thumbnails, reference attachments in AI answers |
| Group chat intelligence | "What did [group] decide about [topic]?" |

### P3 — Nice to Have
| Feature | Description |
|---------|-------------|
| Scheduled auto-index | Background daemon that indexes new messages periodically |
| Notification summary | "What did I miss?" for conversations with many unread |
| Contact enrichment | Pull contact names from macOS Contacts.app |
| Multi-Mac sync | Merge indexes from multiple Macs (shared iCloud chat.db) |
| Plugin system | Custom analyzers / insights |

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| CLI | Python + Click | Simplest for Homebrew distribution, good SQLite support |
| Indexer | Python | sqlite3 stdlib, sentence-transformers, chromadb all Python |
| Embeddings (local) | sentence-transformers (`all-MiniLM-L6-v2`) | Fast, good quality, no API key |
| Embeddings (cloud) | OpenAI `text-embedding-3-small` | Better quality, cheap ($0.02/1M tokens) |
| Vector Store | ChromaDB | Simple, local-first, Python-native |
| LLM (local) | Ollama (Llama 3.1 8B default) | Free, private, good enough for RAG |
| LLM (cloud) | OpenAI GPT-4o-mini / Anthropic Claude | Better quality, opt-in |
| API Server | FastAPI | Fast, async, great DX, auto-docs |
| Web UI | Next.js 14 + Tailwind + shadcn/ui | Modern, fast, beautiful defaults |
| Charts | Recharts or Chart.js | Lightweight, good for insights dashboard |

---

## chat.db Schema (Key Tables)

```sql
-- Core tables we need:
message        -- ROWID, text, date, is_from_me, handle_id, cache_roomnames
handle         -- ROWID, id (phone/email), service
chat           -- ROWID, chat_identifier, display_name, group_id
chat_handle_join    -- chat_id, handle_id
chat_message_join   -- chat_id, message_id

-- Date format: Apple epoch (seconds since 2001-01-01) × 10^9 (nanoseconds)
-- Convert: datetime(message.date/1000000000 + 978307200, 'unixepoch')
```

---

## UX Flows

### First Run
```
$ imessage-ai setup

🔍 Looking for chat.db...
✅ Found: ~/Library/Messages/chat.db
📊 Found 147,832 messages across 342 conversations

⚠️  Full Disk Access required to read chat.db
   → System Settings > Privacy & Security > Full Disk Access
   → Add Terminal.app (or your terminal)

🔄 Indexing messages... (this takes 2-5 min on first run)
   ████████████████████████████████ 100% (147,832 messages)

✅ Setup complete! Run `imessage-ai chat` to start.
```

### Chat
```
$ imessage-ai chat

🚀 Starting imessage-ai at http://localhost:3000
   Using Ollama (llama3.1:8b) — fully local, nothing leaves your machine

> What did Sarah and I talk about last weekend?

Based on your conversations with Sarah (Feb 8-9), you discussed:
1. Dinner plans at that new Thai place on 2nd Ave
2. She recommended the Netflix show "Adolescence"
3. You made plans to meet at Central Park on Sunday at 2pm

Sources: 3 message chunks from Feb 8-9, 2025
```

---

## Success Metrics

- **GitHub stars** — Target: 1K in first month (HN launch)
- **Homebrew installs** — Track via formula analytics
- **Time to first query** — Target: < 5 minutes from `git clone` to asking a question
- **Community PRs** — Healthy open-source signal

## Go-to-Market

1. **Build MVP** — chat.db parser + RAG + basic web UI
2. **Dog-food it** — Use it daily, find edge cases
3. **Polish README** — GIF demo, clear install steps, architecture diagram
4. **Launch on Hacker News** — "Show HN: Chat with your iMessage history using AI — fully local, open-source"
5. **Post on Reddit** — r/MacOS, r/LocalLLaMA, r/selfhosted, r/privacy
6. **Twitter/X thread** — Demo video, privacy angle
7. **Homebrew formula** — Lower barrier to entry

---

## Open Questions

- [ ] Python monorepo or separate packages for CLI/indexer/server?
- [ ] FastAPI + Next.js or all-in-one Next.js with API routes?
- [ ] Homebrew: distribute as Python package (pipx) or compiled binary (PyInstaller)?
- [ ] License: MIT or AGPL? (MIT = more adoption, AGPL = prevents closed forks)
- [ ] Name: `imessage-ai`, `textmind`, `chatmemory`, or `recall`?

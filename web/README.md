# iMessage AI Web UI

Modern web interface for chatting with your iMessage history using AI.

## Features

- **Chat Interface** - Ask natural language questions about your messages
- **Conversation Browser** - Browse all your conversations with statistics
- **Semantic Search** - Find messages by meaning, not just keywords
- **Real-time Streaming** - See AI responses as they're generated
- **Source Citations** - See which messages informed each AI response
- **Fully Local** - Your data never leaves your computer

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:3000
```

## Requirements

- Node.js 18+
- FastAPI backend running on port 8000
- Indexed iMessage database

## Usage

1. **Start the FastAPI server** (from repo root):
   ```bash
   cd server && uvicorn main:app --reload
   ```

2. **Start the web UI** (from web directory):
   ```bash
   npm run dev
   ```

3. **Navigate to http://localhost:3000**

## Pages

- **/** - Main chat interface for AI conversations
- **/conversations** - Browse your message history
- **/search** - Advanced semantic search

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js UI    │────▶│   FastAPI       │────▶│   RAG Pipeline  │
│   (Port 3000)   │     │   (Port 8000)   │     │   (ChromaDB +   │
│                 │     │                 │     │    Ollama)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

The web UI communicates with the FastAPI backend, which handles all the AI processing and database queries.

## Development

Built with:
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Server-Sent Events** - Real-time streaming (future)

## Privacy

- All AI processing happens locally via Ollama
- No data is sent to external servers
- FastAPI backend runs on your machine
- Vector database is stored locally
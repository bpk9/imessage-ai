# iMessage AI FastAPI Server

REST API server providing chat, search, and management endpoints for the iMessage AI system.

## Features

- **Chat API**: RAG-powered chat with your iMessage history
- **Search API**: Vector similarity search across conversations  
- **Indexing API**: Manage message indexing and status
- **Health Monitoring**: System status and health checks
- **CORS Support**: Ready for web UI integration

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn main:app --reload

# Or with custom host/port
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

```bash
# Test API endpoints
python test_api.py
```

## Endpoints

### System
- `GET /` - API information
- `GET /health` - Health check
- `GET /status` - System status and LLM availability

### Chat
- `POST /chat` - Chat with your iMessage history
- `GET /chat/history` - Get current session history
- `DELETE /chat/history` - Clear session history

### Search
- `GET /search` - Search conversations by similarity

### Indexing
- `POST /index` - Start indexing process
- `GET /index/status` - Get indexing status
- `GET /conversations` - List indexed conversations

## Configuration

The server uses the same configuration as the CLI tool:
- **Vector Store**: ChromaDB (persistent storage)
- **LLM**: Ollama by default (configurable)
- **Cache Directory**: `.imessage_ai_server`

## Development

The server automatically:
- Initializes the indexer and chat systems
- Handles CORS for web UI integration
- Provides comprehensive error handling
- Runs background indexing tasks

## Production Deployment

For production, use a proper ASGI server:

```bash
# With gunicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# With uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Architecture

```
Web UI (Next.js)
    ↓ HTTP/REST
FastAPI Server
    ↓
iMessage Indexer + RAG System
    ↓
ChromaDB + Ollama LLM
    ↓
Local chat.db
```

The server acts as the bridge between the web interface and the local AI pipeline.
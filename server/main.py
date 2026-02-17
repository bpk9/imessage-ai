"""
FastAPI backend for iMessage AI

REST API server providing chat, search, and management endpoints.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add indexer to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'indexer'))

from indexer import iMessageIndexer, iMessageChat
from indexer.llm_integration import LLMManager, RAGResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="iMessage AI API",
    description="REST API for chatting with your iMessage history using AI",
    version="0.1.0"
)

# Add CORS middleware for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
chat_instance: Optional[iMessageChat] = None
indexer_instance: Optional[iMessageIndexer] = None


# Pydantic models for API
class ChatMessage(BaseModel):
    message: str
    include_sources: Optional[bool] = True
    filters: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    model: str
    processing_time_ms: int
    timestamp: str


class IndexingRequest(BaseModel):
    days_limit: Optional[int] = 30
    message_limit: Optional[int] = None
    force_reindex: Optional[bool] = False


class IndexingStatus(BaseModel):
    status: str  # 'indexed', 'not_indexed', 'indexing', 'error'
    total_chunks: Optional[int] = None
    total_chats: Optional[int] = None
    last_indexed: Optional[str] = None
    embedding_model: Optional[str] = None


class SystemStatus(BaseModel):
    api_status: str
    llm_backends: Dict[str, bool]
    indexing_status: IndexingStatus
    chat_available: bool


# Dependency to get chat instance
async def get_chat() -> iMessageChat:
    """Get or create chat instance"""
    global chat_instance
    
    if chat_instance is None:
        try:
            # Initialize with Ollama by default
            chat_instance = iMessageChat(llm_type='ollama')
            logger.info("Chat instance initialized")
        except Exception as e:
            logger.error(f"Failed to initialize chat: {e}")
            raise HTTPException(status_code=503, detail=f"Chat system unavailable: {e}")
    
    return chat_instance


# Dependency to get indexer instance
async def get_indexer() -> iMessageIndexer:
    """Get or create indexer instance"""
    global indexer_instance
    
    if indexer_instance is None:
        try:
            indexer_instance = iMessageIndexer(
                vector_store_type='chromadb',
                cache_dir='.imessage_ai_server'
            )
            # Try to load existing vector store
            try:
                indexer_instance.load_existing_vector_store()
            except Exception:
                logger.info("No existing vector store found")
            
            logger.info("Indexer instance initialized")
        except Exception as e:
            logger.error(f"Failed to initialize indexer: {e}")
            raise HTTPException(status_code=503, detail=f"Indexer unavailable: {e}")
    
    return indexer_instance


# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "iMessage AI API", 
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Get system status and health check"""
    try:
        # Check LLM backends
        llm_backends = LLMManager.get_available_llms()
        
        # Check indexing status
        try:
            indexer = await get_indexer()
            stats = indexer.get_stats()
            
            vs_stats = stats.get('vector_store', {})
            total_chunks = vs_stats.get('total_chunks', 0)
            
            if total_chunks > 0:
                indexing_status = IndexingStatus(
                    status="indexed",
                    total_chunks=total_chunks,
                    total_chats=vs_stats.get('unique_chats'),
                    embedding_model=stats.get('config', {}).get('embedding_model')
                )
            else:
                indexing_status = IndexingStatus(status="not_indexed")
                
        except Exception as e:
            logger.error(f"Error checking indexing status: {e}")
            indexing_status = IndexingStatus(status="error")
        
        # Check if chat is available
        chat_available = False
        try:
            chat = await get_chat()
            chat_available = chat.rag is not None
        except Exception:
            pass
        
        return SystemStatus(
            api_status="healthy",
            llm_backends=llm_backends,
            indexing_status=indexing_status,
            chat_available=chat_available
        )
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return SystemStatus(
            api_status="error",
            llm_backends={},
            indexing_status=IndexingStatus(status="error"),
            chat_available=False
        )


@app.post("/chat", response_model=ChatResponse)
async def chat_with_history(
    request: ChatMessage,
    chat: iMessageChat = Depends(get_chat)
):
    """Chat with your iMessage history"""
    
    if chat.rag is None:
        raise HTTPException(
            status_code=400, 
            detail="No indexed data available. Run indexing first."
        )
    
    try:
        # Get response with sources
        response = chat.ask_with_sources(
            request.message,
            filters=request.filters
        )
        
        if not response:
            raise HTTPException(status_code=500, detail="Failed to generate response")
        
        # Format response
        return ChatResponse(
            answer=response['answer'],
            sources=response['sources'] if request.include_sources else [],
            model=response['model'],
            processing_time_ms=response['processing_time_ms'],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat error: {e}")


@app.get("/chat/history")
async def get_chat_history(chat: iMessageChat = Depends(get_chat)):
    """Get current chat session history"""
    if chat.rag is None:
        return {"messages": []}
    
    try:
        stats = chat.rag.get_conversation_stats()
        return {
            "session_stats": stats,
            "message_count": stats.get('total_messages', 0)
        }
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        return {"messages": [], "error": str(e)}


@app.delete("/chat/history")
async def clear_chat_history(chat: iMessageChat = Depends(get_chat)):
    """Clear chat session history"""
    if chat.rag:
        chat.rag.clear_history()
    return {"message": "Chat history cleared"}


@app.post("/index")
async def start_indexing(
    request: IndexingRequest,
    background_tasks: BackgroundTasks,
    indexer: iMessageIndexer = Depends(get_indexer)
):
    """Start indexing iMessage data"""
    
    async def run_indexing():
        """Background task to run indexing"""
        try:
            logger.info(f"Starting indexing: {request.days_limit} days")
            
            metadata = indexer.run_full_index(
                days_limit=request.days_limit,
                message_limit=request.message_limit,
                save_index=True
            )
            
            logger.info(f"Indexing complete: {metadata['chunk_stats']['total_chunks']} chunks")
            
            # Reinitialize chat instance to pick up new data
            global chat_instance
            if chat_instance:
                chat_instance = None
            
        except Exception as e:
            logger.error(f"Indexing failed: {e}")
    
    # Start indexing in background
    background_tasks.add_task(run_indexing)
    
    return {
        "message": "Indexing started",
        "days_limit": request.days_limit,
        "status": "indexing"
    }


@app.get("/index/status", response_model=IndexingStatus)
async def get_indexing_status(indexer: iMessageIndexer = Depends(get_indexer)):
    """Get current indexing status"""
    try:
        stats = indexer.get_stats()
        
        vs_stats = stats.get('vector_store', {})
        total_chunks = vs_stats.get('total_chunks', 0)
        
        if total_chunks > 0:
            return IndexingStatus(
                status="indexed",
                total_chunks=total_chunks,
                total_chats=vs_stats.get('unique_chats'),
                embedding_model=stats.get('config', {}).get('embedding_model')
            )
        else:
            return IndexingStatus(status="not_indexed")
            
    except Exception as e:
        logger.error(f"Failed to get indexing status: {e}")
        return IndexingStatus(status="error")


@app.get("/search")
async def search_conversations(
    query: str,
    limit: Optional[int] = 5,
    chat: iMessageChat = Depends(get_chat)
):
    """Search conversations without generating chat response"""
    
    if chat.rag is None:
        raise HTTPException(
            status_code=400,
            detail="No indexed data available"
        )
    
    try:
        # Get relevant chunks
        results = chat.indexer.search(query, top_k=limit)
        
        # Format results
        search_results = []
        for chunk, score in results:
            participants = ", ".join(chunk.participants[:2])
            if len(chunk.participants) > 2:
                participants += f" (+{len(chunk.participants) - 2})"
            
            search_results.append({
                "participants": participants,
                "time_range": f"{chunk.start_time.strftime('%Y-%m-%d %H:%M')} - {chunk.end_time.strftime('%H:%M')}",
                "message_count": len(chunk.messages),
                "similarity_score": score,
                "preview": chunk.text_content[:200] + "..." if len(chunk.text_content) > 200 else chunk.text_content
            })
        
        return {
            "query": query,
            "results": search_results,
            "total_found": len(search_results)
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {e}")


@app.get("/conversations")
async def get_conversations(indexer: iMessageIndexer = Depends(get_indexer)):
    """Get list of indexed conversations"""
    try:
        stats = indexer.get_stats()
        
        # Basic conversation info from stats
        return {
            "total_chats": stats.get('vector_store', {}).get('unique_chats', 0),
            "total_chunks": stats.get('vector_store', {}).get('total_chunks', 0),
            "chunk_types": stats.get('chunks', {}).get('chunk_types', {}),
            "embedding_model": stats.get('config', {}).get('embedding_model')
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
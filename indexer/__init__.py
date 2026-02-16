"""
imessage-ai Indexer

Parses iMessage chat.db, chunks messages, and generates embeddings for vector search.
"""

from .chat_db_parser import ChatDBParser, Message, Handle, Chat
from .chunker import MessageChunker, MessageChunk
from .embeddings import EmbeddingGenerator, EmbeddingIndex, EmbeddingResult
from .vector_store import ChromaVectorStore, VectorStoreManager
from .pipeline import iMessageIndexer

__version__ = "0.1.0"
__all__ = [
    "ChatDBParser", "Message", "Handle", "Chat",
    "MessageChunker", "MessageChunk", 
    "EmbeddingGenerator", "EmbeddingIndex", "EmbeddingResult",
    "ChromaVectorStore", "VectorStoreManager",
    "iMessageIndexer"
]
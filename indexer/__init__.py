"""
imessage-ai Indexer

Parses iMessage chat.db, chunks messages, and generates embeddings for vector search.
"""

from .chat_db_parser import ChatDBParser, Message, Handle, Chat

__version__ = "0.1.0"
__all__ = ["ChatDBParser", "Message", "Handle", "Chat"]
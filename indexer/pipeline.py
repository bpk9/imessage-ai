"""
Main indexing pipeline for iMessage AI

Orchestrates the full pipeline: chat.db parsing → chunking → embedding → indexing
"""

import os
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from .chat_db_parser import ChatDBParser, Message, Chat
from .chunker import MessageChunker, MessageChunk  
from .embeddings import EmbeddingGenerator, EmbeddingIndex, EmbeddingResult


class iMessageIndexer:
    """Main indexer class that orchestrates the full pipeline"""
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        embedding_model: str = 'local',
        embedding_model_name: Optional[str] = None,
        chunk_strategy: str = 'adaptive',
        cache_dir: str = '.imessage_cache',
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize the iMessage indexer
        
        Args:
            db_path: Path to chat.db (defaults to macOS default)
            embedding_model: 'local' or 'openai'
            embedding_model_name: Specific model name
            chunk_strategy: 'adaptive', 'time_window', 'daily', or 'participant'
            cache_dir: Directory for caching embeddings and indexes
            openai_api_key: OpenAI API key if using OpenAI embeddings
        """
        self.db_path = db_path
        self.embedding_model = embedding_model
        self.chunk_strategy = chunk_strategy
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.chunker = MessageChunker()
        self.embedding_generator = EmbeddingGenerator(
            model_type=embedding_model,
            model_name=embedding_model_name,
            cache_dir=str(self.cache_dir / 'embeddings'),
            openai_api_key=openai_api_key
        )
        
        # Will be populated during indexing
        self.index: Optional[EmbeddingIndex] = None
        self.chats: List[Chat] = []
        self.chunks: List[MessageChunk] = []
        
    def run_full_index(
        self, 
        days_limit: Optional[int] = None,
        message_limit: Optional[int] = None,
        save_index: bool = True
    ) -> Dict:
        """
        Run the full indexing pipeline
        
        Args:
            days_limit: Only index messages from last N days
            message_limit: Maximum messages to process
            save_index: Whether to save the index to disk
            
        Returns:
            Dictionary with indexing statistics
        """
        start_time = datetime.now()
        print("🚀 Starting iMessage indexing pipeline...")
        
        # Step 1: Parse chat database
        print("📱 Parsing iMessage database...")
        with ChatDBParser(self.db_path) as parser:
            # Get database statistics
            db_stats = parser.get_chat_statistics()
            print(f"   Found {db_stats['total_messages']:,} messages in {db_stats['total_chats']} chats")
            
            # Get chats and messages
            self.chats = parser.get_chats()
            
            if days_limit:
                messages = parser.get_recent_messages(days=days_limit, limit=message_limit or 50000)
                print(f"   Using recent messages (last {days_limit} days): {len(messages):,}")
            else:
                messages = parser.get_messages(limit=message_limit)
                print(f"   Using all messages: {len(messages):,}")
        
        if not messages:
            raise ValueError("No messages found to index")
        
        # Step 2: Group messages by chat
        print("🗂️  Grouping messages by conversation...")
        chat_messages = self._group_messages_by_chat(messages)
        print(f"   Messages grouped into {len(chat_messages)} active chats")
        
        # Step 3: Chunk messages
        print("✂️  Chunking messages...")
        all_chunks = []
        for chat_id, chat_msgs in chat_messages.items():
            chat = next(c for c in self.chats if c.id == chat_id)
            
            if self.chunk_strategy == 'adaptive':
                chunks = self.chunker.chunk_messages_adaptive(chat_msgs, chat)
            elif self.chunk_strategy == 'time_window':
                chunks = self.chunker.chunk_by_time_windows(chat_msgs, chat)
            elif self.chunk_strategy == 'daily':
                chunks = self.chunker.chunk_by_daily_groups(chat_msgs, chat)
            elif self.chunk_strategy == 'participant':
                chunks = self.chunker.chunk_by_participants(chat_msgs, chat)
            else:
                raise ValueError(f"Unknown chunk strategy: {self.chunk_strategy}")
            
            all_chunks.extend(chunks)
        
        self.chunks = all_chunks
        chunk_stats = self.chunker.get_chunking_stats(all_chunks)
        print(f"   Created {chunk_stats['total_chunks']} chunks (avg: {chunk_stats['avg_messages_per_chunk']:.1f} msgs/chunk)")
        
        # Step 4: Generate embeddings
        print(f"🧠 Generating embeddings using {self.embedding_model} model...")
        embedding_results = self.embedding_generator.embed_chunks(all_chunks, use_cache=True)
        print(f"   Generated {len(embedding_results)} embeddings")
        
        # Step 5: Build search index
        print("🔍 Building search index...")
        self.index = EmbeddingIndex(embedding_results[0].embedding_dim)
        self.index.add_embeddings(embedding_results, all_chunks)
        index_stats = self.index.stats()
        print(f"   Indexed {index_stats['total_embeddings']} chunks across {index_stats['unique_chats']} chats")
        
        # Step 6: Save index if requested
        if save_index:
            index_path = self.cache_dir / f"imessage_index_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.index.save(str(index_path))
            print(f"💾 Saved index to {index_path}")
        
        # Step 7: Save metadata
        metadata = {
            'indexed_at': datetime.now().isoformat(),
            'db_path': str(self.db_path) if self.db_path else 'default',
            'embedding_model': self.embedding_model,
            'embedding_model_name': self.embedding_generator.model_name,
            'chunk_strategy': self.chunk_strategy,
            'days_limit': days_limit,
            'message_limit': message_limit,
            'database_stats': db_stats,
            'chunk_stats': chunk_stats,
            'index_stats': index_stats,
            'processing_time_seconds': (datetime.now() - start_time).total_seconds()
        }
        
        metadata_path = self.cache_dir / 'latest_index_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"✅ Indexing complete in {processing_time:.1f} seconds!")
        
        return metadata
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[MessageChunk, float]]:
        """
        Search the index for relevant message chunks
        
        Args:
            query: Search query text
            top_k: Number of results to return
            
        Returns:
            List of (MessageChunk, similarity_score) tuples
        """
        if not self.index:
            raise ValueError("Index not built. Run run_full_index() first.")
        
        # Generate embedding for query
        query_embedding = self.embedding_generator.embed_text(query)
        
        # Search index
        results = self.index.search_similar(query_embedding, top_k)
        
        # Convert results to MessageChunk objects
        chunk_results = []
        for metadata, score in results:
            # Find the corresponding chunk
            chunk = next(c for c in self.chunks if c.id == metadata['chunk_id'])
            chunk_results.append((chunk, score))
        
        return chunk_results
    
    def get_conversation_context(self, chunk_id: str, context_messages: int = 10) -> List[Message]:
        """
        Get additional context around a specific chunk
        
        Args:
            chunk_id: ID of the chunk to get context for
            context_messages: Number of messages before/after to include
            
        Returns:
            List of messages with context
        """
        chunk = next(c for c in self.chunks if c.id == chunk_id)
        
        # Get all messages from the same chat
        with ChatDBParser(self.db_path) as parser:
            all_chat_messages = parser.get_messages(chat_id=chunk.chat_id)
        
        # Find the chunk's message range
        chunk_start_id = chunk.messages[0].id
        chunk_end_id = chunk.messages[-1].id
        
        # Find indices
        start_idx = next(i for i, msg in enumerate(all_chat_messages) if msg.id == chunk_start_id)
        end_idx = next(i for i, msg in enumerate(all_chat_messages) if msg.id == chunk_end_id)
        
        # Get context
        context_start = max(0, start_idx - context_messages)
        context_end = min(len(all_chat_messages), end_idx + context_messages + 1)
        
        return all_chat_messages[context_start:context_end]
    
    def _group_messages_by_chat(self, messages: List[Message]) -> Dict[int, List[Message]]:
        """Group messages by chat_id and sort by date"""
        chat_groups = {}
        
        for message in messages:
            if message.chat_id not in chat_groups:
                chat_groups[message.chat_id] = []
            chat_groups[message.chat_id].append(message)
        
        # Sort messages within each chat by date
        for chat_id in chat_groups:
            chat_groups[chat_id].sort(key=lambda m: m.date)
        
        return chat_groups
    
    def load_existing_index(self, index_path: str) -> None:
        """Load a previously saved index"""
        self.index = EmbeddingIndex.load(index_path)
        print(f"📂 Loaded index from {index_path}")
        
        # Load metadata if available
        metadata_path = Path(index_path).parent / 'latest_index_metadata.json'
        if metadata_path.exists():
            with open(metadata_path) as f:
                metadata = json.load(f)
                print(f"   Index from {metadata['indexed_at']} with {metadata['index_stats']['total_embeddings']} chunks")
    
    def get_stats(self) -> Dict:
        """Get comprehensive statistics about the current index"""
        stats = {}
        
        if self.index:
            stats['index'] = self.index.stats()
        
        if self.chunks:
            stats['chunks'] = self.chunker.get_chunking_stats(self.chunks)
        
        if hasattr(self.embedding_generator, 'get_cache_stats'):
            stats['embedding_cache'] = self.embedding_generator.get_cache_stats()
        
        stats['config'] = {
            'embedding_model': self.embedding_model,
            'chunk_strategy': self.chunk_strategy,
            'cache_dir': str(self.cache_dir)
        }
        
        return stats


def main():
    """Example usage of the indexing pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Index iMessage conversations for AI search')
    parser.add_argument('--days', type=int, help='Only index messages from last N days')
    parser.add_argument('--limit', type=int, help='Maximum messages to process')
    parser.add_argument('--model', choices=['local', 'openai'], default='local', help='Embedding model type')
    parser.add_argument('--chunk-strategy', choices=['adaptive', 'time_window', 'daily', 'participant'], 
                       default='adaptive', help='Message chunking strategy')
    parser.add_argument('--openai-key', help='OpenAI API key (if using OpenAI embeddings)')
    parser.add_argument('--test-search', help='Test search query after indexing')
    
    args = parser.parse_args()
    
    try:
        # Initialize indexer
        indexer = iMessageIndexer(
            embedding_model=args.model,
            chunk_strategy=args.chunk_strategy,
            openai_api_key=args.openai_key
        )
        
        # Run indexing
        metadata = indexer.run_full_index(
            days_limit=args.days,
            message_limit=args.limit
        )
        
        print("\n📊 Indexing Results:")
        print(f"   Total messages processed: {metadata['database_stats']['total_messages']:,}")
        print(f"   Chunks created: {metadata['chunk_stats']['total_chunks']}")
        print(f"   Average messages per chunk: {metadata['chunk_stats']['avg_messages_per_chunk']:.1f}")
        print(f"   Processing time: {metadata['processing_time_seconds']:.1f} seconds")
        
        # Test search if requested
        if args.test_search:
            print(f"\n🔍 Testing search: '{args.test_search}'")
            results = indexer.search(args.test_search, top_k=3)
            
            for i, (chunk, score) in enumerate(results, 1):
                print(f"\n{i}. Similarity: {score:.3f}")
                print(f"   Chat: {', '.join(chunk.participants[:2])}")
                print(f"   Time: {chunk.start_time.strftime('%Y-%m-%d %H:%M')}")
                print(f"   Preview: {chunk.text_content[:150]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
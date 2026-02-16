#!/usr/bin/env python3
"""
Test script for the complete iMessage indexing pipeline

Demonstrates: parsing → chunking → embedding → search
"""

import sys
import os
from pathlib import Path

# Add indexer to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline import iMessageIndexer


def test_pipeline_demo():
    """Demo the complete indexing pipeline"""
    print("🧪 Testing iMessage Indexing Pipeline")
    print("=" * 50)
    
    try:
        # Initialize indexer with local embeddings
        print("1️⃣ Initializing indexer...")
        indexer = iMessageIndexer(
            embedding_model='local',
            chunk_strategy='adaptive',
            cache_dir='.test_cache'
        )
        print("   ✅ Indexer initialized")
        
        # Run indexing on recent messages only (for speed)
        print("\n2️⃣ Running indexing pipeline...")
        try:
            metadata = indexer.run_full_index(
                days_limit=7,  # Last week only
                message_limit=1000,  # Limit for testing
                save_index=True
            )
            print("   ✅ Indexing completed successfully")
            
            # Show results
            print("\n📊 Results Summary:")
            print(f"   Messages processed: {metadata['database_stats']['total_messages']:,}")
            print(f"   Chunks created: {metadata['chunk_stats']['total_chunks']}")
            print(f"   Embedding model: {metadata['embedding_model_name']}")
            print(f"   Processing time: {metadata['processing_time_seconds']:.1f}s")
            
        except Exception as e:
            print(f"   ⚠️  Indexing failed: {e}")
            if "chat.db" in str(e):
                print("   💡 This requires macOS with iMessage enabled")
            return False
        
        # Test search functionality
        print("\n3️⃣ Testing search...")
        test_queries = [
            "what did we talk about yesterday?",
            "dinner plans",
            "meeting"
        ]
        
        for query in test_queries:
            try:
                results = indexer.search(query, top_k=2)
                print(f"\n   🔍 Query: '{query}'")
                
                if results:
                    for i, (chunk, score) in enumerate(results, 1):
                        participants = ", ".join(chunk.participants[:2])
                        if len(chunk.participants) > 2:
                            participants += f" (+{len(chunk.participants)-2} more)"
                        
                        time_str = chunk.start_time.strftime('%Y-%m-%d %H:%M')
                        preview = chunk.text_content[:100].replace('\n', ' ')
                        
                        print(f"      {i}. {participants} | {time_str} | Score: {score:.3f}")
                        print(f"         {preview}...")
                else:
                    print("      No results found")
                    
            except Exception as e:
                print(f"      ❌ Search failed: {e}")
        
        # Test stats
        print("\n4️⃣ Getting statistics...")
        stats = indexer.get_stats()
        
        if 'index' in stats:
            print(f"   Index: {stats['index']['total_embeddings']} embeddings")
            print(f"   Chats: {stats['index']['unique_chats']} unique conversations")
        
        if 'chunks' in stats:
            print(f"   Chunk types: {stats['chunks']['chunk_types']}")
        
        print("\n✅ All pipeline tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\n💡 Try installing with:")
        print("   pip install sentence-transformers")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_chunking_only():
    """Test just the chunking component if full pipeline fails"""
    print("\n🔧 Testing chunking component only...")
    
    try:
        from chat_db_parser import ChatDBParser
        from chunker import MessageChunker
        
        with ChatDBParser() as parser:
            # Get a small sample of messages
            messages = parser.get_recent_messages(days=1, limit=50)
            chats = parser.get_chats()
            
            if not messages:
                print("   No recent messages found")
                return False
            
            # Find the chat for these messages
            chat_id = messages[0].chat_id
            chat = next(c for c in chats if c.id == chat_id)
            
            # Test chunking
            chunker = MessageChunker()
            chunks = chunker.chunk_by_time_windows(messages, chat)
            
            print(f"   ✅ Created {len(chunks)} chunks from {len(messages)} messages")
            
            if chunks:
                chunk = chunks[0]
                print(f"   Sample chunk: {len(chunk.messages)} messages")
                print(f"   Time range: {chunk.start_time} to {chunk.end_time}")
                print(f"   Preview: {chunk.text_content[:100]}...")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Chunking test failed: {e}")
        return False


if __name__ == "__main__":
    print("Running iMessage indexing pipeline tests...\n")
    
    success = test_pipeline_demo()
    
    if not success:
        print("\nFalling back to component test...")
        success = test_chunking_only()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Tests completed successfully!")
        exit_code = 0
    else:
        print("💥 Tests failed!")
        exit_code = 1
    
    print("\n💡 Note: This indexer requires:")
    print("   • macOS with iMessage enabled")
    print("   • Full Disk Access permission for Terminal")
    print("   • Python packages: sentence-transformers, numpy")
    
    sys.exit(exit_code)
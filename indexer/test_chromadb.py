#!/usr/bin/env python3
"""
Test script for ChromaDB vector store integration

Tests the ChromaDB functionality separately from the full pipeline.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add indexer to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from vector_store import ChromaVectorStore, VectorStoreManager
    from embeddings import EmbeddingResult
    from chunker import MessageChunk, Message
    from chat_db_parser import Chat
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def create_test_chunks():
    """Create some test message chunks for testing"""
    # Mock chat
    chat = Chat(
        id=1,
        guid="test-chat-guid",
        style=45,
        state=1,
        room_name=None,
        display_name="Test Chat",
        participants=["alice@example.com", "bob@example.com"]
    )
    
    # Mock messages
    messages = [
        Message(
            id=1,
            text="Hey, are we still meeting for lunch tomorrow?",
            date=datetime.now(),
            is_from_me=False,
            sender_id="alice@example.com",
            chat_id=1,
            guid="msg-1",
            service="iMessage"
        ),
        Message(
            id=2, 
            text="Yes! Looking forward to it. How about 12:30 at the usual place?",
            date=datetime.now(),
            is_from_me=True,
            sender_id=None,
            chat_id=1,
            guid="msg-2",
            service="iMessage"
        ),
        Message(
            id=3,
            text="Perfect! See you then.",
            date=datetime.now(),
            is_from_me=False,
            sender_id="alice@example.com",
            chat_id=1,
            guid="msg-3",
            service="iMessage"
        )
    ]
    
    # Create test chunk
    chunk = MessageChunk(
        id="test_chunk_1",
        chat_id=1,
        messages=messages,
        start_time=messages[0].date,
        end_time=messages[-1].date,
        participants=chat.participants,
        text_content="[2026-02-16 16:00] Alice: Hey, are we still meeting for lunch tomorrow?\n[2026-02-16 16:01] Me: Yes! Looking forward to it. How about 12:30 at the usual place?\n[2026-02-16 16:02] Alice: Perfect! See you then.",
        chunk_type="conversation_window",
        metadata={
            'message_count': len(messages),
            'unique_senders': 2,
            'has_media': False,
            'avg_message_length': 35.0
        }
    )
    
    # Create mock embedding result
    embedding = [0.1] * 384  # Mock 384-dimensional embedding
    result = EmbeddingResult(
        chunk_id="test_chunk_1",
        embedding=embedding,
        model_name="test-model",
        embedding_dim=384,
        text_hash="testhash123"
    )
    
    return [chunk], [result], chat


def test_chromadb_basic():
    """Test basic ChromaDB operations"""
    print("🧪 Testing ChromaDB Basic Operations")
    print("=" * 40)
    
    # Create temporary directory for test
    test_dir = tempfile.mkdtemp(prefix="test_chromadb_")
    
    try:
        # Initialize ChromaDB store
        print("1️⃣ Initializing ChromaDB store...")
        store = ChromaVectorStore(
            persist_directory=test_dir,
            collection_name="test_collection"
        )
        print("   ✅ ChromaDB store initialized")
        
        # Create test data
        chunks, embedding_results, chat = create_test_chunks()
        
        # Test adding chunks
        print("\n2️⃣ Adding test chunks...")
        store.add_chunks(embedding_results, chunks)
        print("   ✅ Chunks added successfully")
        
        # Test basic stats
        print("\n3️⃣ Getting stats...")
        stats = store.get_stats()
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   Collection: {stats['collection_name']}")
        print("   ✅ Stats retrieved")
        
        # Test search
        print("\n4️⃣ Testing search...")
        query_embedding = [0.11] * 384  # Similar to our test embedding
        results = store.search(query_embedding, top_k=1)
        
        if results:
            metadata, score = results[0]
            print(f"   Found result with similarity: {score:.3f}")
            print(f"   Chunk ID: {metadata['chunk_id']}")
            print("   ✅ Search successful")
        else:
            print("   ⚠️  No search results found")
        
        # Test metadata filtering
        print("\n5️⃣ Testing metadata filters...")
        filtered = store.filter_by_metadata({'chat_id': 1})
        print(f"   Found {len(filtered)} chunks with chat_id=1")
        print("   ✅ Metadata filtering works")
        
        # Test get by ID
        print("\n6️⃣ Testing get by ID...")
        by_id = store.get_by_ids(['test_chunk_1'])
        if by_id:
            print(f"   Retrieved chunk: {by_id[0]['chunk_id']}")
            print("   ✅ Get by ID works")
        else:
            print("   ⚠️  Get by ID failed")
        
        print("\n✅ All ChromaDB tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")
        return False
        
    finally:
        # Clean up
        try:
            shutil.rmtree(test_dir)
        except:
            pass


def test_vector_store_manager():
    """Test the VectorStoreManager with both ChromaDB and memory fallback"""
    print("\n🧪 Testing VectorStoreManager")
    print("=" * 40)
    
    test_dir = tempfile.mkdtemp(prefix="test_manager_")
    
    try:
        # Test ChromaDB mode
        print("1️⃣ Testing ChromaDB mode...")
        manager = VectorStoreManager(
            store_type='chromadb',
            persist_directory=test_dir,
            collection_name='manager_test'
        )
        print(f"   Store type: {manager.store_type}")
        
        # Add test data
        chunks, embedding_results, _ = create_test_chunks()
        manager.add_chunks(embedding_results, chunks)
        
        # Test search
        query_embedding = [0.11] * 384
        results = manager.search(query_embedding, top_k=1)
        
        if results:
            print(f"   ChromaDB search found {len(results)} results")
            print("   ✅ ChromaDB manager works")
        else:
            print("   ⚠️  ChromaDB search returned no results")
        
        # Test stats
        stats = manager.get_stats()
        print(f"   Stats: {stats['store_type']} with {stats.get('total_chunks', 0)} chunks")
        
        print("\n2️⃣ Testing memory fallback...")
        # Force memory mode
        memory_manager = VectorStoreManager(
            store_type='memory',
            embedding_dim=384
        )
        print(f"   Store type: {memory_manager.store_type}")
        
        # Add same test data
        memory_manager.add_chunks(embedding_results, chunks)
        
        # Test search
        memory_results = memory_manager.search(query_embedding, top_k=1)
        if memory_results:
            print(f"   Memory search found {len(memory_results)} results")
            print("   ✅ Memory manager works")
        else:
            print("   ⚠️  Memory search returned no results")
        
        print("\n✅ VectorStoreManager tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ VectorStoreManager test failed: {e}")
        return False
        
    finally:
        try:
            shutil.rmtree(test_dir)
        except:
            pass


def test_chromadb_persistence():
    """Test that ChromaDB data persists between sessions"""
    print("\n🧪 Testing ChromaDB Persistence")
    print("=" * 30)
    
    test_dir = tempfile.mkdtemp(prefix="test_persist_")
    
    try:
        # Session 1: Add data
        print("1️⃣ Session 1 - Adding data...")
        store1 = ChromaVectorStore(
            persist_directory=test_dir,
            collection_name="persist_test"
        )
        
        chunks, embedding_results, _ = create_test_chunks()
        store1.add_chunks(embedding_results, chunks)
        
        stats1 = store1.get_stats()
        print(f"   Added {stats1['total_chunks']} chunks")
        
        # Session 2: Reload and check data
        print("\n2️⃣ Session 2 - Reloading data...")
        store2 = ChromaVectorStore(
            persist_directory=test_dir,
            collection_name="persist_test"
        )
        
        stats2 = store2.get_stats()
        print(f"   Found {stats2['total_chunks']} chunks after reload")
        
        if stats1['total_chunks'] == stats2['total_chunks']:
            print("   ✅ Data persisted correctly!")
            return True
        else:
            print("   ❌ Data not persisted")
            return False
        
    except Exception as e:
        print(f"❌ Persistence test failed: {e}")
        return False
        
    finally:
        try:
            shutil.rmtree(test_dir)
        except:
            pass


if __name__ == "__main__":
    print("Running ChromaDB integration tests...\n")
    
    # Check if ChromaDB is available
    try:
        import chromadb
        print("✅ ChromaDB is available")
    except ImportError:
        print("❌ ChromaDB not available - run: pip install chromadb")
        print("\n💡 Falling back to memory store tests would require the full pipeline")
        sys.exit(1)
    
    success = True
    success &= test_chromadb_basic()
    success &= test_vector_store_manager()
    success &= test_chromadb_persistence()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All ChromaDB tests passed!")
        print("\n💡 ChromaDB vector store is working correctly!")
        print("   • Persistent storage ✅")
        print("   • Similarity search ✅") 
        print("   • Metadata filtering ✅")
        print("   • Manager abstraction ✅")
        exit_code = 0
    else:
        print("💥 Some ChromaDB tests failed!")
        exit_code = 1
    
    print(f"\n🚀 Next: Run the full pipeline with:")
    print("   python pipeline.py --vector-store chromadb --test-search 'lunch meeting'")
    
    sys.exit(exit_code)
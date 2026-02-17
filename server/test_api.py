#!/usr/bin/env python3
"""
Test script for iMessage AI FastAPI server

Tests the API endpoints to verify functionality.
"""

import requests
import json
import time
from typing import Dict, Any


class APIClient:
    """Simple API client for testing"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
    
    def get(self, endpoint: str) -> Dict[str, Any]:
        """GET request"""
        response = requests.get(f"{self.base_url}{endpoint}")
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request"""
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE request"""
        response = requests.delete(f"{self.base_url}{endpoint}")
        response.raise_for_status()
        return response.json()


def test_basic_endpoints():
    """Test basic API endpoints"""
    print("🧪 Testing Basic API Endpoints")
    print("=" * 35)
    
    client = APIClient()
    
    try:
        # Test root endpoint
        print("1️⃣ Testing root endpoint...")
        root_response = client.get("/")
        print(f"   ✅ Root: {root_response['message']}")
        
        # Test health check
        print("\n2️⃣ Testing health check...")
        health_response = client.get("/health")
        print(f"   ✅ Health: {health_response['status']}")
        
        # Test system status
        print("\n3️⃣ Testing system status...")
        status_response = client.get("/status")
        print(f"   API Status: {status_response['api_status']}")
        print(f"   LLM Backends: {status_response['llm_backends']}")
        print(f"   Chat Available: {status_response['chat_available']}")
        print(f"   Indexing: {status_response['indexing_status']['status']}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Is the server running?")
        print("💡 Start server: uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Basic endpoint test failed: {e}")
        return False


def test_indexing_endpoints():
    """Test indexing-related endpoints"""
    print("\n🧪 Testing Indexing Endpoints")
    print("=" * 30)
    
    client = APIClient()
    
    try:
        # Test indexing status
        print("1️⃣ Testing indexing status...")
        status_response = client.get("/index/status")
        print(f"   Status: {status_response['status']}")
        
        if status_response['total_chunks']:
            print(f"   Total chunks: {status_response['total_chunks']}")
            print(f"   Total chats: {status_response['total_chats']}")
        
        # Test conversations endpoint
        print("\n2️⃣ Testing conversations endpoint...")
        conversations_response = client.get("/conversations")
        print(f"   Total chats: {conversations_response['total_chats']}")
        print(f"   Total chunks: {conversations_response['total_chunks']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Indexing endpoint test failed: {e}")
        return False


def test_search_endpoint():
    """Test search functionality"""
    print("\n🧪 Testing Search Endpoint")
    print("=" * 25)
    
    client = APIClient()
    
    try:
        # Test search
        print("1️⃣ Testing search...")
        search_response = client.get("/search?query=test&limit=3")
        
        print(f"   Query: {search_response['query']}")
        print(f"   Results found: {search_response['total_found']}")
        
        if search_response['results']:
            for i, result in enumerate(search_response['results'][:2], 1):
                print(f"   {i}. {result['participants']} | {result['time_range']}")
                print(f"      Score: {result['similarity_score']:.3f}")
        else:
            print("   ⚠️  No search results (expected if no data indexed)")
        
        return True
        
    except Exception as e:
        print(f"❌ Search endpoint test failed: {e}")
        return False


def test_chat_endpoint():
    """Test chat functionality (if data is indexed)"""
    print("\n🧪 Testing Chat Endpoint")
    print("=" * 22)
    
    client = APIClient()
    
    try:
        # Test chat
        print("1️⃣ Testing chat...")
        
        chat_request = {
            "message": "What are some recent conversations?",
            "include_sources": True
        }
        
        chat_response = client.post("/chat", chat_request)
        
        print(f"   Answer: {chat_response['answer'][:100]}...")
        print(f"   Model: {chat_response['model']}")
        print(f"   Sources: {len(chat_response['sources'])}")
        print(f"   Processing time: {chat_response['processing_time_ms']}ms")
        
        # Test chat history
        print("\n2️⃣ Testing chat history...")
        history_response = client.get("/chat/history")
        print(f"   Session messages: {history_response.get('message_count', 0)}")
        
        return True
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print("   ⚠️  Chat not available (no indexed data)")
            return True
        else:
            print(f"❌ Chat endpoint test failed: {e}")
            return False
    except Exception as e:
        print(f"❌ Chat endpoint test failed: {e}")
        return False


def test_start_indexing():
    """Test starting indexing process"""
    print("\n🧪 Testing Indexing Start")
    print("=" * 25)
    
    client = APIClient()
    
    try:
        print("1️⃣ Testing indexing start (small sample)...")
        
        # Start indexing with small sample
        indexing_request = {
            "days_limit": 1,
            "message_limit": 100,
            "force_reindex": False
        }
        
        response = client.post("/index", indexing_request)
        
        print(f"   Status: {response['status']}")
        print(f"   Days limit: {response['days_limit']}")
        print("   ⏳ Indexing started in background...")
        
        # Wait a moment and check status
        print("\n2️⃣ Checking status after delay...")
        time.sleep(2)
        
        status_response = client.get("/index/status")
        print(f"   Current status: {status_response['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Indexing start test failed: {e}")
        return False


def run_comprehensive_test():
    """Run all tests"""
    print("🚀 iMessage AI FastAPI Server Tests")
    print("=" * 40)
    
    success = True
    
    # Basic tests
    success &= test_basic_endpoints()
    success &= test_indexing_endpoints()
    success &= test_search_endpoint()
    success &= test_chat_endpoint()
    
    # Indexing test (optional)
    print("\n" + "=" * 40)
    response = input("Would you like to test indexing? (y/N): ")
    if response.lower().startswith('y'):
        success &= test_start_indexing()
    
    # Summary
    print("\n" + "=" * 40)
    if success:
        print("🎉 All API tests passed!")
        print("\n💡 API is ready for web UI integration")
        print("   • Swagger docs: http://localhost:8000/docs")
        print("   • ReDoc: http://localhost:8000/redoc")
    else:
        print("💥 Some API tests failed!")
        print("🔧 Check server logs for details")
    
    return success


if __name__ == "__main__":
    run_comprehensive_test()
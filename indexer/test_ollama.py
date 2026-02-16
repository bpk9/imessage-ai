#!/usr/bin/env python3
"""
Test script for Ollama LLM integration

Tests the complete RAG pipeline: indexing + vector search + LLM generation
"""

import sys
import os
from pathlib import Path

# Add indexer to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_integration import OllamaLLM, LLMManager, RAGSystem
from chat_interface import iMessageChat


def test_ollama_connection():
    """Test basic Ollama connection and availability"""
    print("🧪 Testing Ollama Connection")
    print("=" * 30)
    
    try:
        # Test with default model
        print("1️⃣ Testing Ollama server connection...")
        ollama = OllamaLLM()
        
        if not ollama.is_available():
            print("❌ Ollama not available")
            print("\n💡 Make sure Ollama is running:")
            print("   • Install: https://ollama.ai")
            print("   • Start: ollama serve")
            print("   • Pull model: ollama pull llama3.2")
            return False
        
        print(f"✅ Ollama available with model: {ollama.model}")
        
        # List available models
        print("\n2️⃣ Listing available models...")
        models = ollama.list_models()
        if models:
            print("   Available models:")
            for model in models[:5]:  # Show first 5
                name = model['name']
                size = model.get('size', 0)
                size_gb = size / (1024**3) if size else 0
                print(f"     • {name} ({size_gb:.1f}GB)")
        else:
            print("   No models found")
        
        # Test generation
        print("\n3️⃣ Testing text generation...")
        from llm_integration import ChatMessage
        
        test_messages = [
            ChatMessage(role="user", content="What is 2+2? Answer briefly.")
        ]
        
        response = ollama.generate(test_messages)
        print(f"   Response: {response[:100]}{'...' if len(response) > 100 else ''}")
        
        if response and len(response.strip()) > 0:
            print("✅ Text generation working")
            return True
        else:
            print("❌ Text generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False


def test_rag_system():
    """Test the complete RAG system with mock data"""
    print("\n🧪 Testing RAG System")
    print("=" * 20)
    
    try:
        # Check if we can create a chat interface
        print("1️⃣ Initializing chat interface...")
        
        try:
            chat = iMessageChat(llm_type='ollama')
            print("✅ Chat interface initialized")
        except SystemExit:
            print("❌ Chat interface failed to initialize")
            return False
        
        # Check if we have indexed data
        print("\n2️⃣ Checking for indexed data...")
        if chat.rag is None:
            print("⚠️  No indexed data available")
            print("💡 To test RAG fully, run indexing first:")
            print("   python pipeline.py --days 7 --test-search 'test query'")
            return True  # Not a failure, just limited testing
        
        # Test RAG query
        print("\n3️⃣ Testing RAG query...")
        test_question = "What are some recent conversations?"
        
        response = chat.ask_with_sources(test_question)
        if response:
            print(f"   Question: {test_question}")
            print(f"   Answer: {response['answer'][:200]}...")
            print(f"   Sources: {len(response['sources'])} conversations")
            print(f"   Model: {response['model']}")
            print("✅ RAG query successful")
            return True
        else:
            print("❌ RAG query failed")
            return False
            
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        return False


def test_llm_manager():
    """Test the LLM manager with different providers"""
    print("\n🧪 Testing LLM Manager")
    print("=" * 20)
    
    print("1️⃣ Checking available LLM backends...")
    available = LLMManager.get_available_llms()
    
    for llm_type, is_available in available.items():
        status = "✅" if is_available else "❌"
        print(f"   {status} {llm_type}")
    
    if not available['ollama']:
        print("⚠️  Ollama not available for testing")
        return False
    
    print("\n2️⃣ Testing LLM creation...")
    try:
        # Test creating Ollama LLM
        ollama_llm = LLMManager.create_llm('ollama', model='llama3.2')
        print("✅ Ollama LLM created successfully")
        
        # Test other backends if available
        if available['openai']:
            print("⚠️  OpenAI available but requires API key")
        
        if available['anthropic']:
            print("⚠️  Anthropic available but requires API key")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM creation failed: {e}")
        return False


def demo_simple_chat():
    """Demonstrate a simple chat interaction"""
    print("\n🚀 Simple Chat Demo")
    print("=" * 20)
    
    try:
        # Initialize with Ollama
        print("Initializing chat with Ollama...")
        chat = iMessageChat(llm_type='ollama')
        
        if chat.rag is None:
            print("⚠️  No message data indexed.")
            print("This demo shows LLM functionality without iMessage context.")
            print()
            
            # Direct LLM test without RAG
            from llm_integration import ChatMessage
            test_messages = [
                ChatMessage(role="user", content="Tell me a brief joke about AI assistants.")
            ]
            
            response = chat.llm.generate(test_messages)
            print(f"🤖 AI: {response}")
            
        else:
            # Full RAG demo
            print("Running RAG demo with your message history...")
            
            demo_questions = [
                "What are some recent conversations I've had?",
                "Who do I text with most often?",
                "Any interesting topics from my messages?"
            ]
            
            for question in demo_questions:
                print(f"\n❓ {question}")
                answer = chat.ask(question)
                if answer:
                    print(f"🤖 {answer[:300]}{'...' if len(answer) > 300 else ''}")
                else:
                    print("🤖 Sorry, I couldn't find relevant information.")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False


if __name__ == "__main__":
    print("Running Ollama LLM integration tests...\n")
    
    success = True
    
    # Run tests
    success &= test_ollama_connection()
    success &= test_llm_manager() 
    success &= test_rag_system()
    
    # Run demo if basic tests pass
    if success:
        demo_simple_chat()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Ollama integration tests completed!")
        print("\n💡 Next steps:")
        print("   • Index your messages: python pipeline.py --days 7")
        print("   • Start chat: python chat_interface.py")
        print("   • Interactive mode: python chat_interface.py --question 'your question'")
        exit_code = 0
    else:
        print("💥 Some Ollama tests failed!")
        print("\n🔧 Troubleshooting:")
        print("   • Make sure Ollama is installed and running")
        print("   • Pull a model: ollama pull llama3.2")
        print("   • Check server: curl http://localhost:11434")
        exit_code = 1
    
    print(f"\n🚀 Ready for local AI chat with your iMessage history!")
    sys.exit(exit_code)
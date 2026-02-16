"""
Simple chat interface for iMessage AI

Provides both CLI and programmatic interfaces for chatting with your iMessage history.
"""

import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path
import argparse

from .pipeline import iMessageIndexer
from .llm_integration import LLMManager, RAGSystem, ChatMessage


class iMessageChat:
    """Main chat interface for iMessage AI"""
    
    def __init__(
        self,
        indexer: Optional[iMessageIndexer] = None,
        llm_type: str = 'ollama',
        llm_model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize chat interface
        
        Args:
            indexer: Pre-built indexer, or None to create one
            llm_type: 'ollama', 'openai', or 'anthropic' 
            llm_model: Specific model name
            api_key: API key for cloud providers
        """
        
        # Initialize or use provided indexer
        if indexer is None:
            print("🔧 Initializing indexer...")
            self.indexer = iMessageIndexer(
                vector_store_type='chromadb',
                cache_dir='.imessage_ai'
            )
            
            # Try to load existing vector store
            try:
                self.indexer.load_existing_vector_store()
                print("✅ Loaded existing vector store")
            except Exception:
                print("⚠️  No existing vector store found. Run indexing first.")
                self.indexer = None
        else:
            self.indexer = indexer
        
        # Initialize LLM
        print(f"🤖 Initializing {llm_type} LLM...")
        try:
            self.llm = LLMManager.create_llm(
                llm_type=llm_type,
                model=llm_model,
                api_key=api_key
            )
            
            if not self.llm.is_available():
                if llm_type == 'ollama':
                    print("❌ Ollama not available. Make sure Ollama is running and the model is installed.")
                    print(f"💡 Try: ollama pull {llm_model or 'llama3.2'}")
                else:
                    print(f"❌ {llm_type} not available. Check your API key and connection.")
                sys.exit(1)
            
            print(f"✅ {llm_type} LLM ready")
            
        except Exception as e:
            print(f"❌ Failed to initialize LLM: {e}")
            sys.exit(1)
        
        # Initialize RAG system if we have an indexer
        if self.indexer:
            self.rag = RAGSystem(self.llm, self.indexer)
        else:
            self.rag = None
    
    def ensure_indexed(self, days_limit: int = 30, force_reindex: bool = False) -> bool:
        """Ensure messages are indexed and ready for chat"""
        if not self.indexer:
            return False
        
        # Check if we already have a vector store
        try:
            stats = self.indexer.get_stats()
            if stats.get('vector_store', {}).get('total_chunks', 0) > 0 and not force_reindex:
                print(f"📊 Found {stats['vector_store']['total_chunks']} indexed chunks")
                return True
        except Exception:
            pass
        
        # Run indexing
        print(f"📱 Indexing messages from last {days_limit} days...")
        try:
            metadata = self.indexer.run_full_index(
                days_limit=days_limit,
                save_index=True
            )
            
            print(f"✅ Indexed {metadata['chunk_stats']['total_chunks']} message chunks")
            
            # Initialize RAG system
            self.rag = RAGSystem(self.llm, self.indexer)
            
            return True
            
        except Exception as e:
            print(f"❌ Indexing failed: {e}")
            return False
    
    def ask(self, question: str, **kwargs) -> Optional[str]:
        """Ask a question about your iMessage history"""
        if not self.rag:
            print("❌ No indexed data available. Run indexing first.")
            return None
        
        try:
            response = self.rag.ask(question, **kwargs)
            return response.answer
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return None
    
    def ask_with_sources(self, question: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Ask a question and return full response with sources"""
        if not self.rag:
            return None
        
        try:
            response = self.rag.ask(question, **kwargs)
            
            # Format sources
            sources = []
            for chunk in response.sources:
                participants = ", ".join(chunk.participants[:2])
                if len(chunk.participants) > 2:
                    participants += f" (+{len(chunk.participants) - 2})"
                
                sources.append({
                    'participants': participants,
                    'time_range': f"{chunk.start_time.strftime('%Y-%m-%d %H:%M')} - {chunk.end_time.strftime('%H:%M')}",
                    'message_count': len(chunk.messages),
                    'preview': chunk.text_content[:150] + "..." if len(chunk.text_content) > 150 else chunk.text_content
                })
            
            return {
                'answer': response.answer,
                'sources': sources,
                'model': response.model_used,
                'processing_time_ms': response.processing_time_ms
            }
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return None
    
    def start_interactive_chat(self):
        """Start interactive CLI chat session"""
        if not self.rag:
            print("❌ No indexed data available. Run indexing first.")
            return
        
        print("\n🚀 iMessage AI Chat")
        print("=" * 30)
        print("Ask questions about your iMessage history!")
        print("Commands: /help, /stats, /clear, /quit\n")
        
        while True:
            try:
                question = input("💬 You: ").strip()
                
                if not question:
                    continue
                
                # Handle commands
                if question.startswith('/'):
                    if question == '/quit' or question == '/exit':
                        print("👋 Goodbye!")
                        break
                    elif question == '/help':
                        self._show_help()
                        continue
                    elif question == '/stats':
                        self._show_stats()
                        continue
                    elif question == '/clear':
                        self.rag.clear_history()
                        print("🧹 Chat history cleared")
                        continue
                    else:
                        print(f"Unknown command: {question}")
                        continue
                
                # Process question
                print("🤔 Thinking...")
                
                response_data = self.ask_with_sources(question)
                if response_data:
                    print(f"\n🤖 Assistant: {response_data['answer']}\n")
                    
                    # Show sources if available
                    if response_data['sources']:
                        print("📚 Sources:")
                        for i, source in enumerate(response_data['sources'], 1):
                            print(f"  {i}. {source['participants']} | {source['time_range']}")
                            print(f"     {source['preview']}")
                        
                        print(f"\n⏱️  {response_data['processing_time_ms']}ms | {response_data['model']}")
                    
                    print()
                else:
                    print("❌ Sorry, I couldn't process your question.\n")
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
    
    def _show_help(self):
        """Show help information"""
        print("""
💡 iMessage AI Help

EXAMPLES:
• "What did I talk about with Alice yesterday?"
• "Show me funny conversations from last week"
• "When did I last discuss dinner plans?"
• "What were my most active group chats?"

COMMANDS:
• /help    - Show this help
• /stats   - Show indexing statistics  
• /clear   - Clear conversation history
• /quit    - Exit chat

TIPS:
• Be specific about people, dates, or topics
• Try different phrasings if you don't get good results
• The AI has access to your indexed message history
""")
    
    def _show_stats(self):
        """Show indexing and chat statistics"""
        if self.indexer:
            stats = self.indexer.get_stats()
            
            print("\n📊 Statistics:")
            
            # Vector store stats
            if 'vector_store' in stats:
                vs_stats = stats['vector_store']
                if vs_stats.get('total_chunks'):
                    print(f"  📁 Indexed chunks: {vs_stats['total_chunks']:,}")
                if vs_stats.get('unique_chats'):
                    print(f"  💬 Unique chats: {vs_stats['unique_chats']}")
            
            # Chunk stats
            if 'chunks' in stats:
                chunk_stats = stats['chunks']
                print(f"  📝 Avg messages per chunk: {chunk_stats.get('avg_messages_per_chunk', 0):.1f}")
            
            # Chat history
            if self.rag:
                chat_stats = self.rag.get_conversation_stats()
                print(f"  🗣️  Chat messages this session: {chat_stats['total_messages']}")
        else:
            print("No indexing statistics available")


def main():
    """CLI entry point for iMessage AI chat"""
    parser = argparse.ArgumentParser(description='Chat with your iMessage history using AI')
    
    # LLM options
    parser.add_argument('--llm', choices=['ollama', 'openai', 'anthropic'], 
                       default='ollama', help='LLM provider')
    parser.add_argument('--model', help='Specific model name')
    parser.add_argument('--api-key', help='API key for cloud providers')
    
    # Indexing options
    parser.add_argument('--index-days', type=int, default=30,
                       help='Days of message history to index')
    parser.add_argument('--reindex', action='store_true',
                       help='Force reindexing of messages')
    
    # Chat options
    parser.add_argument('--question', help='Ask a single question and exit')
    parser.add_argument('--show-sources', action='store_true',
                       help='Show source conversations for answers')
    
    args = parser.parse_args()
    
    try:
        # Initialize chat interface
        chat = iMessageChat(
            llm_type=args.llm,
            llm_model=args.model,
            api_key=args.api_key
        )
        
        # Ensure data is indexed
        if not chat.ensure_indexed(days_limit=args.index_days, force_reindex=args.reindex):
            print("❌ Failed to index messages. Cannot start chat.")
            return 1
        
        # Single question mode
        if args.question:
            if args.show_sources:
                response = chat.ask_with_sources(args.question)
                if response:
                    print(f"Answer: {response['answer']}\n")
                    
                    if response['sources']:
                        print("Sources:")
                        for i, source in enumerate(response['sources'], 1):
                            print(f"  {i}. {source['participants']} | {source['time_range']}")
                            print(f"     {source['preview']}\n")
                else:
                    print("No answer found.")
            else:
                answer = chat.ask(args.question)
                if answer:
                    print(answer)
                else:
                    print("No answer found.")
        else:
            # Interactive mode
            chat.start_interactive_chat()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
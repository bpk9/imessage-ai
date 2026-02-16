#!/usr/bin/env python3
"""
iMessage AI - Main CLI entry point

Simple command-line interface for chatting with your iMessage history using AI.
"""

import sys
import argparse
from pathlib import Path

# Add indexer to path
sys.path.insert(0, str(Path(__file__).parent / 'indexer'))

from indexer import iMessageIndexer
from indexer.chat_interface import iMessageChat
from indexer.llm_integration import LLMManager


def cmd_setup(args):
    """Setup/index iMessage data"""
    print("🚀 Setting up iMessage AI...")
    
    indexer = iMessageIndexer(
        embedding_model=args.embedding_model,
        vector_store_type='chromadb',
        openai_api_key=args.openai_key
    )
    
    print(f"📱 Indexing messages from last {args.days} days...")
    
    try:
        metadata = indexer.run_full_index(
            days_limit=args.days,
            message_limit=args.limit,
            save_index=True
        )
        
        print(f"✅ Setup complete!")
        print(f"   • Processed {metadata['database_stats']['total_messages']:,} messages")
        print(f"   • Created {metadata['chunk_stats']['total_chunks']} conversation chunks")
        print(f"   • Using {metadata['embedding_model_name']} embeddings")
        print(f"   • Processing time: {metadata['processing_time_seconds']:.1f}s")
        print(f"\n🚀 Ready to chat! Run: python imessage_ai.py chat")
        
        return 0
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1


def cmd_chat(args):
    """Start interactive chat"""
    print("🤖 Starting iMessage AI chat...")
    
    try:
        chat = iMessageChat(
            llm_type=args.llm,
            llm_model=args.model,
            api_key=args.api_key
        )
        
        # Ensure data is indexed
        if not chat.rag:
            print("⚠️  No indexed data found.")
            response = input("Would you like to index your messages now? (y/N): ")
            if response.lower().startswith('y'):
                if not chat.ensure_indexed(days_limit=args.index_days):
                    print("❌ Indexing failed. Cannot start chat.")
                    return 1
            else:
                print("💡 Run 'python imessage_ai.py setup' first to index your messages.")
                return 1
        
        # Single question or interactive mode
        if args.question:
            response = chat.ask_with_sources(args.question)
            if response:
                print(f"\n🤖 {response['answer']}")
                
                if response['sources'] and args.show_sources:
                    print(f"\n📚 Sources:")
                    for i, source in enumerate(response['sources'], 1):
                        print(f"  {i}. {source['participants']} | {source['time_range']}")
            else:
                print("❌ No answer found")
        else:
            chat.start_interactive_chat()
        
        return 0
        
    except Exception as e:
        print(f"❌ Chat failed: {e}")
        return 1


def cmd_status(args):
    """Show system status and statistics"""
    print("📊 iMessage AI Status")
    print("=" * 25)
    
    # Check LLM availability
    print("🤖 LLM Backends:")
    available_llms = LLMManager.get_available_llms()
    for llm_type, is_available in available_llms.items():
        status = "✅ Available" if is_available else "❌ Not available"
        print(f"   {llm_type}: {status}")
    
    # Check indexing status
    print("\n📁 Indexing Status:")
    try:
        indexer = iMessageIndexer(vector_store_type='chromadb')
        indexer.load_existing_vector_store()
        
        stats = indexer.get_stats()
        vs_stats = stats.get('vector_store', {})
        
        if vs_stats.get('total_chunks', 0) > 0:
            print(f"   ✅ {vs_stats['total_chunks']:,} conversation chunks indexed")
            print(f"   📊 {vs_stats.get('unique_chats', 'Unknown')} unique conversations")
            print(f"   🗄️  Store type: {vs_stats.get('store_type', 'Unknown')}")
        else:
            print("   ❌ No indexed data found")
            print("   💡 Run 'python imessage_ai.py setup' to index your messages")
        
    except Exception as e:
        print(f"   ⚠️  Could not check indexing status: {e}")
    
    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='iMessage AI - Chat with your iMessage history using AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python imessage_ai.py setup --days 30        # Index last 30 days of messages
  python imessage_ai.py chat                   # Start interactive chat
  python imessage_ai.py chat --question "what did I talk about yesterday?"
  python imessage_ai.py status                 # Check system status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Index your iMessage data')
    setup_parser.add_argument('--days', type=int, default=30, 
                             help='Number of days of messages to index')
    setup_parser.add_argument('--limit', type=int, 
                             help='Maximum number of messages to process')
    setup_parser.add_argument('--embedding-model', choices=['local', 'openai'], 
                             default='local', help='Embedding model type')
    setup_parser.add_argument('--openai-key', help='OpenAI API key')
    
    # Chat command
    chat_parser = subparsers.add_parser('chat', help='Start chat interface')
    chat_parser.add_argument('--llm', choices=['ollama', 'openai', 'anthropic'],
                            default='ollama', help='LLM provider')
    chat_parser.add_argument('--model', help='Specific model name')
    chat_parser.add_argument('--api-key', help='API key for cloud providers')
    chat_parser.add_argument('--question', help='Ask a single question')
    chat_parser.add_argument('--show-sources', action='store_true',
                            help='Show source conversations')
    chat_parser.add_argument('--index-days', type=int, default=30,
                            help='Days to index if no data found')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command
    if args.command == 'setup':
        return cmd_setup(args)
    elif args.command == 'chat':
        return cmd_chat(args)
    elif args.command == 'status':
        return cmd_status(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
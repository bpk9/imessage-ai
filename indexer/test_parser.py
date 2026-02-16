#!/usr/bin/env python3
"""
Test script for chat_db_parser.py

Run this to validate the parser works with a real chat.db file.
"""

import os
import sys
from pathlib import Path
from chat_db_parser import ChatDBParser


def test_parser_basic():
    """Basic smoke test of the parser"""
    print("🧪 Testing iMessage Database Parser")
    print("=" * 40)
    
    try:
        with ChatDBParser() as parser:
            print("✅ Successfully connected to chat.db")
            
            # Test statistics
            stats = parser.get_chat_statistics()
            print(f"📊 Found {stats['total_messages']:,} messages in {stats['total_chats']} chats")
            
            # Test handles
            handles = parser.get_handles()
            print(f"👥 Found {len(handles)} contact handles")
            
            if handles:
                print(f"   First handle: {handles[0].handle_id} ({handles[0].service})")
            
            # Test chats
            chats = parser.get_chats()
            print(f"💬 Found {len(chats)} chats")
            
            if chats:
                first_chat = chats[0]
                participants = ", ".join(first_chat.participants[:3])  # Show first 3
                if len(first_chat.participants) > 3:
                    participants += f" (and {len(first_chat.participants) - 3} more)"
                print(f"   First chat: {participants}")
            
            # Test recent messages
            recent = parser.get_recent_messages(days=1, limit=3)
            print(f"📱 Found {len(recent)} messages in last 24 hours")
            
            if recent:
                for i, msg in enumerate(recent[:2]):  # Show first 2
                    sender = "You" if msg.is_from_me else (msg.sender_id or "Unknown")
                    preview = (msg.text[:40] + "...") if len(msg.text) > 40 else msg.text
                    print(f"   {i+1}. {sender}: {preview}")
            
            print("\n✅ All parser tests passed!")
            
    except FileNotFoundError:
        print("❌ chat.db not found at ~/Library/Messages/chat.db")
        print("💡 This test requires macOS with iMessage enabled")
        return False
    except PermissionError:
        print("❌ Permission denied accessing chat.db")
        print("💡 Try granting Full Disk Access to Terminal in System Preferences")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True


def test_parser_custom_path():
    """Test parser with custom database path"""
    custom_path = "./test_chat.db"
    
    if not Path(custom_path).exists():
        print(f"⏭️  Skipping custom path test - {custom_path} doesn't exist")
        return True
    
    try:
        with ChatDBParser(custom_path) as parser:
            stats = parser.get_chat_statistics()
            print(f"✅ Custom path test passed - {stats['total_messages']} messages")
    except Exception as e:
        print(f"❌ Custom path test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("Running iMessage parser tests...\n")
    
    success = True
    success &= test_parser_basic()
    success &= test_parser_custom_path()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)
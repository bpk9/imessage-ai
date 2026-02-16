"""
iMessage chat.db SQLite parser

Extracts messages, contacts, and chat metadata from macOS iMessage database.
Database located at: ~/Library/Messages/chat.db
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Message:
    """Represents a single iMessage"""
    id: int
    text: Optional[str]
    date: datetime
    is_from_me: bool
    sender_id: Optional[str]  # handle_id or phone number
    chat_id: int
    guid: str
    service: str  # 'iMessage', 'SMS', etc.


@dataclass
class Handle:
    """Represents a contact/phone number"""
    id: int
    handle_id: str  # phone number or email
    service: str
    country: Optional[str]


@dataclass
class Chat:
    """Represents a conversation (1:1 or group)"""
    id: int
    guid: str
    style: int  # 43 = group chat, 45 = 1:1
    state: int
    room_name: Optional[str]
    display_name: Optional[str]
    participants: List[str]  # list of handle_ids


class ChatDBParser:
    """Parser for iMessage chat.db SQLite database"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default macOS iMessage database path
            home = Path.home()
            db_path = home / "Library" / "Messages" / "chat.db"
        
        self.db_path = Path(db_path)
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"chat.db not found at {self.db_path}")
        
        self.conn = None
    
    def __enter__(self):
        """Context manager entry"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.conn:
            self.conn.close()
    
    def _cocoa_timestamp_to_datetime(self, timestamp: int) -> datetime:
        """Convert Apple's Cocoa timestamp to Python datetime
        
        Cocoa timestamps are nanoseconds since 2001-01-01 00:00:00 UTC
        """
        if timestamp == 0:
            return datetime(1970, 1, 1)  # Fallback for zero timestamps
        
        # Convert nanoseconds to seconds and add Cocoa epoch offset
        cocoa_epoch = datetime(2001, 1, 1)
        seconds = timestamp / 1_000_000_000
        return datetime.fromtimestamp(cocoa_epoch.timestamp() + seconds)
    
    def get_handles(self) -> List[Handle]:
        """Get all contact handles (phone numbers/emails)"""
        if not self.conn:
            raise RuntimeError("Database not connected. Use with statement.")
        
        query = """
        SELECT ROWID, id, service, country
        FROM handle
        ORDER BY ROWID
        """
        
        cursor = self.conn.execute(query)
        handles = []
        
        for row in cursor.fetchall():
            handle = Handle(
                id=row['ROWID'],
                handle_id=row['id'],
                service=row['service'] or 'Unknown',
                country=row['country']
            )
            handles.append(handle)
        
        return handles
    
    def get_chats(self) -> List[Chat]:
        """Get all chat conversations with participants"""
        if not self.conn:
            raise RuntimeError("Database not connected. Use with statement.")
        
        # Get basic chat info
        chat_query = """
        SELECT ROWID, guid, style, state, room_name, display_name
        FROM chat
        ORDER BY ROWID
        """
        
        cursor = self.conn.execute(chat_query)
        chats = []
        
        for row in cursor.fetchall():
            chat_id = row['ROWID']
            
            # Get participants for this chat
            participants_query = """
            SELECT h.id as handle_id
            FROM chat_handle_join chj
            JOIN handle h ON chj.handle_id = h.ROWID
            WHERE chj.chat_id = ?
            """
            
            participants_cursor = self.conn.execute(participants_query, (chat_id,))
            participants = [p['handle_id'] for p in participants_cursor.fetchall()]
            
            chat = Chat(
                id=chat_id,
                guid=row['guid'],
                style=row['style'] or 0,
                state=row['state'] or 0,
                room_name=row['room_name'],
                display_name=row['display_name'],
                participants=participants
            )
            chats.append(chat)
        
        return chats
    
    def get_messages(self, chat_id: Optional[int] = None, limit: Optional[int] = None) -> List[Message]:
        """Get messages, optionally filtered by chat_id"""
        if not self.conn:
            raise RuntimeError("Database not connected. Use with statement.")
        
        # Base query - join messages with chats and handles
        query = """
        SELECT 
            m.ROWID as id,
            m.text,
            m.date,
            m.is_from_me,
            m.guid,
            m.service,
            cmj.chat_id,
            h.id as sender_handle
        FROM message m
        JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
        LEFT JOIN handle h ON m.handle_id = h.ROWID
        """
        
        params = []
        if chat_id is not None:
            query += " WHERE cmj.chat_id = ?"
            params.append(chat_id)
        
        query += " ORDER BY m.date ASC"
        
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor = self.conn.execute(query, params)
        messages = []
        
        for row in cursor.fetchall():
            # Skip empty messages
            if not row['text'] or row['text'].strip() == '':
                continue
            
            message = Message(
                id=row['id'],
                text=row['text'],
                date=self._cocoa_timestamp_to_datetime(row['date']),
                is_from_me=bool(row['is_from_me']),
                sender_id=row['sender_handle'],
                chat_id=row['chat_id'],
                guid=row['guid'],
                service=row['service'] or 'iMessage'
            )
            messages.append(message)
        
        return messages
    
    def get_recent_messages(self, days: int = 30, limit: int = 1000) -> List[Message]:
        """Get recent messages from the last N days"""
        if not self.conn:
            raise RuntimeError("Database not connected. Use with statement.")
        
        # Calculate cutoff timestamp (Cocoa format)
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        cocoa_cutoff = int((cutoff_date - datetime(2001, 1, 1).timestamp()) * 1_000_000_000)
        
        query = """
        SELECT 
            m.ROWID as id,
            m.text,
            m.date,
            m.is_from_me,
            m.guid,
            m.service,
            cmj.chat_id,
            h.id as sender_handle
        FROM message m
        JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
        LEFT JOIN handle h ON m.handle_id = h.ROWID
        WHERE m.date > ? AND m.text IS NOT NULL AND m.text != ''
        ORDER BY m.date DESC
        LIMIT ?
        """
        
        cursor = self.conn.execute(query, (cocoa_cutoff, limit))
        messages = []
        
        for row in cursor.fetchall():
            message = Message(
                id=row['id'],
                text=row['text'],
                date=self._cocoa_timestamp_to_datetime(row['date']),
                is_from_me=bool(row['is_from_me']),
                sender_id=row['sender_handle'],
                chat_id=row['chat_id'],
                guid=row['guid'],
                service=row['service'] or 'iMessage'
            )
            messages.append(message)
        
        return messages
    
    def get_chat_statistics(self) -> Dict[str, int]:
        """Get basic statistics about the database"""
        if not self.conn:
            raise RuntimeError("Database not connected. Use with statement.")
        
        stats = {}
        
        # Total messages
        cursor = self.conn.execute("SELECT COUNT(*) FROM message WHERE text IS NOT NULL AND text != ''")
        stats['total_messages'] = cursor.fetchone()[0]
        
        # Total chats
        cursor = self.conn.execute("SELECT COUNT(*) FROM chat")
        stats['total_chats'] = cursor.fetchone()[0]
        
        # Total handles
        cursor = self.conn.execute("SELECT COUNT(*) FROM handle")
        stats['total_handles'] = cursor.fetchone()[0]
        
        # Messages from me vs others
        cursor = self.conn.execute("SELECT COUNT(*) FROM message WHERE is_from_me = 1 AND text IS NOT NULL")
        stats['messages_from_me'] = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM message WHERE is_from_me = 0 AND text IS NOT NULL")
        stats['messages_from_others'] = cursor.fetchone()[0]
        
        return stats


def main():
    """Test the parser with some basic queries"""
    try:
        with ChatDBParser() as parser:
            print("iMessage Database Parser")
            print("=" * 30)
            
            # Get statistics
            stats = parser.get_chat_statistics()
            print(f"📊 Database Statistics:")
            print(f"  Total messages: {stats['total_messages']:,}")
            print(f"  Total chats: {stats['total_chats']:,}")
            print(f"  Total contacts: {stats['total_handles']:,}")
            print(f"  Messages from me: {stats['messages_from_me']:,}")
            print(f"  Messages from others: {stats['messages_from_others']:,}")
            print()
            
            # Get recent messages
            print("📱 Recent Messages (last 7 days, limit 5):")
            recent = parser.get_recent_messages(days=7, limit=5)
            for msg in recent[:5]:
                sender = "Me" if msg.is_from_me else msg.sender_id or "Unknown"
                text_preview = msg.text[:50] + "..." if len(msg.text) > 50 else msg.text
                print(f"  {msg.date.strftime('%Y-%m-%d %H:%M')} | {sender}: {text_preview}")
            print()
            
            # Get top chats by message count
            print("💬 Most Active Chats:")
            chats = parser.get_chats()[:5]
            for chat in chats:
                participants_str = ", ".join(chat.participants) if chat.participants else "Unknown"
                chat_name = chat.display_name or participants_str
                print(f"  Chat {chat.id}: {chat_name}")
    
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\n💡 This tool requires macOS with iMessage enabled.")
        print("   The chat.db file is located at ~/Library/Messages/chat.db")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
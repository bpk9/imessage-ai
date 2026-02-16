"""
Message chunking for iMessage conversations

Groups messages into semantically meaningful chunks for embedding and retrieval.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from .chat_db_parser import Message, Chat


@dataclass
class MessageChunk:
    """A chunk of related messages for embedding"""
    id: str  # Unique chunk identifier
    chat_id: int
    messages: List[Message]
    start_time: datetime
    end_time: datetime
    participants: List[str]
    text_content: str  # Combined text for embedding
    chunk_type: str  # 'conversation_window', 'topic_shift', 'daily_group'
    metadata: Dict  # Additional context


class MessageChunker:
    """Chunks messages into semantic groups for embedding"""
    
    def __init__(
        self,
        time_window_minutes: int = 30,
        max_messages_per_chunk: int = 50,
        min_messages_per_chunk: int = 3,
        topic_shift_threshold: float = 0.7  # Future: semantic similarity threshold
    ):
        self.time_window_minutes = time_window_minutes
        self.max_messages_per_chunk = max_messages_per_chunk 
        self.min_messages_per_chunk = min_messages_per_chunk
        self.topic_shift_threshold = topic_shift_threshold
    
    def chunk_by_time_windows(self, messages: List[Message], chat: Chat) -> List[MessageChunk]:
        """Group messages by time windows (conversation sessions)"""
        if not messages:
            return []
        
        chunks = []
        current_chunk_messages = []
        window_start = messages[0].date
        
        for message in messages:
            # Check if we should start a new chunk
            time_gap = message.date - (current_chunk_messages[-1].date if current_chunk_messages else window_start)
            should_split = (
                time_gap > timedelta(minutes=self.time_window_minutes) or
                len(current_chunk_messages) >= self.max_messages_per_chunk
            )
            
            if should_split and len(current_chunk_messages) >= self.min_messages_per_chunk:
                # Create chunk from current messages
                chunk = self._create_chunk(
                    current_chunk_messages, 
                    chat, 
                    'conversation_window'
                )
                chunks.append(chunk)
                current_chunk_messages = []
                window_start = message.date
            
            current_chunk_messages.append(message)
        
        # Handle remaining messages
        if len(current_chunk_messages) >= self.min_messages_per_chunk:
            chunk = self._create_chunk(
                current_chunk_messages, 
                chat, 
                'conversation_window'
            )
            chunks.append(chunk)
        elif chunks:  # Add to last chunk if too few messages
            chunks[-1].messages.extend(current_chunk_messages)
            chunks[-1].end_time = current_chunk_messages[-1].date
            chunks[-1].text_content = self._combine_message_text(chunks[-1].messages)
        
        return chunks
    
    def chunk_by_daily_groups(self, messages: List[Message], chat: Chat) -> List[MessageChunk]:
        """Group messages by day"""
        if not messages:
            return []
        
        chunks = []
        current_day = None
        current_chunk_messages = []
        
        for message in messages:
            message_day = message.date.date()
            
            # Check if we've moved to a new day
            if current_day and message_day != current_day:
                if len(current_chunk_messages) >= self.min_messages_per_chunk:
                    chunk = self._create_chunk(
                        current_chunk_messages,
                        chat,
                        'daily_group'
                    )
                    chunks.append(chunk)
                current_chunk_messages = []
            
            current_day = message_day
            current_chunk_messages.append(message)
        
        # Handle remaining messages
        if len(current_chunk_messages) >= self.min_messages_per_chunk:
            chunk = self._create_chunk(
                current_chunk_messages,
                chat,
                'daily_group'
            )
            chunks.append(chunk)
        
        return chunks
    
    def chunk_by_participants(self, messages: List[Message], chat: Chat) -> List[MessageChunk]:
        """Group messages by conversation turns (when participants change)"""
        if not messages:
            return []
        
        chunks = []
        current_chunk_messages = []
        current_speaker = None
        
        for message in messages:
            speaker = message.sender_id if not message.is_from_me else 'me'
            
            # Check for speaker change or chunk size limit
            should_split = (
                current_speaker and speaker != current_speaker or
                len(current_chunk_messages) >= self.max_messages_per_chunk
            )
            
            if should_split and len(current_chunk_messages) >= self.min_messages_per_chunk:
                chunk = self._create_chunk(
                    current_chunk_messages,
                    chat,
                    'participant_turn'
                )
                chunks.append(chunk)
                current_chunk_messages = []
            
            current_speaker = speaker
            current_chunk_messages.append(message)
        
        # Handle remaining messages
        if len(current_chunk_messages) >= self.min_messages_per_chunk:
            chunk = self._create_chunk(
                current_chunk_messages,
                chat,
                'participant_turn'
            )
            chunks.append(chunk)
        
        return chunks
    
    def chunk_messages_adaptive(self, messages: List[Message], chat: Chat) -> List[MessageChunk]:
        """Adaptively chunk messages using the best strategy for the chat type"""
        if not messages:
            return []
        
        # Choose strategy based on chat characteristics
        if len(chat.participants) <= 2:
            # 1:1 chat - use time windows
            return self.chunk_by_time_windows(messages, chat)
        elif len(messages) > 1000:
            # Large group chat - use daily groups
            return self.chunk_by_daily_groups(messages, chat)
        else:
            # Small/medium group - use time windows
            return self.chunk_by_time_windows(messages, chat)
    
    def _create_chunk(
        self, 
        messages: List[Message], 
        chat: Chat, 
        chunk_type: str
    ) -> MessageChunk:
        """Create a MessageChunk from a list of messages"""
        if not messages:
            raise ValueError("Cannot create chunk from empty messages list")
        
        # Generate unique chunk ID
        chunk_id = f"chat_{chat.id}_{chunk_type}_{messages[0].id}_{messages[-1].id}"
        
        # Combine message text
        text_content = self._combine_message_text(messages)
        
        # Calculate time range
        start_time = min(msg.date for msg in messages)
        end_time = max(msg.date for msg in messages)
        
        # Generate metadata
        metadata = {
            'message_count': len(messages),
            'unique_senders': len(set(
                msg.sender_id if not msg.is_from_me else 'me' 
                for msg in messages
            )),
            'has_media': any(self._message_has_media(msg) for msg in messages),
            'avg_message_length': sum(len(msg.text or '') for msg in messages) / len(messages),
            'chat_style': chat.style,
            'chat_name': chat.display_name or ', '.join(chat.participants[:3])
        }
        
        return MessageChunk(
            id=chunk_id,
            chat_id=chat.id,
            messages=messages,
            start_time=start_time,
            end_time=end_time,
            participants=chat.participants,
            text_content=text_content,
            chunk_type=chunk_type,
            metadata=metadata
        )
    
    def _combine_message_text(self, messages: List[Message]) -> str:
        """Combine messages into a single text string for embedding"""
        combined_parts = []
        
        for msg in messages:
            if not msg.text or msg.text.strip() == '':
                continue
            
            # Format: "Sender: Message text"
            sender = 'Me' if msg.is_from_me else (msg.sender_id or 'Unknown')
            timestamp = msg.date.strftime('%Y-%m-%d %H:%M')
            
            # Create readable message format
            part = f"[{timestamp}] {sender}: {msg.text.strip()}"
            combined_parts.append(part)
        
        return '\n'.join(combined_parts)
    
    def _message_has_media(self, message: Message) -> bool:
        """Check if message contains media (simplified heuristic)"""
        if not message.text:
            return False
        
        # Simple heuristics for media messages
        media_indicators = [
            'attachment:', 'image:', 'video:', 'audio:',
            '\ufffc',  # Object replacement character (media placeholder)
            'shared a',
        ]
        
        text_lower = message.text.lower()
        return any(indicator in text_lower for indicator in media_indicators)
    
    def get_chunking_stats(self, chunks: List[MessageChunk]) -> Dict:
        """Get statistics about the chunking results"""
        if not chunks:
            return {}
        
        total_messages = sum(len(chunk.messages) for chunk in chunks)
        chunk_sizes = [len(chunk.messages) for chunk in chunks]
        text_lengths = [len(chunk.text_content) for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'total_messages': total_messages,
            'avg_messages_per_chunk': total_messages / len(chunks),
            'min_messages_per_chunk': min(chunk_sizes),
            'max_messages_per_chunk': max(chunk_sizes),
            'avg_text_length': sum(text_lengths) / len(chunks),
            'chunk_types': {
                chunk_type: sum(1 for c in chunks if c.chunk_type == chunk_type)
                for chunk_type in set(c.chunk_type for c in chunks)
            }
        }
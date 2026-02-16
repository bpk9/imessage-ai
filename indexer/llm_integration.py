"""
LLM integration for iMessage AI

Supports both local LLMs (Ollama) and cloud APIs (OpenAI, Anthropic) for RAG-based chat.
"""

import json
import requests
from typing import List, Dict, Optional, Tuple, Any, Generator
from datetime import datetime
from dataclasses import dataclass

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .chunker import MessageChunk


@dataclass
class ChatMessage:
    """Chat message for LLM conversation"""
    role: str  # 'system', 'user', 'assistant'
    content: str
    timestamp: Optional[datetime] = None


@dataclass
class RAGResponse:
    """Response from RAG query including sources"""
    answer: str
    sources: List[MessageChunk]
    model_used: str
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[int] = None


class OllamaLLM:
    """Local LLM integration via Ollama"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        temperature: float = 0.7,
        timeout: int = 60
    ):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama server URL
            model: Model name (e.g., 'llama3.2', 'mistral', 'codellama')
            temperature: Response creativity (0.0-1.0)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        
    def is_available(self) -> bool:
        """Check if Ollama server is running and model is available"""
        try:
            # Check if server is up
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False
            
            # Check if our model is available
            models = response.json().get('models', [])
            model_names = [m['name'].split(':')[0] for m in models]  # Remove tag
            
            return self.model in model_names or any(self.model in name for name in model_names)
            
        except Exception:
            return False
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            return response.json().get('models', [])
        except Exception as e:
            print(f"Failed to list models: {e}")
            return []
    
    def pull_model(self, model: Optional[str] = None) -> bool:
        """Pull/download a model"""
        model_to_pull = model or self.model
        
        try:
            print(f"🔄 Pulling model {model_to_pull}...")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_to_pull},
                timeout=300  # 5 minutes for download
            )
            
            if response.status_code == 200:
                print(f"✅ Model {model_to_pull} pulled successfully")
                return True
            else:
                print(f"❌ Failed to pull model: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error pulling model: {e}")
            return False
    
    def generate(
        self, 
        messages: List[ChatMessage], 
        stream: bool = False,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate response from conversation history"""
        
        # Format messages for Ollama
        prompt = self._format_messages(messages, system_prompt)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self.temperature
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            if stream:
                return self._handle_stream(response)
            else:
                result = response.json()
                return result.get('response', '')
                
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {e}")
    
    def _format_messages(self, messages: List[ChatMessage], system_prompt: Optional[str] = None) -> str:
        """Convert messages to a single prompt for Ollama"""
        prompt_parts = []
        
        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}\n")
        
        for msg in messages:
            if msg.role == 'system':
                prompt_parts.append(f"System: {msg.content}\n")
            elif msg.role == 'user':
                prompt_parts.append(f"User: {msg.content}\n")
            elif msg.role == 'assistant':
                prompt_parts.append(f"Assistant: {msg.content}\n")
        
        # Add final assistant prompt
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)
    
    def _handle_stream(self, response: requests.Response) -> str:
        """Handle streaming response from Ollama"""
        full_response = ""
        
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if 'response' in data:
                        full_response += data['response']
                except json.JSONDecodeError:
                    continue
        
        return full_response


class OpenAILLM:
    """OpenAI API integration"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 4000
    ):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not available. Install with: pip install openai")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def is_available(self) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            # Test with a simple completion
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception:
            return False
    
    def generate(self, messages: List[ChatMessage], system_prompt: Optional[str] = None) -> str:
        """Generate response using OpenAI"""
        
        # Format messages
        api_messages = []
        
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        
        for msg in messages:
            api_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {e}")


class AnthropicLLM:
    """Anthropic Claude API integration"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-haiku-20240307",
        temperature: float = 0.7,
        max_tokens: int = 4000
    ):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package not available. Install with: pip install anthropic")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def is_available(self) -> bool:
        """Check if Anthropic API is accessible"""
        try:
            # Test with a simple completion
            self.client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception:
            return False
    
    def generate(self, messages: List[ChatMessage], system_prompt: Optional[str] = None) -> str:
        """Generate response using Anthropic Claude"""
        
        # Format messages (Claude has different format)
        api_messages = []
        
        for msg in messages:
            if msg.role != 'system':  # System prompts handled separately in Claude
                api_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt or "You are a helpful AI assistant.",
                messages=api_messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            raise RuntimeError(f"Anthropic generation failed: {e}")


class RAGSystem:
    """RAG (Retrieval-Augmented Generation) system for iMessage AI"""
    
    def __init__(
        self,
        llm: Any,  # OllamaLLM, OpenAILLM, or AnthropicLLM
        indexer: Any,  # iMessageIndexer from pipeline.py
        max_context_chunks: int = 5,
        max_context_length: int = 4000
    ):
        """
        Initialize RAG system
        
        Args:
            llm: Language model instance
            indexer: iMessage indexer with vector store
            max_context_chunks: Maximum chunks to include in context
            max_context_length: Maximum characters of context
        """
        self.llm = llm
        self.indexer = indexer
        self.max_context_chunks = max_context_chunks
        self.max_context_length = max_context_length
        
        # Chat history for conversation
        self.chat_history: List[ChatMessage] = []
    
    def ask(
        self, 
        question: str, 
        include_chat_history: bool = True,
        filters: Optional[Dict] = None
    ) -> RAGResponse:
        """
        Ask a question about your iMessage history
        
        Args:
            question: User's question
            include_chat_history: Whether to include previous conversation
            filters: Optional metadata filters for search
            
        Returns:
            RAG response with answer and sources
        """
        start_time = datetime.now()
        
        # 1. Retrieve relevant chunks
        relevant_chunks = self.indexer.search(
            query=question,
            top_k=self.max_context_chunks,
            where_filters=filters
        )
        
        # Extract chunks and scores
        chunks = [chunk for chunk, score in relevant_chunks]
        
        # 2. Build context from chunks
        context = self._build_context(chunks)
        
        # 3. Create system prompt
        system_prompt = self._create_system_prompt(context)
        
        # 4. Prepare messages
        messages = []
        
        # Add recent chat history if requested
        if include_chat_history and self.chat_history:
            messages.extend(self.chat_history[-10:])  # Last 10 messages
        
        # Add current question
        messages.append(ChatMessage(role="user", content=question))
        
        # 5. Generate response
        try:
            answer = self.llm.generate(messages, system_prompt=system_prompt)
            
            # 6. Update chat history
            self.chat_history.append(ChatMessage(role="user", content=question))
            self.chat_history.append(ChatMessage(role="assistant", content=answer))
            
            # Trim history if too long
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return RAGResponse(
                answer=answer,
                sources=chunks,
                model_used=getattr(self.llm, 'model', 'unknown'),
                processing_time_ms=int(processing_time)
            )
            
        except Exception as e:
            raise RuntimeError(f"RAG query failed: {e}")
    
    def _build_context(self, chunks: List[MessageChunk]) -> str:
        """Build context string from relevant message chunks"""
        context_parts = []
        total_length = 0
        
        for i, chunk in enumerate(chunks):
            # Format chunk with metadata
            participants = ", ".join(chunk.participants[:3])
            if len(chunk.participants) > 3:
                participants += f" (and {len(chunk.participants) - 3} others)"
            
            chunk_header = f"--- Conversation {i+1} ---\n"
            chunk_header += f"Participants: {participants}\n"
            chunk_header += f"Time: {chunk.start_time.strftime('%Y-%m-%d %H:%M')} - {chunk.end_time.strftime('%H:%M')}\n"
            chunk_header += f"Messages: {len(chunk.messages)}\n\n"
            
            chunk_content = chunk.text_content
            
            # Check length limit
            chunk_text = chunk_header + chunk_content + "\n\n"
            if total_length + len(chunk_text) > self.max_context_length:
                break
            
            context_parts.append(chunk_text)
            total_length += len(chunk_text)
        
        return "".join(context_parts)
    
    def _create_system_prompt(self, context: str) -> str:
        """Create system prompt with conversation context"""
        return f"""You are an AI assistant helping someone understand their iMessage conversation history. 

You have access to relevant conversations from their chat history. Use this context to answer their questions accurately and helpfully.

CONVERSATION CONTEXT:
{context}

INSTRUCTIONS:
- Answer questions based on the conversation context provided
- Be conversational and helpful
- If you can't find relevant information in the context, say so
- Reference specific conversations when relevant (e.g., "In your chat with Alice...")
- Maintain privacy and be respectful about personal conversations
- If asked about recent conversations, note the dates from the context

Remember: This is the user's own private message history. Help them understand and navigate their conversations."""
    
    def clear_history(self) -> None:
        """Clear chat history"""
        self.chat_history = []
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get statistics about the current conversation"""
        return {
            'total_messages': len(self.chat_history),
            'user_messages': sum(1 for m in self.chat_history if m.role == 'user'),
            'assistant_messages': sum(1 for m in self.chat_history if m.role == 'assistant'),
            'last_interaction': self.chat_history[-1].timestamp if self.chat_history else None
        }


class LLMManager:
    """Manager for different LLM backends"""
    
    @staticmethod
    def create_llm(
        llm_type: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Create LLM instance based on type
        
        Args:
            llm_type: 'ollama', 'openai', or 'anthropic'
            model: Model name (uses defaults if None)
            api_key: API key for cloud providers
            **kwargs: Additional arguments for LLM
        """
        
        if llm_type == 'ollama':
            default_model = model or 'llama3.2'
            return OllamaLLM(model=default_model, **kwargs)
        
        elif llm_type == 'openai':
            if not api_key:
                raise ValueError("OpenAI API key required")
            default_model = model or 'gpt-4o-mini'
            return OpenAILLM(api_key=api_key, model=default_model, **kwargs)
        
        elif llm_type == 'anthropic':
            if not api_key:
                raise ValueError("Anthropic API key required")
            default_model = model or 'claude-3-haiku-20240307'
            return AnthropicLLM(api_key=api_key, model=default_model, **kwargs)
        
        else:
            raise ValueError(f"Unsupported LLM type: {llm_type}")
    
    @staticmethod
    def get_available_llms() -> Dict[str, bool]:
        """Check which LLM backends are available"""
        availability = {}
        
        # Check Ollama
        try:
            ollama = OllamaLLM()
            availability['ollama'] = ollama.is_available()
        except Exception:
            availability['ollama'] = False
        
        # Check OpenAI (requires API key to test fully)
        availability['openai'] = OPENAI_AVAILABLE
        
        # Check Anthropic (requires API key to test fully)
        availability['anthropic'] = ANTHROPIC_AVAILABLE
        
        return availability
"""
Embedding generation for message chunks

Generates vector embeddings for semantic search and retrieval.
Supports both local models (sentence-transformers) and cloud APIs (OpenAI).
"""

import hashlib
import json
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
import pickle
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .chunker import MessageChunk


@dataclass
class EmbeddingResult:
    """Result of embedding generation"""
    chunk_id: str
    embedding: List[float]
    model_name: str
    embedding_dim: int
    text_hash: str  # Hash of input text for caching


class EmbeddingGenerator:
    """Generates embeddings for message chunks"""
    
    def __init__(
        self, 
        model_type: str = 'local',
        model_name: Optional[str] = None,
        cache_dir: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize embedding generator
        
        Args:
            model_type: 'local' (sentence-transformers) or 'openai'
            model_name: Specific model name or None for defaults
            cache_dir: Directory to cache embeddings
            openai_api_key: OpenAI API key if using OpenAI embeddings
        """
        self.model_type = model_type
        self.cache_dir = Path(cache_dir) if cache_dir else Path('.embeddings_cache')
        self.cache_dir.mkdir(exist_ok=True)
        
        if model_type == 'local':
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
            
            # Default local model - good balance of speed and quality
            self.model_name = model_name or 'all-MiniLM-L6-v2'
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            
        elif model_type == 'openai':
            if not OPENAI_AVAILABLE:
                raise ImportError("openai not installed. Run: pip install openai")
            
            self.model_name = model_name or 'text-embedding-ada-002'
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
            self.embedding_dim = 1536  # Ada-002 dimension
            
        else:
            raise ValueError(f"Unsupported model_type: {model_type}")
    
    def embed_chunks(self, chunks: List[MessageChunk], use_cache: bool = True) -> List[EmbeddingResult]:
        """Generate embeddings for a list of message chunks"""
        results = []
        texts_to_embed = []
        cache_misses = []
        
        # Check cache first if enabled
        if use_cache:
            for i, chunk in enumerate(chunks):
                cached_result = self._load_from_cache(chunk.text_content)
                if cached_result:
                    results.append(cached_result)
                else:
                    cache_misses.append((i, chunk))
                    texts_to_embed.append(chunk.text_content)
        else:
            cache_misses = [(i, chunk) for i, chunk in enumerate(chunks)]
            texts_to_embed = [chunk.text_content for chunk in chunks]
        
        # Generate embeddings for cache misses
        if texts_to_embed:
            if self.model_type == 'local':
                embeddings = self._embed_local(texts_to_embed)
            elif self.model_type == 'openai':
                embeddings = self._embed_openai(texts_to_embed)
            
            # Create results and cache them
            for (original_idx, chunk), embedding in zip(cache_misses, embeddings):
                result = EmbeddingResult(
                    chunk_id=chunk.id,
                    embedding=embedding,
                    model_name=self.model_name,
                    embedding_dim=len(embedding),
                    text_hash=self._text_hash(chunk.text_content)
                )
                
                if use_cache:
                    self._save_to_cache(chunk.text_content, result)
                
                results.append(result)
        
        # Sort results back to original order
        results.sort(key=lambda r: next(i for i, chunk in enumerate(chunks) if chunk.id == r.chunk_id))
        
        return results
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text string"""
        if self.model_type == 'local':
            return self._embed_local([text])[0]
        elif self.model_type == 'openai':
            return self._embed_openai([text])[0]
    
    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local sentence-transformers model"""
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
    
    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        response = self.openai_client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        
        return [embedding.embedding for embedding in response.data]
    
    def _text_hash(self, text: str) -> str:
        """Generate hash of text for caching"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _cache_key(self, text_hash: str) -> str:
        """Generate cache file path"""
        return f"{self.model_type}_{self.model_name}_{text_hash}"
    
    def _save_to_cache(self, text: str, result: EmbeddingResult) -> None:
        """Save embedding result to cache"""
        try:
            cache_file = self.cache_dir / f"{self._cache_key(result.text_hash)}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
        except Exception as e:
            # Don't fail if caching fails
            print(f"Warning: Failed to save embedding to cache: {e}")
    
    def _load_from_cache(self, text: str) -> Optional[EmbeddingResult]:
        """Load embedding result from cache"""
        try:
            text_hash = self._text_hash(text)
            cache_file = self.cache_dir / f"{self._cache_key(text_hash)}.pkl"
            
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    result = pickle.load(f)
                    # Verify hash matches
                    if result.text_hash == text_hash:
                        return result
        except Exception as e:
            # Don't fail if cache loading fails
            print(f"Warning: Failed to load embedding from cache: {e}")
        
        return None
    
    def clear_cache(self) -> None:
        """Clear embedding cache"""
        try:
            for cache_file in self.cache_dir.glob(f"{self.model_type}_{self.model_name}_*.pkl"):
                cache_file.unlink()
        except Exception as e:
            print(f"Warning: Failed to clear cache: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get statistics about the embedding cache"""
        try:
            cache_files = list(self.cache_dir.glob(f"{self.model_type}_{self.model_name}_*.pkl"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'cache_dir': str(self.cache_dir),
                'cached_embeddings': len(cache_files),
                'total_cache_size_mb': total_size / (1024 * 1024),
                'model_type': self.model_type,
                'model_name': self.model_name
            }
        except Exception:
            return {'error': 'Failed to get cache stats'}


class EmbeddingIndex:
    """Simple in-memory index for embeddings (before ChromaDB integration)"""
    
    def __init__(self, embedding_dim: int):
        self.embedding_dim = embedding_dim
        self.embeddings: List[List[float]] = []
        self.metadata: List[Dict] = []
        self.chunk_ids: List[str] = []
    
    def add_embeddings(self, results: List[EmbeddingResult], chunks: List[MessageChunk]) -> None:
        """Add embeddings to the index"""
        for result, chunk in zip(results, chunks):
            if len(result.embedding) != self.embedding_dim:
                raise ValueError(f"Embedding dimension mismatch: expected {self.embedding_dim}, got {len(result.embedding)}")
            
            self.embeddings.append(result.embedding)
            self.chunk_ids.append(result.chunk_id)
            
            # Store chunk metadata for retrieval
            metadata = {
                'chunk_id': chunk.id,
                'chat_id': chunk.chat_id,
                'start_time': chunk.start_time.isoformat(),
                'end_time': chunk.end_time.isoformat(),
                'participants': chunk.participants,
                'chunk_type': chunk.chunk_type,
                'message_count': len(chunk.messages),
                'text_preview': chunk.text_content[:200] + '...' if len(chunk.text_content) > 200 else chunk.text_content
            }
            metadata.update(chunk.metadata)
            self.metadata.append(metadata)
    
    def search_similar(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[Dict, float]]:
        """Search for similar embeddings (simple cosine similarity)"""
        if len(query_embedding) != self.embedding_dim:
            raise ValueError(f"Query embedding dimension mismatch: expected {self.embedding_dim}, got {len(query_embedding)}")
        
        scores = []
        for i, emb in enumerate(self.embeddings):
            # Simple cosine similarity
            dot_product = sum(a * b for a, b in zip(query_embedding, emb))
            magnitude_a = sum(a * a for a in query_embedding) ** 0.5
            magnitude_b = sum(b * b for b in emb) ** 0.5
            
            if magnitude_a > 0 and magnitude_b > 0:
                similarity = dot_product / (magnitude_a * magnitude_b)
            else:
                similarity = 0.0
            
            scores.append((self.metadata[i], similarity))
        
        # Sort by similarity (highest first)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_k]
    
    def save(self, filepath: str) -> None:
        """Save index to file"""
        index_data = {
            'embedding_dim': self.embedding_dim,
            'embeddings': self.embeddings,
            'metadata': self.metadata,
            'chunk_ids': self.chunk_ids
        }
        
        with open(filepath, 'w') as f:
            json.dump(index_data, f)
    
    @classmethod
    def load(cls, filepath: str) -> 'EmbeddingIndex':
        """Load index from file"""
        with open(filepath, 'r') as f:
            index_data = json.load(f)
        
        index = cls(index_data['embedding_dim'])
        index.embeddings = index_data['embeddings']
        index.metadata = index_data['metadata']
        index.chunk_ids = index_data['chunk_ids']
        
        return index
    
    def stats(self) -> Dict:
        """Get index statistics"""
        return {
            'total_embeddings': len(self.embeddings),
            'embedding_dim': self.embedding_dim,
            'unique_chats': len(set(meta['chat_id'] for meta in self.metadata)),
            'chunk_types': {
                chunk_type: sum(1 for meta in self.metadata if meta['chunk_type'] == chunk_type)
                for chunk_type in set(meta['chunk_type'] for meta in self.metadata)
            }
        }
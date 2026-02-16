"""
ChromaDB vector store integration for iMessage AI

Persistent vector storage with efficient similarity search and metadata filtering.
"""

import os
import json
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from .embeddings import EmbeddingResult
from .chunker import MessageChunk


class ChromaVectorStore:
    """ChromaDB-based vector store for message chunks"""
    
    def __init__(
        self,
        persist_directory: str = ".chromadb",
        collection_name: str = "imessage_chunks",
        embedding_function: Optional[Any] = None
    ):
        """
        Initialize ChromaDB vector store
        
        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection for message chunks
            embedding_function: ChromaDB embedding function (optional, we provide embeddings)
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb not installed. Run: pip install chromadb")
        
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        self.collection_name = collection_name
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False  # Disable telemetry for privacy
            )
        )
        
        # Get or create collection
        # We don't provide an embedding function since we generate embeddings ourselves
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"📂 Loaded existing collection '{collection_name}' with {self.collection.count()} items")
        except ValueError:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "iMessage conversation chunks for AI search"}
            )
            print(f"🆕 Created new collection '{collection_name}'")
    
    def add_chunks(
        self, 
        embedding_results: List[EmbeddingResult], 
        chunks: List[MessageChunk]
    ) -> None:
        """Add message chunks with embeddings to the vector store"""
        if len(embedding_results) != len(chunks):
            raise ValueError("Number of embedding results must match number of chunks")
        
        # Prepare data for ChromaDB
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for result, chunk in zip(embedding_results, chunks):
            ids.append(result.chunk_id)
            embeddings.append(result.embedding)
            documents.append(chunk.text_content)
            
            # Prepare metadata (ChromaDB requires JSON-serializable values)
            metadata = {
                'chat_id': chunk.chat_id,
                'start_time': chunk.start_time.isoformat(),
                'end_time': chunk.end_time.isoformat(),
                'participants': json.dumps(chunk.participants),  # Serialize list
                'chunk_type': chunk.chunk_type,
                'message_count': len(chunk.messages),
                'embedding_model': result.model_name,
                'embedding_dim': result.embedding_dim,
                'created_at': datetime.now().isoformat()
            }
            
            # Add chunk metadata (flatten nested dicts)
            for key, value in chunk.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    metadata[f'chunk_{key}'] = value
                elif isinstance(value, (list, dict)):
                    metadata[f'chunk_{key}'] = json.dumps(value)
            
            metadatas.append(metadata)
        
        # Add to ChromaDB collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✅ Added {len(chunks)} chunks to vector store")
    
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        where_filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Dict, float]]:
        """
        Search for similar chunks using vector similarity
        
        Args:
            query_embedding: Query vector embedding
            top_k: Number of results to return
            where_filters: Optional metadata filters (e.g., {'chat_id': 123})
            
        Returns:
            List of (metadata, similarity_score) tuples
        """
        # ChromaDB query
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filters,
            include=['metadatas', 'documents', 'distances']
        )
        
        # Process results
        search_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i].copy()
                distance = results['distances'][0][i]
                
                # Convert distance to similarity score (ChromaDB uses L2 distance)
                # For normalized embeddings, similarity ≈ 1 - (distance²/4)
                similarity = max(0, 1 - (distance ** 2) / 4)
                
                # Parse JSON fields back to Python objects
                if 'participants' in metadata:
                    metadata['participants'] = json.loads(metadata['participants'])
                
                # Add document text
                metadata['document'] = results['documents'][0][i]
                metadata['chunk_id'] = results['ids'][0][i]
                
                search_results.append((metadata, similarity))
        
        return search_results
    
    def search_by_text(
        self, 
        query_text: str, 
        top_k: int = 5,
        where_filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Dict, float]]:
        """
        Search using text query (requires an embedding function)
        
        Note: This method requires ChromaDB to have an embedding function.
        Use search() with pre-computed embeddings instead.
        """
        raise NotImplementedError(
            "Text search requires embedding function. Use search() with query_embedding instead."
        )
    
    def get_by_ids(self, chunk_ids: List[str]) -> List[Dict]:
        """Get chunks by their IDs"""
        results = self.collection.get(
            ids=chunk_ids,
            include=['metadatas', 'documents']
        )
        
        chunks = []
        if results['ids']:
            for i, chunk_id in enumerate(results['ids']):
                metadata = results['metadatas'][i].copy()
                
                # Parse JSON fields
                if 'participants' in metadata:
                    metadata['participants'] = json.loads(metadata['participants'])
                
                metadata['document'] = results['documents'][i]
                metadata['chunk_id'] = chunk_id
                
                chunks.append(metadata)
        
        return chunks
    
    def filter_by_metadata(
        self, 
        where_filters: Dict[str, Any], 
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Filter chunks by metadata criteria"""
        results = self.collection.get(
            where=where_filters,
            limit=limit,
            include=['metadatas', 'documents']
        )
        
        chunks = []
        if results['ids']:
            for i, chunk_id in enumerate(results['ids']):
                metadata = results['metadatas'][i].copy()
                
                # Parse JSON fields
                if 'participants' in metadata:
                    metadata['participants'] = json.loads(metadata['participants'])
                
                metadata['document'] = results['documents'][i]
                metadata['chunk_id'] = chunk_id
                
                chunks.append(metadata)
        
        return chunks
    
    def delete_chunks(self, chunk_ids: List[str]) -> None:
        """Delete chunks by IDs"""
        self.collection.delete(ids=chunk_ids)
        print(f"🗑️  Deleted {len(chunk_ids)} chunks")
    
    def clear_collection(self) -> None:
        """Clear all data from the collection"""
        # Delete and recreate collection
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "iMessage conversation chunks for AI search"}
        )
        print("🧹 Cleared vector store collection")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        count = self.collection.count()
        
        # Get sample of metadata to analyze
        sample_results = self.collection.get(
            limit=min(100, count),
            include=['metadatas']
        )
        
        stats = {
            'total_chunks': count,
            'collection_name': self.collection_name,
            'persist_directory': str(self.persist_directory)
        }
        
        if sample_results['metadatas']:
            # Analyze metadata
            chat_ids = set()
            chunk_types = {}
            models = set()
            
            for metadata in sample_results['metadatas']:
                chat_ids.add(metadata.get('chat_id'))
                
                chunk_type = metadata.get('chunk_type', 'unknown')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                
                models.add(metadata.get('embedding_model'))
            
            stats.update({
                'unique_chats_sample': len(chat_ids),
                'chunk_types_sample': chunk_types,
                'embedding_models': list(models)
            })
        
        return stats
    
    def backup_collection(self, backup_path: str) -> None:
        """Export collection data to JSON backup"""
        all_data = self.collection.get(include=['metadatas', 'documents', 'embeddings'])
        
        backup_data = {
            'collection_name': self.collection_name,
            'exported_at': datetime.now().isoformat(),
            'total_chunks': len(all_data['ids']),
            'data': {
                'ids': all_data['ids'],
                'documents': all_data['documents'],
                'metadatas': all_data['metadatas'],
                'embeddings': all_data['embeddings']
            }
        }
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        print(f"💾 Backed up {len(all_data['ids'])} chunks to {backup_path}")
    
    def restore_from_backup(self, backup_path: str) -> None:
        """Restore collection from JSON backup"""
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        # Clear existing collection
        self.clear_collection()
        
        # Restore data
        data = backup_data['data']
        if data['ids']:
            self.collection.add(
                ids=data['ids'],
                documents=data['documents'],
                metadatas=data['metadatas'],
                embeddings=data['embeddings']
            )
        
        print(f"📂 Restored {len(data['ids'])} chunks from {backup_path}")


class VectorStoreManager:
    """Manager for switching between different vector store implementations"""
    
    def __init__(self, store_type: str = 'chromadb', **kwargs):
        """
        Initialize vector store manager
        
        Args:
            store_type: 'chromadb' or 'memory' (fallback)
            **kwargs: Arguments passed to the vector store constructor
        """
        self.store_type = store_type
        
        if store_type == 'chromadb':
            if not CHROMADB_AVAILABLE:
                print("⚠️  ChromaDB not available, falling back to in-memory store")
                self.store_type = 'memory'
            else:
                self.store = ChromaVectorStore(**kwargs)
        
        if self.store_type == 'memory':
            # Import here to avoid circular import
            from .embeddings import EmbeddingIndex
            embedding_dim = kwargs.get('embedding_dim', 384)  # Default for MiniLM
            self.store = EmbeddingIndex(embedding_dim)
    
    def add_chunks(self, embedding_results: List[EmbeddingResult], chunks: List[MessageChunk]) -> None:
        """Add chunks to the vector store"""
        if self.store_type == 'chromadb':
            self.store.add_chunks(embedding_results, chunks)
        else:
            # Memory store
            self.store.add_embeddings(embedding_results, chunks)
    
    def search(self, query_embedding: List[float], top_k: int = 5, **kwargs) -> List[Tuple[Dict, float]]:
        """Search the vector store"""
        if self.store_type == 'chromadb':
            return self.store.search(query_embedding, top_k, kwargs.get('where_filters'))
        else:
            # Memory store returns different format, normalize it
            results = self.store.search_similar(query_embedding, top_k)
            return results  # Already in correct format
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        stats = {'store_type': self.store_type}
        stats.update(self.store.get_stats() if hasattr(self.store, 'get_stats') else self.store.stats())
        return stats
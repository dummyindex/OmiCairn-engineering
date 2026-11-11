"""
Fix Experience Vector Store Service using ChromaDB HTTP Client
Vector database of error-fix experiences (HTTP client version, supports concurrency)
"""
import os
import json
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from threading import Lock
from tool.error_normalizer import ErrorNormalizer
from log.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("fix_experience_vector_store")


class FixExperienceVectorStore:
    """ChromaDB HTTP Client-based RAG vector store for error fixes (supports concurrency)"""
    
    # Timestamp file path
    TIMESTAMP_FILE = os.path.join(os.environ.get("RAG_FLAGS_DIR", "/rag-flags"), "fix_experience_rag_last_sync_timestamp.json")
    
    def __init__(self, chroma_host: str = None, chroma_port: int = None):
        """
        Initialize ChromaDB HTTP client
        
        :param chroma_host: ChromaDB server host (default: from env or localhost)
        :param chroma_port: ChromaDB server port (default: from env or 8000)
        """
        # Get ChromaDB server configuration from environment variables or arguments
        if chroma_host is None:
            chroma_host = os.environ.get("CHROMA_HOST", "localhost")
        if chroma_port is None:
            chroma_port = int(os.environ.get("CHROMA_PORT", "8000"))
        
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        
        # Timestamp file lock (the HTTP client itself is thread-safe; only the timestamp file needs protection)
        self._timestamp_lock = Lock()
        
        logger.info(f"Initializing ChromaDB HTTP client connecting to {chroma_host}:{chroma_port}")
        
        try:
            # Initialize the ChromaDB HTTP client
            self.client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            
            # Test the connection
            self.client.heartbeat()
            logger.info(f"Successfully connected to ChromaDB server at {chroma_host}:{chroma_port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB server at {chroma_host}:{chroma_port}: {str(e)}")
            raise
        
        # Get or create the collection
        self.collection_name = "fix_experience"
        
        # Use the BAAI/bge-small-en-v1.5 embedding model
        # A strong general-purpose embedding model with vector dimension 384
        self.embedding_model_name = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        logger.info(f"Using embedding model: {self.embedding_model_name}")
        
        # Create the embedding function
        try:
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model_name
            )
            logger.info(f"Successfully initialized embedding function with model: {self.embedding_model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding function: {str(e)}")
            logger.warning("Falling back to default embedding function")
            self.embedding_function = None
        
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={
                    "description": "Error fixes and strategies from fix_description table",
                    "embedding_model": self.embedding_model_name,
                    "embedding_dimension": 384  # vector dimension of bge-small-en-v1.5
                }
            )
            logger.info(f"Created new collection: {self.collection_name} with embedding model: {self.embedding_model_name}")
    
    def get_last_sync_timestamp(self) -> datetime:
        """
        Get the last sync timestamp from file (Thread-Safe)
        
        :return: Last sync timestamp, defaults to 30 days ago if not found
        """
        with self._timestamp_lock:
            try:
                if os.path.exists(self.TIMESTAMP_FILE):
                    with open(self.TIMESTAMP_FILE, 'r') as f:
                        data = json.load(f)
                        timestamp_str = data.get('last_sync_timestamp')
                        if timestamp_str:
                            return datetime.fromisoformat(timestamp_str)
            except Exception as e:
                logger.error(f"Failed to read last sync timestamp: {str(e)}")
            
            # Default: 30 days ago
            return datetime.now() - timedelta(days=30)
    
    def save_last_sync_timestamp(self, timestamp: datetime):
        """
        Save the last sync timestamp to file (Thread-Safe)
        
        :param timestamp: Timestamp to save
        """
        with self._timestamp_lock:
            try:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(self.TIMESTAMP_FILE), exist_ok=True)
                
                # Use a temp file + atomic rename to avoid a half-written file on crash
                temp_file = self.TIMESTAMP_FILE + '.tmp'
                with open(temp_file, 'w') as f:
                    json.dump({
                        'last_sync_timestamp': timestamp.isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }, f, indent=2)
                
                # Atomic operation: rename
                os.replace(temp_file, self.TIMESTAMP_FILE)
                
                logger.info(f"Saved last sync timestamp: {timestamp.isoformat()}")
            except Exception as e:
                logger.error(f"Failed to save last sync timestamp: {str(e)}")
    
    def batch_add_fix_descriptions(
        self, 
        fix_descriptions: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Batch add multiple fix descriptions to the vector store
        The HTTP client supports concurrency natively; the ChromaDB server handles concurrency control
        
        :param fix_descriptions: List of fix description dictionaries with keys:
                                id, computation_id, error_info, fix_strategy, created_at
        :return: Dict with success and failure counts
        """
        if not fix_descriptions:
            return {"success": 0, "failure": 0}
        
        # The HTTP client needs no extra lock; the server handles concurrency
        documents = []
        metadatas = []
        ids = []
        success_count = 0
        failure_count = 0
        
        for fix_desc in fix_descriptions:
            try:
                fix_id = fix_desc['id']
                computation_id = fix_desc['computation_id']
                error_info = fix_desc['error_info']
                fix_strategy = fix_desc['fix_strategy']
                created_at = fix_desc['created_at']
                
                # Normalize the error message
                normalized_error = ErrorNormalizer.normalize(error_info)
                error_type = ErrorNormalizer.extract_error_type(error_info)
                
                # Create searchable text
                searchable_text = ErrorNormalizer.create_searchable_text(error_info, fix_strategy)
                
                documents.append(searchable_text)
                metadatas.append({
                    "fix_id": fix_id,
                    "computation_id": computation_id,
                    "error_type": error_type,
                    "normalized_error": normalized_error,
                    "original_error": error_info[:1000],
                    "fix_strategy": fix_strategy[:1000],
                    "created_at": created_at.isoformat() if isinstance(created_at, datetime) else str(created_at)
                })
                ids.append(f"fix_{fix_id}")
                
            except Exception as e:
                logger.error(f"Failed to prepare fix description {fix_desc.get('id', 'unknown')}: {str(e)}")
                failure_count += 1
        
        # Batch add (with upsert semantics)
        if documents:
            try:
                # Check for existing IDs
                existing_ids = set()
                try:
                    existing = self.collection.get(ids=ids)
                    if existing and existing['ids']:
                        existing_ids = set(existing['ids'])
                except Exception:
                    pass
                
                # Separate inserts from updates
                new_docs, new_metas, new_ids = [], [], []
                update_docs, update_metas, update_ids = [], [], []
                
                for doc, meta, doc_id in zip(documents, metadatas, ids):
                    if doc_id in existing_ids:
                        update_docs.append(doc)
                        update_metas.append(meta)
                        update_ids.append(doc_id)
                    else:
                        new_docs.append(doc)
                        new_metas.append(meta)
                        new_ids.append(doc_id)
                
                # Update existing entries
                if update_docs:
                    self.collection.update(
                        documents=update_docs,
                        metadatas=update_metas,
                        ids=update_ids
                    )
                    logger.info(f"Updated {len(update_docs)} existing fix descriptions")
                
                # Add new entries
                if new_docs:
                    self.collection.add(
                        documents=new_docs,
                        metadatas=new_metas,
                        ids=new_ids
                    )
                    logger.info(f"Added {len(new_docs)} new fix descriptions")
                
                success_count = len(documents)
                logger.info(f"Successfully processed {success_count} fix descriptions to vector store")
            except Exception as e:
                logger.error(f"Failed to batch add fix descriptions: {str(e)}")
                failure_count += len(documents)
        
        return {"success": success_count, "failure": failure_count}
    
    def search_similar_fixes(
        self, 
        error_info: str, 
        top_k: int = 5,
        error_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar error fixes
        The HTTP client supports concurrent queries natively
        
        :param error_info: Error information to search for
        :param top_k: Number of top results to return
        :param error_type_filter: Optional error type filter
        :return: List of similar fix descriptions with metadata and similarity scores
        """
        try:
            # Normalize the query error message
            normalized_error = ErrorNormalizer.normalize(error_info)
            error_type = ErrorNormalizer.extract_error_type(error_info)
            
            # Create the query text
            query_text = f"Error Type: {error_type}\n\nNormalized Error: {normalized_error}"
            
            # Build filter conditions
            where_filter = None
            if error_type_filter:
                where_filter = {"error_type": error_type_filter}
            
            # Run the search
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=where_filter
            )
            
            # Format the results
            similar_fixes = []
            if results and results['metadatas'] and len(results['metadatas']) > 0:
                metadatas = results['metadatas'][0]
                distances = results['distances'][0] if 'distances' in results else [0] * len(metadatas)
                
                for metadata, distance in zip(metadatas, distances):
                    similar_fixes.append({
                        "fix_id": metadata.get("fix_id"),
                        "computation_id": metadata.get("computation_id"),
                        "error_type": metadata.get("error_type"),
                        "normalized_error": metadata.get("normalized_error"),
                        "original_error": metadata.get("original_error"),
                        "fix_strategy": metadata.get("fix_strategy"),
                        "created_at": metadata.get("created_at"),
                        "similarity_score": 1 - distance
                    })
            
            logger.info(f"Found {len(similar_fixes)} similar fixes for error type: {error_type}")
            return similar_fixes
            
        except Exception as e:
            logger.error(f"Failed to search similar fixes: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection
        
        :return: Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            stats = {
                "collection_name": self.collection_name,
                "total_documents": count,
                "status": "healthy",
                "server": f"{self.chroma_host}:{self.chroma_port}",
                "embedding_model": self.embedding_model_name,
                "embedding_dimension": 384  # vector dimension of bge-small-en-v1.5
            }
            
            # Try to fetch collection metadata
            try:
                collection_metadata = self.collection.metadata
                if collection_metadata:
                    stats["collection_metadata"] = collection_metadata
            except Exception:
                pass
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {
                "collection_name": self.collection_name,
                "total_documents": 0,
                "status": "error",
                "error": str(e),
                "server": f"{self.chroma_host}:{self.chroma_port}",
                "embedding_model": self.embedding_model_name
            }


# Thread-safe singleton implementation
_fix_experience_vector_store_instance = None
_instance_lock = Lock()


def get_fix_experience_vector_store() -> FixExperienceVectorStore:
    """Get or create Fix Experience vector store singleton instance (Thread-Safe)"""
    global _fix_experience_vector_store_instance
    
    if _fix_experience_vector_store_instance is None:
        with _instance_lock:
            if _fix_experience_vector_store_instance is None:
                _fix_experience_vector_store_instance = FixExperienceVectorStore()
    
    return _fix_experience_vector_store_instance

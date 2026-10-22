"""
Domain Knowledge Vector Store Service using ChromaDB HTTP Client
Domain-knowledge vector database for biological analysis computations (HTTP client version, supports concurrency)
"""
import os
import json
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from threading import Lock
from log.logger_factory import LoggerFactory
from sss.porter_factory import PorterFactory

logger = LoggerFactory.get_logger("domain_knowledge_vector_store")


class DomainKnowledgeVectorStore:
    """ChromaDB HTTP Client-based RAG vector store for domain knowledge (supports concurrency)"""
    
    # Timestamp file path
    TIMESTAMP_FILE = os.path.join(os.environ.get("RAG_FLAGS_DIR", "/rag-flags"), "domain_knowledge_rag_last_sync_timestamp.json")
    
    # S3 configuration
    S3_PREFIX = "domain-knowledge/"
    
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
        self.collection_name = "domain_knowledge"
        
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
                    "description": "Domain knowledge for biological analysis computations",
                    "embedding_model": self.embedding_model_name,
                    "embedding_dimension": 384  # vector dimension of bge-small-en-v1.5
                }
            )
            logger.info(f"Created new collection: {self.collection_name} with embedding model: {self.embedding_model_name}")
    
    def get_last_sync_timestamp(self) -> datetime:
        """
        Get the last sync timestamp from file (Thread-Safe)
        
        :return: Last sync timestamp, defaults to epoch (1970-01-01) if not found
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
            
            # Default to the epoch so the first sync fetches all files
            return datetime(1970, 1, 1)
    
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

    def fetch_s3_files_with_metadata(self, last_sync_time: datetime) -> List[Dict[str, Any]]:
        """
        Fetch all domain knowledge files and their metadata from S3
        
        :param last_sync_time: last sync time; only files modified after this time are fetched
        :return: list of files, each element containing file content and metadata
        """
        try:
            porter = PorterFactory.create_porter()
            porter.set_operation_target(self.S3_PREFIX)
            
            # List all files
            file_list = porter.list_files(recursive=True)
            logger.info(f"Found {len(file_list)} files in S3 prefix: {self.S3_PREFIX}")
            
            files_with_metadata = []
            
            for object_key in file_list:
                # Skip directories (keys ending with /)
                if object_key.endswith('/'):
                    continue
                
                try:
                    # Get file info (including last-modified time)
                    file_info = porter.get_head(object_key)
                    last_modified = file_info.get('LastModified')
                    
                    # Convert the datetime object returned by boto3 into a comparable format
                    if last_modified:
                        # boto3 returns datetime objects, which can be compared directly
                        if last_modified.replace(tzinfo=None) < last_sync_time:
                            logger.debug(f"Skipping {object_key} (not modified since last sync)")
                            continue
                    
                    # Read file content
                    porter.set_operation_target(object_key)
                    content = porter.fetch_file_text()
                    
                    if content:
                        try:
                            # Parse JSON content
                            data = json.loads(content)
                            
                            # Extract the name and description fields
                            name = data.get('name', '')
                            description = data.get('description', '')
                            text = data.get('text', '')
                            
                            if name or description or text:
                                files_with_metadata.append({
                                    'object_key': object_key,
                                    'name': name,
                                    'description': description,
                                    'text': text,
                                    'last_modified': last_modified,
                                    'raw_data': data
                                })
                                logger.debug(f"Loaded file: {object_key}")
                            else:
                                logger.warning(f"File {object_key} missing required fields (name/description/text)")
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON from {object_key}: {str(e)}")
                    else:
                        logger.warning(f"Empty content for file: {object_key}")
                        
                except Exception as file_error:
                    logger.error(f"Failed to process file {object_key}: {str(file_error)}")
            
            logger.info(f"Successfully loaded {len(files_with_metadata)} valid files from S3")
            return files_with_metadata
            
        except Exception as e:
            logger.error(f"Failed to fetch files from S3: {str(e)}")
            return []

    def batch_add_domain_knowledge(
        self, 
        knowledge_items: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Batch add multiple domain knowledge items to the vector store
        The HTTP client supports concurrency natively; the ChromaDB server handles concurrency control
        
        :param knowledge_items: List of knowledge items with name, description, text fields
        :return: Dict with success and failure counts
        """
        if not knowledge_items:
            return {"success": 0, "failure": 0}
        
        documents = []
        metadatas = []
        ids = []
        success_count = 0
        failure_count = 0
        
        for item in knowledge_items:
            try:
                object_key = item.get('object_key', '')
                name = item.get('name', '')
                description = item.get('description', '')
                text = item.get('text', '')
                last_modified = item.get('last_modified')
                
                # Create searchable text (concatenate name and description)
                searchable_text = f"{name}\n------------\n{description}"
                
                # Limit text length (avoid exceeding the embedding model limit)
                if len(searchable_text) > 8000:
                    searchable_text = searchable_text[:8000] + "..."
                
                documents.append(searchable_text)
                
                # Store the full text field in metadata
                metadata = {
                    "object_key": object_key,
                    "name": name[:500] if name else "",
                    "description": description[:500] if description else "",
                    "text": text,  # store the full text field
                    "last_modified": last_modified.isoformat() if last_modified else datetime.now().isoformat()
                }
                metadatas.append(metadata)
                
                # Use the hash of object_key as ID (prefix removed for simplicity)
                doc_id = f"dk_{object_key.replace(self.S3_PREFIX, '').replace('/', '_').replace('.json', '')}"
                ids.append(doc_id)
                
            except Exception as e:
                logger.error(f"Failed to prepare knowledge item {item.get('object_key', 'unknown')}: {str(e)}")
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
                    logger.info(f"Updated {len(update_docs)} existing domain knowledge items")
                
                # Add new entries
                if new_docs:
                    self.collection.add(
                        documents=new_docs,
                        metadatas=new_metas,
                        ids=new_ids
                    )
                    logger.info(f"Added {len(new_docs)} new domain knowledge items")
                
                success_count = len(documents)
                logger.info(f"Successfully processed {success_count} domain knowledge items to vector store")
            except Exception as e:
                logger.error(f"Failed to batch add domain knowledge: {str(e)}")
                failure_count += len(documents)
        
        return {"success": success_count, "failure": failure_count}
    
    def search_similar_knowledge(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar domain knowledge
        The HTTP client supports concurrent queries natively
        
        :param query: Query text
        :param top_k: Number of top results to return
        :return: List of similar knowledge items with metadata and similarity scores
        """
        try:
            # Run the search
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # Format the results
            similar_items = []
            if results and results['metadatas'] and len(results['metadatas']) > 0:
                metadatas = results['metadatas'][0]
                distances = results['distances'][0] if 'distances' in results else [0] * len(metadatas)
                documents = results['documents'][0] if 'documents' in results else [''] * len(metadatas)
                
                for metadata, distance, document in zip(metadatas, distances, documents):
                    similar_items.append({
                        "object_key": metadata.get("object_key"),
                        "name": metadata.get("name"),
                        "description": metadata.get("description"),
                        "text": metadata.get("text"),  # return the full text field
                        "last_modified": metadata.get("last_modified"),
                        "similarity_score": 1 - distance,
                        "searchable_text": document  # text used for search (name + description)
                    })
            
            logger.info(f"Found {len(similar_items)} similar domain knowledge items")
            return similar_items
            
        except Exception as e:
            logger.error(f"Failed to search similar knowledge: {str(e)}")
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
_domain_knowledge_vector_store_instance = None
_instance_lock = Lock()


def get_domain_knowledge_vector_store() -> DomainKnowledgeVectorStore:
    """Get or create Domain Knowledge vector store singleton instance (Thread-Safe)"""
    global _domain_knowledge_vector_store_instance
    
    if _domain_knowledge_vector_store_instance is None:
        with _instance_lock:
            if _domain_knowledge_vector_store_instance is None:
                _domain_knowledge_vector_store_instance = DomainKnowledgeVectorStore()
    
    return _domain_knowledge_vector_store_instance

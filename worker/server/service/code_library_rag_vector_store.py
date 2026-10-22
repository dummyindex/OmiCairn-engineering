"""
Code Library Vector Store Service using ChromaDB HTTP Client
Vector database for the user code library (HTTP client version, supports concurrency)
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

logger = LoggerFactory.get_logger("code_library_vector_store")


class CodeLibraryVectorStore:
    """ChromaDB HTTP Client-based RAG vector store for code library (supports concurrency)"""
    
    # Timestamp file path
    TIMESTAMP_FILE = os.path.join(os.environ.get("RAG_FLAGS_DIR", "/rag-flags"), "code_library_rag_last_sync_timestamp.json")
    
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
        self.collection_name = "code_library"
        
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
                    "description": "User code library from function_block_version_v1 table",
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

    def get_code(self, version_id: int) -> str:
        """
        Get the code content of a code version
        
        :param version_id: version ID
        :return: code content string
        """
        try:
            porter = PorterFactory.create_porter()
            
            porter.set_operation_target(f"function-block-version/{version_id}")
            file_list = porter.list_files()
            if not file_list:
                logger.warning(f"No files found for function block version ID: {version_id}")
                return "No files found"
            
            code = "Code:\n"
            # Supported code file extensions
            code_extensions = ['py', 'js', 'ts', 'java', 'go', 'cpp', 'c', 'cs', 'rb', 
                             'php', 'rs', 'swift', 'kt', 'm', 'scala', 'sh', 'html', 'css', 'r']
            
            for object_key in file_list:
                suffix = object_key.split('.')[-1].lower()
                if suffix in code_extensions:
                    try:
                        porter.set_operation_target(object_key)
                        code += f"\n\n# File: {object_key}\n"
                        content_header = porter.fetch_file_text_range(0, 10000)
                        code += content_header
                        code += "\n"
                    except Exception as file_error:
                        logger.warning(f"Failed to fetch file {object_key}: {file_error}")
                        code += f"# Error reading file: {str(file_error)}\n"
            
            return code
        except Exception as e:
            logger.error(f"Failed to get code for version {version_id}: {e}")
            return f"Error fetching code: {str(e)}"
                

    def batch_add_code_versions(
        self, 
        code_versions: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Batch add multiple code versions to the vector store
        The HTTP client supports concurrency natively; the ChromaDB server handles concurrency control
        
        :param code_versions: List of code version dictionaries from function_block_version_v1
        :return: Dict with success and failure counts
        """
        if not code_versions:
            return {"success": 0, "failure": 0}
        
        # TODO: implement vectorization and storage logic for code versions
        # Code content, metadata, etc. should be handled here according to actual requirements
        
        documents = []
        metadatas = []
        ids = []
        success_count = 0
        failure_count = 0
        
        for version in code_versions:
            try:
                # TODO: extract fields according to the actual function_block_version_v1 table schema
                version_id = version.get('id')
                function_block_id = version.get('function_block_id')
                function_block_name = version.get('function_block_name', 'Unknown')
                code_content = self.get_code(version_id)
                description = version.get('description', '')
                created_time = version.get('created_time', '')

                # Create searchable text (combine code and description)
                searchable_text = f"Function Block: {function_block_name}\n\n"
                if description:
                    searchable_text += f"Description: {description}\n\n"
                searchable_text += f"Code:\n{code_content}"
                
                # Limit text length (avoid exceeding the embedding model limit)
                if len(searchable_text) > 8000:
                    searchable_text = searchable_text[:8000] + "..."
                
                documents.append(searchable_text)
                metadatas.append({
                    "version_id": version_id,
                    "function_block_id": function_block_id,
                    "function_block_name": function_block_name,
                    "description": description[:500] if description else "",
                    "code_preview": code_content[:500] if code_content else "",
                    "created_time": created_time.isoformat() if isinstance(created_time, datetime) else str(created_time)
                })
                ids.append(f"code_version_{version_id}")
                
            except Exception as e:
                logger.error(f"Failed to prepare code version {version.get('id', 'unknown')}: {str(e)}")
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
                    logger.info(f"Updated {len(update_docs)} existing code versions")
                
                # Add new entries
                if new_docs:
                    self.collection.add(
                        documents=new_docs,
                        metadatas=new_metas,
                        ids=new_ids
                    )
                    logger.info(f"Added {len(new_docs)} new code versions")
                
                success_count = len(documents)
                logger.info(f"Successfully processed {success_count} code versions to vector store")
            except Exception as e:
                logger.error(f"Failed to batch add code versions: {str(e)}")
                failure_count += len(documents)
        
        return {"success": success_count, "failure": failure_count}
    
    def search_similar_code(
        self, 
        query: str, 
        top_k: int = 5,
        function_block_name_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar code in the library
        The HTTP client supports concurrent queries natively
        
        :param query: Query text (code snippet or description)
        :param top_k: Number of top results to return
        :param function_block_name_filter: Optional function block name filter
        :return: List of similar code versions with metadata and similarity scores
        """
        try:
            # Build filter conditions
            where_filter = None
            if function_block_name_filter:
                where_filter = {"function_block_name": function_block_name_filter}
            
            # Run the search
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter
            )
            
            # Format the results
            similar_codes = []
            if results and results['metadatas'] and len(results['metadatas']) > 0:
                metadatas = results['metadatas'][0]
                distances = results['distances'][0] if 'distances' in results else [0] * len(metadatas)
                documents = results['documents'][0] if 'documents' in results else [''] * len(metadatas)
                
                for metadata, distance, document in zip(metadatas, distances, documents):
                    similar_codes.append({
                        "version_id": metadata.get("version_id"),
                        "function_block_id": metadata.get("function_block_id"),
                        "function_block_name": metadata.get("function_block_name"),
                        "description": metadata.get("description"),
                        "code_preview": metadata.get("code_preview"),
                        "created_time": metadata.get("created_time"),
                        "similarity_score": 1 - distance,
                        "full_text": document  # full searchable text
                    })
            
            logger.info(f"Found {len(similar_codes)} similar code versions")
            return similar_codes
            
        except Exception as e:
            logger.error(f"Failed to search similar code: {str(e)}")
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
_code_library_vector_store_instance = None
_instance_lock = Lock()


def get_code_library_vector_store() -> CodeLibraryVectorStore:
    """Get or create Code Library vector store singleton instance (Thread-Safe)"""
    global _code_library_vector_store_instance
    
    if _code_library_vector_store_instance is None:
        with _instance_lock:
            if _code_library_vector_store_instance is None:
                _code_library_vector_store_instance = CodeLibraryVectorStore()
    
    return _code_library_vector_store_instance

"""
ChromaDB configuration
Manages the ChromaDB HTTP server connection settings
"""
import os

class ChromaConfig:
    """ChromaDB server configuration"""
    
    # ChromaDB HTTP server host
    CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
    
    # ChromaDB HTTP server port
    CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))
    
    # Connection timeout (seconds)
    CHROMA_TIMEOUT = int(os.environ.get("CHROMA_TIMEOUT", "30"))
    
    # Number of retries
    CHROMA_MAX_RETRIES = int(os.environ.get("CHROMA_MAX_RETRIES", "3"))
    
    # Timestamp file path
    TIMESTAMP_FILE = os.environ.get(
        "RAG_TIMESTAMP_FILE",
        "/omicairn/data/rag_last_sync_timestamp.json"
    )
    
    @classmethod
    def get_server_url(cls) -> str:
        """Get the full server URL"""
        return f"http://{cls.CHROMA_HOST}:{cls.CHROMA_PORT}"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that the configuration is usable"""
        try:
            import requests
            url = f"{cls.get_server_url()}/api/v2/heartbeat"
            response = requests.get(url, timeout=cls.CHROMA_TIMEOUT)
            return response.status_code == 200
        except Exception:
            return False

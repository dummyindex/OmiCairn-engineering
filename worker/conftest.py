"""
Global pytest configuration for omicairn-worker testing.
Provides comprehensive mocking for database connections and external services.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the server directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'handle_dynamic_generation'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'handle_job_feedback'))  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'handle_visualizer'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

# Set test environment variables before any imports
os.environ.setdefault('MYSQL_IP', 'localhost')
os.environ.setdefault('MYSQL_PORT', '3306')
os.environ.setdefault('MYSQL_DATABASE', 'test_db')
os.environ.setdefault('MYSQL_USERNAME', 'test_user')
os.environ.setdefault('MYSQL_PASSWORD', 'test_pass')
os.environ.setdefault('GPT_WORKFLOW_SERVER_HOST', 'localhost')
os.environ.setdefault('GPT_WORKFLOW_SERVER_PORT', '5000')
os.environ.setdefault('MAIN_SERVER_HOST', 'localhost')
os.environ.setdefault('COMPUTATION_SERVER_HOST', 'localhost')
os.environ.setdefault('SYSTEM_AGENT_KEY', 'test_key')
os.environ.setdefault('NETWORK_PROXY_HOST', 'localhost')
os.environ.setdefault('NETWORK_PROXY_PORT', '8080')


@pytest.fixture(autouse=True)
def mock_database_globally():
    """
    Mock database connections globally for all tests.
    
    This fixture automatically runs for ALL tests to ensure complete database isolation.
    It prevents any real database connections and provides mock objects instead.
    """
    # Create mock module for psycopg2 if it doesn't exist
    if 'psycopg2' not in sys.modules:
        sys.modules['psycopg2'] = MagicMock()
    
    with patch('sqlalchemy.create_engine') as mock_create_engine, \
         patch('pymysql.connect') as mock_pymysql, \
         patch('mysql.connector.connect', create=True) as mock_mysql_connector, \
         patch('sqlite3.connect') as mock_sqlite3, \
         patch('sqlalchemy.orm.sessionmaker') as mock_sessionmaker, \
         patch('sqlalchemy.MetaData') as mock_metadata:
        
        # Mock SQLAlchemy engine and all its methods
        mock_engine = Mock()
        mock_engine.connect.return_value = Mock()
        mock_engine.dispose.return_value = None
        mock_engine.execute.return_value = Mock()
        mock_engine.pool = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Mock comprehensive session behavior
        mock_session = Mock()
        mock_session.commit.return_value = None
        mock_session.rollback.return_value = None
        mock_session.close.return_value = None
        mock_session.begin.return_value = Mock()
        mock_session.flush.return_value = None
        mock_session.merge.return_value = Mock()
        mock_session.add.return_value = None
        mock_session.delete.return_value = None
        mock_session.query.return_value = Mock()
        mock_session.execute.return_value = Mock()
        
        # Mock query builder chain
        mock_query = Mock()
        mock_query.filter.return_value = Mock()
        mock_query.filter_by.return_value = Mock()
        mock_query.first.return_value = None
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = Mock()
        mock_query.limit.return_value = Mock()
        mock_query.offset.return_value = Mock()
        mock_session.query.return_value = mock_query
        
        # Mock sessionmaker
        mock_session_factory = Mock(return_value=mock_session)
        mock_sessionmaker.return_value = mock_session_factory
        
        # Mock all database connection types
        mock_connection = Mock()
        mock_connection.cursor.return_value = Mock()
        mock_connection.commit.return_value = None
        mock_connection.rollback.return_value = None
        mock_connection.close.return_value = None
        
        mock_pymysql.return_value = mock_connection
        if mock_mysql_connector:
            mock_mysql_connector.return_value = mock_connection
        mock_sqlite3.return_value = mock_connection
        
        # Mock metadata operations
        mock_metadata_instance = Mock()
        mock_metadata_instance.create_all.return_value = None
        mock_metadata_instance.drop_all.return_value = None
        mock_metadata.return_value = mock_metadata_instance
        
        yield {
            'engine': mock_engine,
            'session': mock_session,
            'connection': mock_connection,
            'session_factory': mock_session_factory,
            'query': mock_query,
            'metadata': mock_metadata_instance
        }


@pytest.fixture(autouse=True) 
def enforce_test_environment():
    """
    Enforce test environment safety measures.
    
    This fixture runs automatically and verifies we're in a safe test environment.
    """
    # Ensure critical environment variables are set to test values
    critical_env_checks = {
        'MYSQL_DATABASE': 'test_db',
        'MYSQL_USERNAME': 'test_user', 
        'MYSQL_PASSWORD': 'test_pass'
    }
    
    for env_var, expected_value in critical_env_checks.items():
        actual_value = os.environ.get(env_var)
        if actual_value != expected_value:
            # Force set to test value if not already set correctly
            os.environ[env_var] = expected_value
    
    # Additional safety: ensure we're not in a production-like environment
    dangerous_values = ['production', 'prod', 'live', 'main', 'real']
    for env_var in ['MYSQL_DATABASE', 'MYSQL_USERNAME']:
        value = os.environ.get(env_var, '').lower()
        for dangerous in dangerous_values:
            if dangerous in value:
                raise RuntimeError(
                    f"SAFETY CHECK FAILED: {env_var}='{value}' contains production indicator '{dangerous}'. "
                    f"Tests must not run against production databases!"
                )
    
    yield
    
    # Post-test cleanup - ensure no database files were created
    import glob
    db_files = glob.glob('*.db') + glob.glob('*.sqlite') + glob.glob('*.sqlite3')
    test_created_files = [f for f in db_files if f.startswith('test_') and f.endswith(('.db', '.sqlite', '.sqlite3'))]
    
    # Clean up any test database files
    for test_file in test_created_files:
        try:
            os.remove(test_file)
        except OSError:
            pass  # File might already be gone


@pytest.fixture
def mock_requests():
    """Mock requests library for HTTP calls."""
    with patch('requests.post') as mock_post, \
         patch('requests.get') as mock_get:
        
        # Default successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test_response"}
        mock_response.text = '{"data": "test_response"}'
        
        mock_post.return_value = mock_response
        mock_get.return_value = mock_response
        
        yield {
            'post': mock_post,
            'get': mock_get,
            'response': mock_response
        }


@pytest.fixture
def mock_logger():
    """Mock logger to avoid log setup issues."""
    with patch('logger_factory.LoggerFactory.get_logger') as mock_logger_factory:
        mock_logger = Mock()
        mock_logger_factory.return_value = mock_logger
        yield mock_logger


@pytest.fixture
def sample_dynamic_generation_data():
    """Sample data for dynamic generation testing."""
    return {
        "dynamic_generation_id": "dg_123",
        "session_id": "session_123", 
        "user_id": "user_123",
        "node_id": "node_123",
        "analysis_id": "analysis_123",
        "user_request": "Create a data processing function",
        "history": [
            {
                "node": {
                    "id": "node1",
                    "name": "Input Node",
                    "createdTime": 1640995200000
                },
                "latestComputation": {
                    "id": "comp1",
                    "status": "completed"
                }
            }
        ]
    }


@pytest.fixture
def sample_llm_response():
    """Sample LLM response data."""
    return {
        "data": {
            "function_block": "import pandas as pd\ndef process_data(df):\n    return df.groupby('column').mean()",
            "code": 200,
            "message": "Success"
        }
    }
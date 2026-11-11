"""
pytest configuration for omicairn-backend server tests
Enhanced with comprehensive fixtures for unit and integration testing
"""
import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test environment setup
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("MYSQL_IP", "localhost")
os.environ.setdefault("MYSQL_PORT", "3306")
os.environ.setdefault("MYSQL_DB", "omicairn")
os.environ.setdefault("MYSQL_USER", "test")
os.environ.setdefault("MYSQL_PASSWORD", "test")


# ===== Application Fixtures =====

@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    from main import create_app
    app = create_app(False)
    app.config['TESTING'] = True
    return app


@pytest.fixture(scope='session')
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def app_context(app):
    """Create an application context."""
    with app.app_context():
        yield app


# ===== Database Mock Fixtures =====

@pytest.fixture
def mock_db_session():
    """Mock database session - for DAO tests"""
    session = MagicMock()
    # Mock query chain
    mock_query = MagicMock()
    session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.filter_by.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.all.return_value = []
    mock_query.first.return_value = None
    mock_query.count.return_value = 0

    # Mock commit/rollback/add/delete
    session.add.return_value = None
    session.delete.return_value = None
    session.commit.return_value = None
    session.rollback.return_value = None
    session.flush.return_value = None

    return session


@pytest.fixture(scope='function')
def mock_db():
    """Mock database operations - legacy compatibility"""
    with patch('server.db.config.get_db_connection') as mock_conn:
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_connection
        yield mock_cursor


# ===== Authentication Fixtures =====

@pytest.fixture(scope='function')
def mock_auth():
    """Mock authentication."""
    with patch('server.authority.guardian_factory.AuthorityGuardianFactory') as mock_factory:
        mock_guardian = Mock()
        mock_guardian.authenticate.return_value = True
        mock_guardian.get_user_id.return_value = 1
        mock_factory.create.return_value = mock_guardian
        yield mock_guardian


@pytest.fixture
def test_user():
    """Test user data - dict format"""
    return {
        'id': 1,
        'user_name': 'testuser',
        'email': 'test@example.com',
        'phone_number': '+1234567890',
        'password': 'testpass123',
        'password_hash': 'hashed_password_here'
    }


@pytest.fixture(scope='function')
def sample_user():
    """Create a sample User model instance for testing."""
    from server.model.user import User

    return User(
        id=1,
        user_name="test_user",
        phone_number="+1234567890",
        password="test_password",
        created_time=datetime.now(),
        disabled=False,
        email="test@example.com",
        extend1=None
    )


@pytest.fixture
def authenticated_client(client, test_user):
    """Authenticated test client"""
    # Mock JWT token generation
    token = "test_jwt_token_" + str(test_user['id'])
    client.environ_base = client.environ_base or {}
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {token}'
    return client


# ===== Model Fixtures =====

@pytest.fixture(scope='function')
def sample_analysis():
    """Create a sample Analysis model instance for testing."""
    from server.model.analysis import Analysis

    return Analysis(
        id=1,
        name="test_analysis",
        user_id=1,
        created_time=datetime.now(),
        description="Test analysis description",
        status="pending"
    )


@pytest.fixture
def test_analysis():
    """Test analysis data - dict format"""
    return {
        'id': 1,
        'name': 'Test Analysis',
        'description': 'Test analysis description',
        'user_id': 1,
        'status': 'pending',
        'created_time': datetime.now()
    }


@pytest.fixture
def test_pipeline_template():
    """Test pipeline template data"""
    return {
        'id': 1,
        'name': 'Test Template',
        'description': 'Test template description',
        'user_id': 1,
        'public': False,
        'created_time': datetime.now()
    }


# ===== External Service Mock Fixtures =====

@pytest.fixture(scope='function')
def mock_s3():
    """Mock S3-compatible storage operations."""
    with patch('boto3.client') as mock_boto:
        mock_s3_client = Mock()
        # Mock common S3 operations
        mock_s3_client.upload_file.return_value = None
        mock_s3_client.download_file.return_value = None
        mock_s3_client.delete_object.return_value = {'DeleteMarker': True}
        mock_s3_client.list_objects_v2.return_value = {'Contents': []}
        mock_boto.return_value = mock_s3_client
        yield mock_s3_client


@pytest.fixture(scope='function')
def mock_llm():
    """Mock LLM interface."""
    with patch('server.llm.llm_interface.LlmInterface') as mock_llm_class:
        mock_instance = Mock()
        mock_instance.chat.return_value = {
            'response': 'Mock LLM response',
            'tokens': 100,
            'cost': 0.001
        }
        mock_instance.stream_chat.return_value = iter(['Mock', ' streaming', ' response'])
        mock_llm_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_storage():
    """Mock object storage service (S3-compatible)"""
    with patch('server.sss.sss_factory.SSSFactory.create') as mock_create:
        mock_storage = MagicMock()
        mock_storage.upload.return_value = 'https://mock-storage.com/test-file.txt'
        mock_storage.download.return_value = b'test file content'
        mock_storage.delete.return_value = True
        mock_storage.generate_presigned_url.return_value = 'https://mock-storage.com/presigned-url'
        mock_create.return_value = mock_storage
        yield mock_storage


@pytest.fixture
def mock_scheduler():
    """Mock APScheduler task scheduler"""
    with patch('server.schedule.scheduler.APScheduler') as mock_scheduler:
        mock_instance = MagicMock()
        mock_instance.add_job.return_value = Mock(id='job_123')
        mock_instance.remove_job.return_value = None
        mock_instance.get_job.return_value = Mock(id='job_123')
        mock_scheduler.return_value = mock_instance
        yield mock_instance


# ===== Test Data Helper Functions =====

def create_mock_file(filename='test.txt', content=b'test content'):
    """Create a mock file object - for file upload tests"""
    from io import BytesIO
    return (BytesIO(content), filename)


def generate_test_jwt(user_data):
    """Generate a test JWT token"""
    return f"test_jwt_token_{user_data.get('id', 1)}"


# ===== Test Environment Setup =====

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables - applied automatically to all tests"""
    # Already set at module level, but can add per-test overrides here
    yield
    # Cleanup after tests if needed

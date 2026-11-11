"""
Test helper functions
Provides commonly used test utility functions
"""
from io import BytesIO
from typing import Any, Dict, Optional
from unittest.mock import MagicMock


# ===== API Response Assertion Helpers =====

def assert_api_success(response, status_code: int = 200, message: Optional[str] = None):
    """
    Assert that the API response is successful

    Args:
        response: Flask test client response
        status_code: Expected HTTP status code
        message: Optional expected message in response
    """
    assert response.status_code == status_code, \
        f"Expected status {status_code}, got {response.status_code}. Response: {response.data}"

    if hasattr(response, 'json'):
        json_data = response.json if callable(response.json) else response.get_json()
        if json_data:
            # Common success patterns
            if 'code' in json_data:
                assert json_data['code'] == 200, f"Expected code 200, got {json_data.get('code')}"

            if message and 'message' in json_data:
                assert message in json_data['message'], \
                    f"Expected message containing '{message}', got '{json_data.get('message')}'"


def assert_api_error(response, status_code: int, error_code: Optional[int] = None,
                     error_message: Optional[str] = None):
    """
    Assert that the API response is an error

    Args:
        response: Flask test client response
        status_code: Expected HTTP status code
        error_code: Optional expected error code in response body
        error_message: Optional expected error message substring
    """
    assert response.status_code == status_code, \
        f"Expected status {status_code}, got {response.status_code}"

    if hasattr(response, 'json'):
        json_data = response.json if callable(response.json) else response.get_json()
        if json_data:
            if error_code is not None and 'code' in json_data:
                assert json_data['code'] == error_code, \
                    f"Expected error code {error_code}, got {json_data.get('code')}"

            if error_message and 'message' in json_data:
                assert error_message in json_data['message'], \
                    f"Expected error message containing '{error_message}', got '{json_data.get('message')}'"


def assert_response_has_keys(response, required_keys: list):
    """
    Assert that the response contains the required keys

    Args:
        response: Flask test client response
        required_keys: List of required keys
    """
    json_data = response.json if callable(response.json) else response.get_json()
    assert json_data is not None, "Response has no JSON data"

    for key in required_keys:
        assert key in json_data, f"Response missing required key: {key}"


# ===== Mock File Helpers =====

def create_mock_file(filename: str = 'test.txt', content: bytes = b'test content'):
    """
    Create a mock file object for file upload tests

    Args:
        filename: File name
        content: File content as bytes

    Returns:
        Tuple of (BytesIO object, filename)
    """
    return (BytesIO(content), filename)


def create_mock_csv_file(filename: str = 'test.csv', rows: Optional[list] = None):
    """
    Create a mock CSV file

    Args:
        filename: CSV file name
        rows: List of row data, defaults to sample data

    Returns:
        Tuple of (BytesIO object, filename)
    """
    if rows is None:
        rows = [
            'col1,col2,col3',
            'val1,val2,val3',
            'val4,val5,val6'
        ]

    content = '\n'.join(rows).encode('utf-8')
    return (BytesIO(content), filename)


# ===== Database Mock Helpers =====

def setup_mock_query_result(mock_query: MagicMock, result: Any,
                            method: str = 'first'):
    """
    Set the return value of a mock query

    Args:
        mock_query: MagicMock query object
        result: Result to return
        method: Query method ('first', 'all', 'count', 'one')
    """
    mock_query.filter.return_value = mock_query
    mock_query.filter_by.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.offset.return_value = mock_query

    if method == 'first':
        mock_query.first.return_value = result
    elif method == 'all':
        mock_query.all.return_value = result
    elif method == 'count':
        mock_query.count.return_value = result
    elif method == 'one':
        mock_query.one.return_value = result


def assert_db_commit_called(mock_session: MagicMock, times: int = 1):
    """
    Assert that the database commit was called

    Args:
        mock_session: Mock database session
        times: Expected number of calls
    """
    assert mock_session.commit.call_count == times, \
        f"Expected {times} commit(s), got {mock_session.commit.call_count}"


def assert_db_rollback_called(mock_session: MagicMock):
    """Assert that the database rollback was called"""
    assert mock_session.rollback.called, "Expected rollback to be called"


def assert_db_add_called_with(mock_session: MagicMock, expected_type: type):
    """
    Assert that session.add was called with an object of a specific type

    Args:
        mock_session: Mock database session
        expected_type: Expected object type
    """
    assert mock_session.add.called, "Expected session.add to be called"
    call_args = mock_session.add.call_args
    if call_args:
        added_obj = call_args[0][0] if call_args[0] else None
        assert isinstance(added_obj, expected_type), \
            f"Expected {expected_type.__name__}, got {type(added_obj).__name__}"


# ===== DAO Test Helpers =====

def create_mock_dao_session():
    """
    Create a mock session for DAO tests
    Includes all commonly used database operation methods

    Returns:
        MagicMock session object
    """
    session = MagicMock()

    # Query chain
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

    # Session operations
    session.add.return_value = None
    session.delete.return_value = None
    session.commit.return_value = None
    session.rollback.return_value = None
    session.flush.return_value = None

    return session


# ===== Service Test Helpers =====

def create_mock_dao():
    """
    Create a mock DAO for Service tests

    Returns:
        MagicMock DAO object
    """
    dao = MagicMock()
    dao.insert.return_value = None
    dao.update.return_value = None
    dao.delete.return_value = None
    dao.query_by_id.return_value = None
    dao.query_all.return_value = []
    return dao


# ===== JWT/Auth Helpers =====

def generate_test_jwt(user_id: int = 1, **claims) -> str:
    """
    Generate a test JWT token

    Args:
        user_id: User ID to include in token
        **claims: Additional JWT claims

    Returns:
        Test JWT token string
    """
    return f"test_jwt_token_{user_id}"


def create_auth_headers(token: Optional[str] = None, user_id: int = 1) -> Dict[str, str]:
    """
    Create authentication request headers

    Args:
        token: JWT token, if None will generate test token
        user_id: User ID for token generation if token is None

    Returns:
        Dict with Authorization header
    """
    if token is None:
        token = generate_test_jwt(user_id)

    return {'Authorization': f'Bearer {token}'}


# ===== Test Data Validation =====

def assert_dict_contains(actual: dict, expected: dict, partial: bool = True):
    """
    Assert that the dict contains the expected key-value pairs

    Args:
        actual: Actual dictionary
        expected: Expected key-value pairs
        partial: If True, actual can have extra keys; if False, must match exactly
    """
    for key, value in expected.items():
        assert key in actual, f"Key '{key}' not found in actual dict"
        assert actual[key] == value, \
            f"Key '{key}': expected {value}, got {actual[key]}"

    if not partial:
        assert set(actual.keys()) == set(expected.keys()), \
            f"Key mismatch. Expected: {set(expected.keys())}, Got: {set(actual.keys())}"


# ===== Common Test Utilities =====

def assert_no_exception(func, *args, **kwargs):
    """
    Assert that the function runs without raising an exception

    Args:
        func: Function to call
        *args: Positional arguments
        **kwargs: Keyword arguments
    """
    try:
        func(*args, **kwargs)
    except Exception as e:
        raise AssertionError(f"Function raised unexpected exception: {e}")


def assert_raises_with_message(exception_class, message_substring, func, *args, **kwargs):
    """
    Assert that the function raises a specific exception whose message contains specific text

    Args:
        exception_class: Expected exception class
        message_substring: Substring that should be in exception message
        func: Function to call
        *args: Positional arguments
        **kwargs: Keyword arguments
    """
    try:
        func(*args, **kwargs)
        raise AssertionError(f"Expected {exception_class.__name__} but no exception was raised")
    except exception_class as e:
        assert message_substring in str(e), \
            f"Expected message containing '{message_substring}', got '{str(e)}'"
    except Exception as e:
        raise AssertionError(
            f"Expected {exception_class.__name__}, got {type(e).__name__}: {e}"
        )


# Export all helper functions
__all__ = [
    # API assertions
    'assert_api_success',
    'assert_api_error',
    'assert_response_has_keys',

    # File mocks
    'create_mock_file',
    'create_mock_csv_file',

    # Database helpers
    'setup_mock_query_result',
    'assert_db_commit_called',
    'assert_db_rollback_called',
    'assert_db_add_called_with',
    'create_mock_dao_session',

    # Service/DAO helpers
    'create_mock_dao',

    # Auth helpers
    'generate_test_jwt',
    'create_auth_headers',

    # Validation
    'assert_dict_contains',
    'assert_no_exception',
    'assert_raises_with_message'
]

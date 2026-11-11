# Testing Guide

## Overview

This project uses pytest as its test framework and includes both unit tests and integration tests. The tests cover all three layers of the project architecture: Controller, Service, and DAO.

## Test Layout

```
server/tests/
├── conftest.py              # Shared fixtures and configuration
├── factories.py             # Test data factories
├── helpers.py               # Test helper functions
├── unit/                    # Unit tests
│   ├── controllers/         # Controller-layer tests
│   ├── services/            # Service-layer tests
│   ├── daos/                # DAO-layer tests
│   ├── auth/                # Authentication tests
│   ├── models/              # Model tests
│   └── ...
└── integration/             # Integration tests
    ├── test_user_workflow.py
    └── test_integration_scenarios.py
```

## Running Tests

### Run all tests
```bash
cd server
pytest tests/ -v
```

### Run the tests for a specific layer
```bash
# Run all DAO tests
pytest tests/unit/daos/ -v

# Run all Service tests
pytest tests/unit/services/ -v

# Run all Controller tests
pytest tests/unit/controllers/ -v

# Run integration tests
pytest tests/integration/ -v
```

### Run tests by marker
```bash
# Run tests marked as unit
pytest -m unit

# Run tests marked as integration
pytest -m integration

# Run tests marked as dao
pytest -m dao

# Run tests marked as service
pytest -m service

# Run tests marked as controller
pytest -m controller
```

### Generate a coverage report
```bash
# Run the tests and generate a coverage report
pytest tests/ --cov=. --cov-report=html --cov-report=term

# View the HTML coverage report
# Open htmlcov/index.html
```

### Run specific tests
```bash
# Run a specific test file
pytest tests/unit/daos/test_user.py -v

# Run a specific test class
pytest tests/unit/daos/test_user.py::TestUserDao -v

# Run a specific test method
pytest tests/unit/daos/test_user.py::TestUserDao::test_find_by_id_success -v
```

## Writing Tests

### DAO-layer test pattern

DAO tests should mock the database session and the SQLAlchemy query object:

```python
import pytest
from unittest.mock import patch, MagicMock
from dao.user import UserDao

@pytest.mark.unit
@pytest.mark.dao
class TestUserDao:
    @pytest.fixture
    def dao(self):
        return UserDao()

    @patch('model.user.User.query')
    def test_find_by_id(self, mock_query, dao):
        """Test finding a user by ID"""
        # Arrange
        mock_user = Mock(id=1, user_name="test")
        mock_query.get.return_value = mock_user

        # Act
        result = dao.find_by_id(1)

        # Assert
        assert result.id == 1
        mock_query.get.assert_called_once_with(1)
```

### Service-layer test pattern

Service tests should mock the DAO layer:

```python
import pytest
from unittest.mock import patch, Mock
from service.user import UserService

@pytest.mark.unit
@pytest.mark.service
class TestUserService:
    @pytest.fixture
    def service(self):
        return UserService()

    @patch('service.user.user_dao')
    def test_login_success(self, mock_user_dao, service):
        """Test successful user login"""
        # Arrange
        mock_user = Mock(id=1, password="hashed")
        mock_user_dao.find_by_phone_number.return_value = mock_user

        # Act
        result = service.login_by_password("+123", "password")

        # Assert
        assert result is not None
        mock_user_dao.find_by_phone_number.assert_called_once()
```

### Controller-layer test pattern

Controller tests should mock the Service layer:

```python
import pytest
from unittest.mock import patch

@pytest.mark.unit
@pytest.mark.controller
class TestUserController:
    @patch('controller.user.user_service')
    def test_login_api(self, mock_user_service, client):
        """Test the login API"""
        # Arrange
        mock_user_service.login_by_password.return_value = Mock(value="token")

        # Act
        response = client.post('/api/user/login', data={
            'phone_number': '+123',
            'password': 'password'
        })

        # Assert
        assert response.status_code == 200
        mock_user_service.login_by_password.assert_called_once()
```

### Integration test pattern

Integration tests exercise complete end-to-end flows and mock external dependencies (database, S3, etc.):

```python
import pytest

@pytest.mark.integration
class TestUserWorkflow:
    def test_complete_user_workflow(self, client):
        """Test the complete user workflow"""
        # 1. Register
        register_resp = client.post('/api/user/register', data={...})
        assert register_resp.status_code == 200

        # 2. Log in
        login_resp = client.post('/api/user/login', data={...})
        assert login_resp.status_code == 200

        # 3. Use the token to access a protected resource
        # ...
```

## Test Data Factories

Use the test data factories to create test data:

```python
from tests.factories import UserFactory, AnalysisFactory

# Create a single user
user_data = UserFactory.create(user_name="testuser")

# Create users in batch
users = UserFactory.create_batch(count=5)

# Create an analysis
analysis_data = AnalysisFactory.create(name="Test Analysis")
```

## Test Helper Functions

Use the test helper functions to simplify test code:

```python
from tests.helpers import (
    assert_api_success,
    assert_api_error,
    create_mock_file,
    create_auth_headers
)

# Assert a successful API response
assert_api_success(response, status_code=200)

# Assert an API error response
assert_api_error(response, status_code=400, error_code=1001)

# Create a mock file
file_obj = create_mock_file('test.csv', b'data')

# Create authentication headers
headers = create_auth_headers(user_id=1)
```

## Common Fixtures

The project provides several commonly used fixtures:

- `app` - Flask application instance
- `client` - Flask test client
- `authenticated_client` - authenticated test client
- `mock_db_session` - mock database session
- `test_user` - test user data
- `test_analysis` - test analysis data
- `mock_s3` - mock S3 service
- `mock_llm` - mock LLM service
- `mock_storage` - mock object storage service

See `tests/conftest.py` for details.

## CI/CD Integration

Unit tests run in GitHub Actions (on pushes to main and on PRs targeting main). See `.github/workflows/ci-cd.yml` for details.

Note: this is an early research release; some test modules have not yet been synchronized with the current implementation and may fail.

## Coverage Targets (targets, not yet reached)

- Overall coverage: ≥80%
- Controllers: ≥75%
- Services: ≥85%
- DAOs: ≥80%

## Best Practices

1. **Follow the AAA pattern**: Arrange, Act, Assert
2. **Test one thing per test**: keep tests simple and focused
3. **Use descriptive test names**: a test name should clearly state what is being tested
4. **Mock external dependencies**: unit tests should be fast and isolated
5. **Use fixtures to reuse code**: avoid duplicating code across tests
6. **Test edge cases**: test not only the normal flow but also error cases
7. **Keep tests independent**: tests should not depend on each other

## Troubleshooting

### Import errors
If you hit import errors, make sure that:
- you run pytest from the `server/` directory
- the Python path is configured correctly (`conftest.py` already configures it)

### Mocks have no effect
Make sure that:
- the mock path is correct (mock where the object is used, not where it is defined)
- you pass the full path to `patch`

### Test timeouts
- check for real external calls that have not been mocked
- make sure there are no infinite loops

## Contributing

When adding a new feature:
1. Write tests for new DAO methods
2. Write tests for new Service methods
3. Write tests for new API endpoints
4. Run the tests and make sure they pass
5. Check that coverage has not decreased

## References

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Flask testing documentation](https://flask.palletsprojects.com/en/2.3.x/testing/)

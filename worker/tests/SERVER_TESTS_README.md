# Server Test Suite for omicairn-worker

## Overview
This test suite provides mock-based unit and integration tests for the omicairn-worker server module. It checks control flow and request/response shapes; it does not run against a real database, object store or LLM service, and no coverage figures are claimed.

## Test Structure

### Unit Tests
- `test_server_health.py` - Health check endpoint tests
- `test_server_controller_task.py` - Task controller API tests
- `test_server_controller_computation.py` - Computation controller API tests
- `test_server_service_task.py` - Task service business logic tests
- `test_server_service_computation.py` - Computation service business logic tests
- `test_server_wrapper_tools.py` - Wrapper and utility tests
- `test_server_dynamic_generation.py` - Dynamic generation tests
- `test_server_visualizer.py` - Visualizer functionality tests

### Integration Tests
- `test_server_integration.py` - API integration tests

## Running Tests

### Run all server tests:
```bash
cd omicairn-worker
pytest tests/test_server_*.py -v
```

### Run specific test module:
```bash
pytest tests/test_server_health.py -v
```

### Run with coverage:
```bash
pytest tests/test_server_*.py --cov=server --cov-report=html
```

### Run specific test class:
```bash
pytest tests/test_server_controller_task.py::TestTaskController -v
```

### Run specific test method:
```bash
pytest tests/test_server_controller_task.py::TestTaskController::test_task_dispatch_api_success -v
```

## Areas Exercised (mock-based)

### Controllers (APIs)
- ✅ Health check endpoints
- ✅ Task management APIs
- ✅ Computation management APIs
- ✅ Dynamic generation APIs
- ✅ Visualizer APIs

### Services (Business Logic)
- ✅ Task service operations
- ✅ Computation service operations
- ✅ Dynamic generation service
- ✅ Visualizer service
- ✅ LLM monitoring service

### Data Access Layer
- ✅ Task DAO operations
- ✅ Computation DAO operations
- ✅ Node DAO operations
- ✅ Edge DAO operations
- ✅ Transaction handling

### Integration Scenarios
- ✅ Complete analysis workflow
- ✅ Data upload to analysis pipeline
- ✅ Error recovery and retry
- ✅ Multi-node parallel execution
- ✅ Dynamic code generation flow
- ✅ Visualization generation
- ✅ User feedback loops

### Utilities and Tools
- ✅ Exception wrapper
- ✅ Database session management
- ✅ Response manager
- ✅ Authority and authentication
- ✅ Flow tool (execution order)
- ✅ Computation launcher
- ✅ JSON encoder

## Test Configuration

All tests use the global pytest configuration in `conftest.py` which provides:
- Automatic database mocking
- Environment variable setup
- Common fixtures
- Mock objects for external services

## Mock Strategy

Tests follow a consistent mocking strategy:
1. **Database**: All database connections are mocked at the SQLAlchemy level
2. **External Services**: AWS services (S3, Batch, CloudWatch) are mocked
3. **LLM Services**: OpenAI/GPT calls are mocked
4. **File System**: S3 operations are mocked with Porter

## Adding New Tests

When adding new tests:
1. Create test file following naming convention: `test_server_<module>.py`
2. Group related tests in classes
3. Use descriptive test method names: `test_<feature>_<scenario>`
4. Mock external dependencies
5. Verify both success and failure cases
6. Add docstrings explaining what is being tested

## Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Mock all external dependencies
3. **Clarity**: Use clear, descriptive names
4. **Coverage**: Test both success and error paths
5. **Speed**: Unit tests should run quickly
6. **Documentation**: Add docstrings to explain complex tests

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- No real database connections required
- No external service dependencies
- Fast execution time
- Clear failure messages

## Common Patterns

### Testing API Controllers
```python
def test_api_endpoint(self):
    with patch('server.controller.module.request') as mock_request, \
         patch('server.controller.module.service') as mock_service:
        # Setup mocks
        mock_request.get_json.return_value = {...}
        mock_service.method.return_value = {...}
        
        # Test
        api = APIClass()
        result = api.post()
        
        # Verify
        assert result["code"] == 200
```

### Testing Services
```python
def test_service_method(self):
    with patch('server.service.module.dao') as mock_dao:
        # Setup mocks
        mock_dao.method.return_value = Mock(...)
        
        # Test
        service = ServiceClass()
        result = service.method(args)
        
        # Verify
        assert result is not None
```

### Testing DAOs
```python
def test_dao_operation(self):
    with patch('server.dao.module.alchemy_db') as mock_db:
        # Setup mocks
        mock_session = Mock()
        mock_db.session = mock_session
        
        # Test
        dao = DAOClass()
        result = dao.find_by_id("id_123")
        
        # Verify
        mock_session.query.assert_called_once()
```

## Troubleshooting

### Import Errors
- Ensure pytest is installed: `pip install pytest pytest-mock`
- Check Python path includes server directory

### Mock Not Working
- Verify patch target path is correct
- Check if import happens before patching

### Flaky Tests
- Ensure tests don't depend on execution order
- Check for shared state between tests
- Use proper fixtures for setup/teardown

## Future Improvements

- [ ] Add performance benchmarks
- [ ] Add stress tests for concurrent operations
- [ ] Add tests for batch job processing
- [ ] Add tests for websocket connections
- [ ] Improve test data generators
- [ ] Add API contract tests
- [ ] Add database migration tests

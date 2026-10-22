# OmiCairn-Worker Test Suite

This directory contains unit tests for the omicairn-worker component, focusing on API interactions with the LLM/agent service and internal service functionality. This is research-grade software: many tests are mock-based and do not constitute measured coverage.

## Test Suites

### Server Module Tests
Unit and integration tests for the `server` module.

**Quick Links:**
- **[Quick Start Guide](QUICK_START.md)** - Get started in 5 minutes
- **[Commands Reference](TEST_COMMANDS.md)** - All test commands

**Documentation:**
- [Complete Documentation](SERVER_TESTS_README.md)

**Run Server Tests:**
```bash
# Run all server tests
python tests/run_server_tests.py

# Run with coverage
python tests/run_server_tests.py --coverage

# Run by category
python tests/run_server_tests.py --category controllers
```

**Test Files:** `test_server_*.py`

---

## Quick Start

### Run All Tests
```bash
python run_tests.py
```

### Run with Coverage
```bash
python run_tests.py --coverage --html-report
```

### Run Specific Test Module
```bash
python run_tests.py -m test_dynamic_generation_apis.py -v
```

### Run Individual Test Suites
```bash
python run_tests.py --suites
```

## Test Structure

### Core Test Files

1. **test_dynamic_generation_apis.py** - Tests for dynamic function block generation APIs
   - `TestDynamicGenerationLlmInterface` - Tests LlmInterface class for dynamic generation
   - `TestDynamicGenerationServerAgent` - Tests ServerAgent class for server communication
   - `TestDynamicGenerationErrorHandling` - Error handling scenarios

2. **test_chat_apis.py** - Tests for chat-related API interactions
   - `TestChatAPIInteractions` - All chat API functionality (init, send, history)
   - `TestChatErrorHandling` - Chat-specific error scenarios
   - `TestChatIntegrationScenarios` - End-to-end chat workflows

3. **test_job_feedback_apis.py** - Tests for job feedback processing APIs
   - `TestJobFeedbackLlmInterface` - Tests LlmInterface for error optimization
   - `TestJobFeedbackHandling` - Tests computation success/failure handling
   - `TestDynamicGenerationAgent` - Tests dynamic generation agent functionality
   - `TestBugFixerAgent` - Tests bug fixing and retry mechanisms
   - `TestJobFeedbackMain` - Tests main job feedback workflow
   - `TestJobFeedbackErrorHandling` - Error handling in job feedback processing

4. **test_visualizer_apis.py** - Tests for visualizer processing APIs
   - `TestVisualizerLlmInterface` - Tests LlmInterface for visualization
   - `TestVisualizerServerAgent` - Tests ServerAgent for visualizer operations
   - `TestVisualizerProcessing` - Tests visualization processing workflows
   - `TestVisualizerFunctionBlockCreation` - Tests function block creation for visualizations
   - `TestVisualizerErrorHandling` - Error handling in visualizer processing
   - `TestVisualizerIntegration` - Integration scenarios for visualizer functionality

5. **test_server_core.py** - Tests for server core functionality
   - `TestTaskController` - Tests task controller API endpoints
   - `TestTaskService` - Tests task service functionality
   - `TestNodeDAO` - Tests node data access object operations
   - `TestTaskDAO` - Tests task data access object operations
   - `TestComputationDAO` - Tests computation data access object operations
   - `TestServerModelsIntegration` - Tests integration between models and DAOs
   - `TestServerErrorHandling` - Error handling in server components

6. **test_integration_scenarios.py** - Integration tests and comprehensive error handling
   - `TestCrossModuleIntegration` - Tests integration across different modules
   - `TestErrorHandlingScenarios` - Comprehensive error handling tests
   - `TestConcurrentOperations` - Tests concurrent operations and race conditions
   - `TestDataFlowValidation` - Tests data flow and state transitions
   - `TestPerformanceAndScalability` - Performance and scalability tests

### 🆕 Advanced Test Files

7. **test_performance.py** - Performance and scalability testing
   - `TestPerformanceScenarios` - Load testing and concurrent request handling
   - `TestScalabilityTests` - System limits and maximum user scenarios
   - `TestResourceUtilizationTests` - CPU, memory, and network resource testing

8. **test_security.py** - Security and defensive testing
   - `TestAuthenticationSecurity` - Authentication mechanisms and token validation
   - `TestInputValidationSecurity` - SQL injection, XSS, and command injection prevention
   - `TestAuthorizationSecurity` - Access control and user isolation
   - `TestDataProtectionSecurity` - Data filtering and privacy measures
   - `TestNetworkSecurity` - SSL, timeouts, and rate limiting

9. **test_edge_cases.py** - Edge cases and boundary conditions
   - `TestBoundaryConditions` - Empty inputs, maximum sizes, unicode handling
   - `TestUnusualScenarios` - Simultaneous requests, rapid sequences, mixed patterns
   - `TestCornerCaseDataScenarios` - Circular references, extreme values, malformed data
   - `TestResourceExhaustionScenarios` - Memory-intensive and high-frequency operations

10. **test_configuration.py** - Configuration and environment testing
    - `TestEnvironmentVariables` - Environment variable handling and validation

## Test Categories

### API Integration Tests
- Dynamic function block generation (`dynamic_fb`, `dynamic_fb_with_plan`)
- Node report generation (`get_node_report`)
- Workflow report creation (`create_workflow_report`)
- Pipeline recommendation (`recommend_pipeline`)
- Chat functionality (init, send messages, history)
- Error description optimization

### Server Communication Tests
- Node creation and management
- Edge creation between nodes
- Task launching and monitoring
- Computation history retrieval
- LLM consumption recording

### Error Handling Tests
- Network failures and timeouts
- Authentication errors
- Invalid parameters
- Server error responses
- Status code validation

## 🧪 Running Tests

### Using the Test Runner (Recommended)
```bash
# Run all tests with coverage
python run_tests.py --coverage --html-report

# Run specific module with verbose output
python run_tests.py -m test_security.py -v

# Run tests matching a pattern
python run_tests.py -k "test_authentication" -v

# Run individual test suites
python run_tests.py --suites

# Run with parallel execution
python run_tests.py --parallel 4 --verbose
```

### Using pytest directly
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_dynamic_generation_apis.py -v
python -m pytest tests/test_performance.py -v

# Run tests by category
python -m pytest tests/ -m "api" -v          # API integration tests
python -m pytest tests/ -m "unit" -v         # Unit tests
python -m pytest tests/ -m "integration" -v  # Integration tests
python -m pytest tests/ -m "performance" -v  # Performance tests
python -m pytest tests/ -m "security" -v     # Security tests

# Run with coverage
python -m pytest tests/ --cov=handle_dynamic_generation --cov=handle_job_feedback --cov=handle_visualizer --cov=server --cov-report=html
```

### Test Categories and Markers

- `@pytest.mark.api` - API integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests  
- `@pytest.mark.performance` - Performance and load tests
- `@pytest.mark.security` - Security and defensive tests
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.edge_case` - Edge case and boundary tests

## Test Configuration

### Global Fixtures (conftest.py)
- `mock_database_globally` - Mocks all database connections
- `mock_requests` - Mocks HTTP requests to external services
- `mock_logger` - Mocks logging to avoid setup issues
- `sample_dynamic_generation_data` - Sample test data
- `sample_llm_response` - Sample LLM response data

### Environment Variables
The test suite automatically sets required environment variables:
- `MYSQL_*` - Database connection settings
- `GPT_WORKFLOW_SERVER_*` - GPT server configuration
- `MAIN_SERVER_HOST` - Main server endpoint
- `COMPUTATION_SERVER_HOST` - Computation server endpoint

## API Compatibility

These tests exercise the request shapes sent to the LLM/agent service API endpoints:

### Dynamic Generation Endpoints
- `POST /dynamic_fb/get` - Generate dynamic function blocks
- `GET /data/interpretation/get` - Get node reports
- `GET /report/get` - Create workflow reports
- `POST /workflow` - Recommend pipelines
- `GET /pipline/template/get` - Get similar templates
- `POST /error/write` - Error description optimization

### Chat Endpoints
- `POST /oldchat/init` - Initialize chat
- `GET /oldchat/history` - Get chat history
- `POST /oldchat/` - Send chat message
- `POST /oldchat/init/global` - Initialize global chat
- `POST /oldchat/global` - Send global message
- `POST /oldchat/init/local` - Initialize local chat
- `POST /oldchat/local` - Send local message
- `GET /chat/history/all` - Get complex chat list
- `GET /chat/history` - Get complex chat messages
- `POST /chat/init/analysis` - Initialize complex chat
- `POST /chat/analysis` - Send complex message

## Test Data Validation

All tests validate:
- Correct URL construction
- Proper parameter passing
- Request body structure
- Response handling
- Error propagation
- Authentication headers

## 📊 Test Metrics and Coverage

### Coverage Reports
```bash
# Generate HTML coverage report
python run_tests.py --coverage --html-report
# Open htmlcov/index.html in browser

# Generate XML coverage report (for CI/CD)
python run_tests.py --coverage --xml-report
```

### Performance Benchmarks
```bash
# Run performance tests only
python -m pytest tests/test_performance.py -v

# Run with performance profiling
python -m pytest tests/test_performance.py --profile
```

## 🔧 Advanced Testing Features

### Parallel Test Execution
```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel
python run_tests.py --parallel 4
```

### Test Debugging
```bash
# Run with debugging on failure
python -m pytest tests/ --pdb

# Run with extra output
python -m pytest tests/ -s --tb=long

# Run only failed tests from last run
python -m pytest tests/ --lf
```

### Custom Test Filters
```bash
# Run tests by name pattern
python -m pytest tests/ -k "test_authentication or test_security"

# Skip slow tests
python -m pytest tests/ -m "not slow"

# Run only critical tests
python -m pytest tests/ -m "critical"
```

## 🚀 Continuous Integration

These tests are designed to run in CI/CD environments with:
- No external service dependencies
- Mocking of external services
- Fast execution times
- Clear failure reporting
- Coverage tracking
- Parallel execution support
- XML test result generation
- Multiple Python version compatibility

### CI/CD Pipeline Example
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-xdist
    - name: Run tests
      run: python run_tests.py --coverage --xml-report --parallel 2
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 🛠️ Test Development Guidelines

### Writing New Tests
1. **Follow naming conventions**: `test_feature_scenario`
2. **Use descriptive docstrings**: Explain what the test validates
3. **Group related tests**: Use classes to organize test methods
4. **Mock external dependencies**: Use `mock_requests`, `mock_database_globally`
5. **Add appropriate markers**: `@pytest.mark.api`, `@pytest.mark.unit`, etc.

### Test Structure
```python
class TestNewFeature:
    """Test new feature functionality."""
    
    def test_basic_functionality(self, mock_requests, mock_logger):
        """Test basic feature operation."""
        # Arrange
        mock_requests['post'].return_value = Mock(status_code=200)
        
        # Act
        result = feature_function()
        
        # Assert
        assert result.status_code == 200
        mock_requests['post'].assert_called_once()
```

### Performance Testing Guidelines
- Test with realistic data sizes
- Include concurrent operation scenarios
- Set reasonable timeout expectations
- Monitor memory usage patterns
- Test system behavior under load

### Security Testing Guidelines
- Test input validation and sanitization
- Verify authentication and authorization
- Test for common vulnerabilities (XSS, SQL injection)
- Validate sensitive data handling
- Test rate limiting and DoS protection

## 🛡️ Database Isolation & Safety

### Comprehensive Database Mocking
Tests are intended to be isolated from real databases through:

```python
# conftest.py - Global database mocking (autouse=True)
@pytest.fixture(autouse=True)
def mock_database_globally():
    """Mock ALL database connections globally."""
    with patch('sqlalchemy.create_engine') as mock_create_engine, \
         patch('pymysql.connect') as mock_pymysql, \
         patch('mysql.connector.connect') as mock_mysql_connector, \
         patch('sqlite3.connect') as mock_sqlite3:
        # ... comprehensive mocking
```

### Safety Verification
```bash
# Run database isolation tests
python -m pytest tests/test_database_isolation.py -v
```

### Safety Features
- ✅ **Autouse fixtures**: All database connections mocked automatically
- ✅ **Environment validation**: Test-only database credentials enforced  
- ✅ **Safeguard**: test-only database credentials are forced by `conftest.py`
- ✅ **Mocking**: SQLAlchemy, PyMySQL, MySQL Connector, SQLite (psycopg2 stubbed if absent)
- ✅ **Session isolation**: All database sessions are mocked
- ✅ **Connection pooling**: Database pools are mocked
- ✅ **Transaction safety**: All transactions use mock objects
- ✅ **Post-test cleanup**: Removes any test database files

### Intended Isolation
- **No real network connections** to database servers
- **No actual database queries** executed
- **No production data** accessed or modified
- **No database files** created (except temporary test files)
- **Environment variables** forced to test-safe values

## 📋 Test Checklist

Before submitting code, ensure:
- [ ] All existing tests pass
- [ ] New features have corresponding tests
- [ ] Edge cases are covered
- [ ] Security implications are tested
- [ ] Performance impact is assessed
- [ ] Tests follow project conventions
- [ ] Documentation is updated
- [ ] **Database safety verified**: `python -m pytest tests/test_database_isolation.py`
- [ ] **No production database access**: All connections properly mocked
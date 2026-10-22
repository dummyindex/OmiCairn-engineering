# Quick Test Commands

## Run all server tests
python tests/run_server_tests.py

## Run with coverage report
python tests/run_server_tests.py --coverage

## Run specific categories
python tests/run_server_tests.py --category controllers
python tests/run_server_tests.py --category services
python tests/run_server_tests.py --category integration

## Run specific test file
pytest tests/test_server_health.py -v

## Run specific test class
pytest tests/test_server_controller_task.py::TestTaskController -v

## Run specific test method
pytest tests/test_server_controller_task.py::TestTaskController::test_task_dispatch_api_success -v

## Run with verbose output and show print statements
pytest tests/test_server_*.py -v -s

## Run and stop at first failure
pytest tests/test_server_*.py -x

## Run tests matching a pattern
pytest tests/test_server_*.py -k "health" -v

## Run tests in parallel (requires pytest-xdist)
pytest tests/test_server_*.py -n auto

## Generate HTML coverage report
pytest tests/test_server_*.py --cov=server --cov-report=html
# Then open htmlcov/index.html in browser

## Run with detailed failure output
pytest tests/test_server_*.py -vv --tb=long

## Run tests and show durations
pytest tests/test_server_*.py --durations=10

## Run only failed tests from last run
pytest tests/test_server_*.py --lf

## Run tests that failed last time, then others
pytest tests/test_server_*.py --ff

## Useful combinations
# Run specific category with coverage
pytest tests/test_server_controller_*.py --cov=server.controller --cov-report=term

# Run integration tests with verbose output
pytest tests/test_server_integration.py -vv

# Quick smoke test (health + basic endpoints)
pytest tests/test_server_health.py tests/test_server_controller_task.py -v

## Windows PowerShell
# Run all server tests
python tests\run_server_tests.py

# Run with coverage
python tests\run_server_tests.py --coverage

# Run specific category
python tests\run_server_tests.py --category controllers

# omicairn-worker Server Tests: Quick Start

> Research-grade software. Most server tests are mock-based unit tests; they check
> request/response shapes and control flow, not end-to-end behaviour against a real
> database, object store or LLM service. No coverage figures are claimed here.

## 1. Install test dependencies

```bash
pip install pytest pytest-mock pytest-cov
```

## 2. Run the server tests

```bash
# Using the runner script
python tests/run_server_tests.py

# Or directly with pytest
pytest tests/test_server_*.py -v
```

## 3. Run a category

```bash
python tests/run_server_tests.py --category controllers
python tests/run_server_tests.py --category services
python tests/run_server_tests.py --category integration
```

## 4. Coverage report (optional)

```bash
pytest tests/test_server_*.py --cov=server --cov-report=html
# then open htmlcov/index.html
```

## Test files

```
tests/
├── test_server_health.py                  # health check API
├── test_server_controller_task.py         # task controller
├── test_server_controller_computation.py  # computation controller
├── test_server_service_task.py            # task service
├── test_server_service_computation.py     # computation service
├── test_server_dynamic_generation.py      # dynamic generation
├── test_server_visualizer.py              # visualizer
├── test_server_wrapper_tools.py           # response manager
├── test_server_integration.py             # mock-based integration flows
├── run_server_tests.py                    # runner script
├── SERVER_TESTS_README.md                 # detailed documentation
└── TEST_COMMANDS.md                       # command reference
```

All database connections are mocked by the autouse fixture in the repository-level
`conftest.py`; see `test_database_isolation.py`.

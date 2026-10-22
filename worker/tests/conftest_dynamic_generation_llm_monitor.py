"""
Dynamic Generation LLM Monitor test configuration

Provides common fixtures and configuration needed by the tests
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch


@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "test_generation_id": 12345,
        "test_branch_id": 54321,
        "test_node_ids": [1000, 1001, 1002, 1003],
        "test_retry_process_id": 9999,
        "test_computation_id": 8888,
        "s3_test_bucket": "test-omicairn-bucket",
        "max_response_time": 2.0,  # Maximum response time (seconds)
        "max_concurrent_requests": 10
    }


@pytest.fixture
def mock_dynamic_generation():
    """Common dynamic_generation mock object"""
    return Mock(
        generation_id=12345,
        previous_node_id=1000,
        user_request="Test user request: generate a data processing pipeline",
        state="running",
        max_node=10,
        max_branch=3,
        created_time=datetime.now() - timedelta(hours=1)
    )


@pytest.fixture
def mock_dynamic_generation_branch():
    """Common branch mock object"""
    return Mock(
        id=54321,
        dynamic_generation_id=12345,
        end_node_id=1003,
        state="running",
        created_time=datetime.now() - timedelta(minutes=30),
        updated_time=datetime.now() - timedelta(minutes=5)
    )


@pytest.fixture
def mock_nodes():
    """Common list of node mock objects"""
    base_time = datetime.now() - timedelta(minutes=30)
    return [
        Mock(
            id=1000, 
            name="Data input node",
            created_time=base_time,
            dynamic_generation_id=12345
        ),
        Mock(
            id=1001, 
            name="Data cleaning node",
            created_time=base_time + timedelta(minutes=5),
            dynamic_generation_id=12345
        ),
        Mock(
            id=1002, 
            name="Data transformation node",
            created_time=base_time + timedelta(minutes=10),
            dynamic_generation_id=12345
        ),
        Mock(
            id=1003, 
            name="Data output node",
            created_time=base_time + timedelta(minutes=15),
            dynamic_generation_id=12345
        )
    ]


@pytest.fixture
def mock_retry_process():
    """Common retry process mock object"""
    return Mock(
        id=9999,
        node_id=1002,
        task_id=7777,
        state="running",
        max_retry=5,
        rest_retry=3,
        created_time=datetime.now() - timedelta(minutes=10),
        user_prompt="Fix the data type conversion error"
    )


@pytest.fixture
def mock_computation():
    """Common computation mock object"""
    return Mock(
        id=8888,
        node_id=1002,
        task_id=7777,
        retry_process_id=9999,
        computation_state="failed",
        created_time=datetime.now() - timedelta(minutes=8),
        error_description="Data type mismatch error"
    )


@pytest.fixture
def sample_s3_prompt_data():
    """Sample S3 prompt data"""
    return {
        "user_request": "Please generate a data cleaning function block",
        "context": {
            "previous_node_output": {
                "data_type": "CSV",
                "columns": ["name", "age", "salary", "department"],
                "row_count": 1000,
                "null_values": ["age: 5", "salary: 12"]
            },
            "user_requirements": [
                "Remove null values",
                "Standardize data format",
                "Add data validation"
            ]
        },
        "generation_mode": "mixed",
        "max_branch": 3,
        "timestamp": int((datetime.now() - timedelta(minutes=20)).timestamp() * 1000)
    }


@pytest.fixture
def sample_s3_output_data():
    """Sample S3 output data"""
    return {
        "satisfied": False,
        "reasoning": "A dedicated data cleaning function block needs to be generated",
        "next_level_function_blocks": [
            {
                "name": "Data cleaning FB",
                "programming_language": "Python",
                "function_block_code": """
def clean_data(df):
    # Remove null values
    df_cleaned = df.dropna()
    
    # Standardize data format
    if 'age' in df_cleaned.columns:
        df_cleaned['age'] = pd.to_numeric(df_cleaned['age'], errors='coerce')
    
    if 'salary' in df_cleaned.columns:
        df_cleaned['salary'] = pd.to_numeric(df_cleaned['salary'], errors='coerce')
    
    return df_cleaned
                """,
                "parameters": {
                    "input_data": "{{previous_node_output}}",
                    "clean_strategy": "aggressive"
                },
                "static_config_file_content": {
                    "description": "Data cleaning function block that removes null values and standardizes format",
                    "args": [
                        {
                            "name": "clean_strategy",
                            "value_type": "str",
                            "description": "Cleaning strategy: conservative or aggressive",
                            "default_value": "conservative",
                            "render_type": "select",
                            "options": ["conservative", "aggressive"]
                        }
                    ]
                },
                "requirements_file_content": "pandas>=1.3.0\nnumpy>=1.21.0"
            }
        ],
        "timestamp": int((datetime.now() - timedelta(minutes=19)).timestamp() * 1000)
    }


@pytest.fixture
def sample_retry_session_data():
    """Sample retry process session data"""
    return {
        "node_computation_information": {
            "node_id": 1002,
            "computation_id": 8888,
            "error_type": "parameter_error",
            "error_description": "Parameter type mismatch: expected float, got str",
            "failed_params": {
                "threshold": "0.95",  # Should be a float
                "method": "linear"
            }
        },
        "input_prompt": "Fix node parameters based on the error message: parameter type mismatch",
        "parameters_fix_solution": {
            "fix_applied": True,
            "original_params": {
                "threshold": "0.95",
                "method": "linear"
            },
            "fixed_params": {
                "threshold": 0.95,  # Fixed to float type
                "method": "linear"
            },
            "fix_explanation": "Converted the threshold parameter from string type to float type"
        },
        "code_fix_solution": None,  # Only a parameter fix this time; no code fix needed
        "result": {
            "success": True,
            "message": "Parameters fixed successfully",
            "retry_computation_id": 8889
        }
    }


@pytest.fixture
def mock_s3_environment():
    """Mock S3 environment"""
    class MockS3Environment:
        def __init__(self):
            self.storage = {}
        
        def store_data(self, path, data):
            self.storage[path] = json.dumps(data) if isinstance(data, dict) else data
        
        def retrieve_data(self, path):
            return self.storage.get(path, "")
        
        def setup_dynamic_generation_data(self, generation_id, node_id, prompt_data, output_data):
            prompt_path = f"dynamic_generation/{generation_id}/{node_id}/prompt.json"
            output_path = f"dynamic_generation/{generation_id}/{node_id}/output.json"
            self.store_data(prompt_path, prompt_data)
            self.store_data(output_path, output_data)
        
        def setup_retry_process_data(self, retry_process_id, computation_id, session_data):
            session_path = f"retry_process/{retry_process_id}/{computation_id}/session.json"
            self.store_data(session_path, session_data)
    
    return MockS3Environment()


@pytest.fixture
def mock_database_data(mock_dynamic_generation, mock_dynamic_generation_branch, 
                      mock_nodes, mock_retry_process, mock_computation):
    """Mock complete database data structure"""
    return {
        "dynamic_generations": {12345: mock_dynamic_generation},
        "branches": {54321: mock_dynamic_generation_branch},
        "nodes": {node.id: node for node in mock_nodes},
        "retry_processes": {9999: mock_retry_process},
        "computations": {8888: mock_computation},
        "edges": [
            # Mock edge relationships: 1000 -> 1001 -> 1002 -> 1003
            {"source_node_id": 1000, "target_node_id": 1001},
            {"source_node_id": 1001, "target_node_id": 1002},
            {"source_node_id": 1002, "target_node_id": 1003}
        ]
    }


@pytest.fixture
def performance_benchmarks():
    """Performance benchmark configuration"""
    return {
        "single_branch_max_time": 2.0,  # Max single-branch query time (seconds)
        "full_task_max_time": 5.0,     # Max full-task query time (seconds)
        "concurrent_requests": 10,      # Number of concurrent requests
        "large_dataset_nodes": 100,     # Number of nodes in large dataset
        "memory_limit_mb": 100          # Memory usage limit (MB)
    }


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Automatically set up test logging"""
    import logging
    
    # Set the log level during tests
    logging.getLogger("DynamicGenerationLLMMonitor").setLevel(logging.DEBUG)
    
    # Test-specific log handlers can be added here
    test_handler = logging.StreamHandler()
    test_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    test_handler.setFormatter(formatter)
    
    logger = logging.getLogger("DynamicGenerationLLMMonitor")
    if not logger.handlers:
        logger.addHandler(test_handler)
    
    yield
    
    # Clean up test log handlers
    logger.removeHandler(test_handler)


# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "unit: unit test marker"
    )
    config.addinivalue_line(
        "markers", "integration: integration test marker"
    )
    config.addinivalue_line(
        "markers", "performance: performance test marker"
    )
    config.addinivalue_line(
        "markers", "slow: marker for long-running tests"
    )


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Automatically clean up test data"""
    yield
    
    # Clean up any leftover mock data after the test
    # Cleanup logic can be added here, e.g. resetting global variables
    pass
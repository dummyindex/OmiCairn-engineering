import pytest
import json
import time
import threading
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from flask import Flask
from concurrent.futures import ThreadPoolExecutor, as_completed

from server.service.dynamic_generation_llm_monitor import DynamicGenerationLLMMonitorService
from server.controller.dynamic_generation_llm_monitor import dynamic_generation_llm_monitor_bp
from server.main import app


class TestDynamicGenerationLLMMonitorIntegration:
    """Dynamic Generation LLM monitoring integration tests"""

    @pytest.fixture
    def test_app(self):
        """Create the test app"""
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, test_app):
        """Create the test client"""
        return test_app.test_client()

    @pytest.fixture
    def sample_generation_data(self):
        """Create sample generation data"""
        return {
            "generation_id": 12345,
            "user_request": "Integration test: generate a data analysis FB",
            "state": "running",
            "previous_node_id": 1000,
            "max_node": 10,
            "max_branch": 3
        }

    @pytest.fixture
    def sample_branch_data(self):
        """Create sample branch data"""
        return {
            "id": 54321,
            "dynamic_generation_id": 12345,
            "end_node_id": 1003,
            "state": "running",
            "created_time": datetime.now() - timedelta(minutes=30),
            "updated_time": datetime.now() - timedelta(minutes=5)
        }

    @pytest.fixture
    def sample_nodes_data(self):
        """Create sample node data"""
        return [
            {"id": 1000, "name": "Data input node", "created_time": datetime.now() - timedelta(minutes=30)},
            {"id": 1001, "name": "Data processing node", "created_time": datetime.now() - timedelta(minutes=25)},
            {"id": 1002, "name": "Data analysis node", "created_time": datetime.now() - timedelta(minutes=20)},
            {"id": 1003, "name": "Result output node", "created_time": datetime.now() - timedelta(minutes=15)}
        ]

    @pytest.fixture
    def sample_llm_interactions(self):
        """Create sample LLM interaction data"""
        return [
            {
                "type": "dynamic_generation",
                "node_id": 1001,
                "input": {
                    "prompt": "Based on the input data, generate a data processing function block",
                    "context": "The user uploaded sales data in CSV format that needs cleaning and preprocessing"
                },
                "output": {
                    "response": "I will generate a data cleaning FB for you",
                    "next_level_function_blocks": [
                        {
                            "name": "Data cleaning FB",
                            "programming_language": "Python",
                            "function_block_code": "def clean_data(df): return df.dropna()"
                        }
                    ]
                },
                "timestamp": int((datetime.now() - timedelta(minutes=25)).timestamp() * 1000)
            },
            {
                "type": "bug_fixer", 
                "node_id": 1002,
                "retry_process_id": 9999,
                "computation_id": 8888,
                "input": {
                    "prompt": "Fix the parameter error of the data analysis node",
                    "node_computation_info": {"error": "Parameter type mismatch"}
                },
                "output": {
                    "parameters_fix_solution": {"fix_applied": True, "new_params": {"dtype": "float64"}},
                    "result": {"success": True, "message": "Parameters fixed"}
                },
                "timestamp": int((datetime.now() - timedelta(minutes=20)).timestamp() * 1000)
            }
        ]

    def test_end_to_end_branches_api(self, client, sample_generation_data, sample_branch_data):
        """End-to-end test: branch list API"""
        with patch('server.service.dynamic_generation.dynamic_generation_service') as mock_service:
            # Set up mock data
            mock_generation = Mock(**sample_generation_data)
            mock_branch = Mock(**sample_branch_data)
            
            mock_service.get_by_id.return_value = mock_generation
            mock_service.get_generation_branch_list_by_generation_id.return_value = [mock_branch]
            
            # Send the request
            response = client.get('/dynamic-generation-llm-monitor/branches?generation_id=12345')
            
            # Verify the response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 200
            assert data['data']['generation_id'] == 12345
            assert len(data['data']['branches']) == 1
            assert data['data']['branches'][0]['id'] == 54321

    def test_end_to_end_single_branch_api(self, client, sample_llm_interactions):
        """End-to-end test: single-branch monitoring API"""
        with patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_llm_monitor_service') as mock_service:
            # Set up mock response
            mock_service.get_single_branch_interactions.return_value = {
                "branch_id": 54321,
                "generation_id": 12345,
                "end_node_id": 1003,
                "interactions": sample_llm_interactions,
                "total_count": 2,
                "last_updated": int(datetime.now().timestamp() * 1000)
            }
            
            # Send the request
            response = client.get('/dynamic-generation-llm-monitor/single-branch?generation_id=12345&branch_id=54321')
            
            # Verify the response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 200
            assert data['data']['total_count'] == 2
            assert len(data['data']['interactions']) == 2
            
            # Verify the interaction data structure
            interactions = data['data']['interactions']
            assert interactions[0]['type'] == 'dynamic_generation'
            assert interactions[1]['type'] == 'bug_fixer'

    def test_end_to_end_full_task_api(self, client, sample_generation_data, sample_branch_data, sample_llm_interactions):
        """End-to-end test: full-task monitoring API"""
        with patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_llm_monitor_service') as mock_service:
            # Set up mock response
            mock_service.get_full_task_interactions.return_value = {
                "generation_id": 12345,
                "user_request": sample_generation_data["user_request"],
                "state": "running",
                "branches": [{"id": 54321, "end_node_id": 1003, "state": "running"}],
                "interactions": sample_llm_interactions,
                "total_count": 2,
                "last_updated": int(datetime.now().timestamp() * 1000)
            }
            
            # Send the request
            response = client.get('/dynamic-generation-llm-monitor/full-task?generation_id=12345')
            
            # Verify the response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 200
            assert data['data']['generation_id'] == 12345
            assert data['data']['total_count'] == 2
            assert len(data['data']['branches']) == 1

    def test_api_parameter_validation(self, client):
        """Test API parameter validation"""
        # Test missing required parameters
        response = client.get('/dynamic-generation-llm-monitor/branches')
        assert response.status_code != 200  # should return an error
        
        response = client.get('/dynamic-generation-llm-monitor/single-branch?generation_id=123')
        assert response.status_code != 200  # missing branch_id
        
        response = client.get('/dynamic-generation-llm-monitor/full-task')
        assert response.status_code != 200  # missing generation_id

    def test_api_error_handling(self, client):
        """Test API error handling"""
        with patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_llm_monitor_service') as mock_service:
            # Simulate a service-layer error
            mock_service.get_full_task_interactions.return_value = {
                "error": "Dynamic generation not found"
            }
            
            response = client.get('/dynamic-generation-llm-monitor/full-task?generation_id=99999')
            
            # Verify the error response
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['code'] == 400


class TestDynamicGenerationLLMMonitorPerformance:
    """Performance tests"""

    @pytest.fixture
    def service(self):
        return DynamicGenerationLLMMonitorService()

    @pytest.fixture
    def performance_test_data(self):
        """Generate performance test data"""
        return {
            "generation_id": 99999,
            "node_count": 100,
            "retry_process_count": 50,
            "interactions_per_node": 2
        }

    def test_single_branch_response_time(self, service, performance_test_data):
        """Test single-branch monitoring response time"""
        with patch.multiple(
            service,
            _get_nodes_in_generation_path=Mock(return_value=list(range(1, performance_test_data["node_count"] + 1))),
            _get_dynamic_generation_interaction=Mock(return_value={
                "type": "dynamic_generation",
                "timestamp": int(datetime.now().timestamp() * 1000),
                "node_id": 1
            })
        ):
            with patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao') as mock_dao:
                with patch('server.service.dynamic_generation_llm_monitor.computation_dao') as mock_comp_dao:
                    # Set up mocks
                    mock_dao.find_branch_by_id.return_value = Mock(
                        dynamic_generation_id=99999,
                        end_node_id=100,
                        id=12345
                    )
                    mock_comp_dao.find_retry_process_by_node_id.return_value = []
                    
                    # Measure the response time
                    start_time = time.time()
                    result = service.get_single_branch_interactions(99999, 12345)
                    end_time = time.time()
                    
                    response_time = end_time - start_time
                    
                    # Verify the response time is under 2 seconds (suits a 2-second polling interval)
                    assert response_time < 2.0, f"Response time too long: {response_time}s"
                    assert "error" not in result
                    assert result["total_count"] == performance_test_data["node_count"]

    def test_full_task_response_time_large_dataset(self, service, performance_test_data):
        """Test full-task monitoring response time on a large dataset"""
        large_node_list = list(range(1, performance_test_data["node_count"] + 1))
        
        with patch.multiple(
            service,
            _get_nodes_in_generation_path=Mock(return_value=large_node_list),
            _get_dynamic_generation_interaction=Mock(return_value={
                "type": "dynamic_generation",
                "timestamp": int(datetime.now().timestamp() * 1000),
                "node_id": 1
            })
        ):
            with patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao') as mock_dao:
                with patch('server.service.dynamic_generation_llm_monitor.computation_dao') as mock_comp_dao:
                    # Set up mocks
                    mock_dao.find_by_id.return_value = Mock(
                        generation_id=99999,
                        user_request="Performance test",
                        state="running"
                    )
                    mock_dao.find_branches_by_dynamic_generation_id.return_value = []
                    mock_comp_dao.find_retry_process_by_node_id.return_value = []
                    
                    # Measure the response time
                    start_time = time.time()
                    result = service.get_full_task_interactions(99999)
                    end_time = time.time()
                    
                    response_time = end_time - start_time
                    
                    # Verify the response time is within a reasonable range
                    assert response_time < 5.0, f"Large-dataset response time too long: {response_time}s"
                    assert "error" not in result
                    assert result["total_count"] == performance_test_data["node_count"]

    def test_concurrent_api_requests(self, service):
        """Test concurrent API request performance"""
        def make_request(generation_id):
            with patch.multiple(
                service,
                _get_nodes_in_generation_path=Mock(return_value=[1, 2, 3]),
                _get_dynamic_generation_interaction=Mock(return_value={
                    "type": "dynamic_generation",
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "node_id": 1
                })
            ):
                with patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao') as mock_dao:
                    with patch('server.service.dynamic_generation_llm_monitor.computation_dao') as mock_comp_dao:
                        mock_dao.find_by_id.return_value = Mock(
                            generation_id=generation_id,
                            user_request="Concurrency test",
                            state="running"
                        )
                        mock_dao.find_branches_by_dynamic_generation_id.return_value = []
                        mock_comp_dao.find_retry_process_by_node_id.return_value = []
                        
                        return service.get_full_task_interactions(generation_id)

        # Execute 10 requests concurrently
        concurrent_requests = 10
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [
                executor.submit(make_request, i) 
                for i in range(concurrent_requests)
            ]
            
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all requests succeeded
        assert len(results) == concurrent_requests
        for result in results:
            assert "error" not in result
        
        # Verify concurrent performance (average under 1 second per request)
        avg_response_time = total_time / concurrent_requests
        assert avg_response_time < 1.0, f"Average concurrent request response time too long: {avg_response_time}s"

    def test_memory_usage_with_large_interactions(self, service):
        """Test memory usage with a large amount of interaction data"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create a large amount of mock interaction data
        large_interaction = {
            "type": "dynamic_generation",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "node_id": 1,
            "input": {"prompt": "x" * 10000},  # 10KB of mock data
            "output": {"response": "y" * 10000}  # 10KB of mock data
        }
        
        with patch.multiple(
            service,
            _get_nodes_in_generation_path=Mock(return_value=list(range(1, 501))),  # 500 nodes
            _get_dynamic_generation_interaction=Mock(return_value=large_interaction)
        ):
            with patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao') as mock_dao:
                with patch('server.service.dynamic_generation_llm_monitor.computation_dao') as mock_comp_dao:
                    mock_dao.find_by_id.return_value = Mock(
                        generation_id=88888,
                        user_request="Memory test",
                        state="running"
                    )
                    mock_dao.find_branches_by_dynamic_generation_id.return_value = []
                    mock_comp_dao.find_retry_process_by_node_id.return_value = []
                    
                    # Perform the operation
                    result = service.get_full_task_interactions(88888)
                    
                    # Check memory usage
                    final_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_increase = final_memory - initial_memory
                    
                    # Verify the result
                    assert "error" not in result
                    assert result["total_count"] == 500
                    
                    # Verify memory growth is within a reasonable range (under 100MB)
                    assert memory_increase < 100, f"Memory growth too large: {memory_increase}MB"

    def test_s3_access_timeout_handling(self, service):
        """Test handling of S3 access timeouts"""
        def slow_s3_access(*args, **kwargs):
            time.sleep(3)  # Simulate slow S3 access
            return ("slow data", "slow response")
        
        with patch('server.service.dynamic_generation_llm_monitor.DynamicGenerationWaiter') as mock_waiter_class:
            mock_waiter = Mock()
            mock_waiter_class.return_value = mock_waiter
            mock_waiter.fetch_log.side_effect = slow_s3_access
            
            # Measure timeout handling
            start_time = time.time()
            result = service._get_dynamic_generation_interaction(123, 100)
            end_time = time.time()
            
            # The real implementation should have a timeout mechanism
            # Here we verify the operation at least completes without crashing
            response_time = end_time - start_time
            
            # If there is no timeout mechanism, this test reminds us to add one
            print(f"S3 access time: {response_time}s")


class TestDataConsistency:
    """Data consistency tests"""

    @pytest.fixture
    def service(self):
        return DynamicGenerationLLMMonitorService()

    def test_interaction_timestamp_ordering(self, service):
        """Test correctness of interaction timestamp ordering"""
        # Create out-of-order timestamp data
        interactions = [
            {"type": "dynamic_generation", "timestamp": 1640995300000, "node_id": 3},
            {"type": "bug_fixer", "timestamp": 1640995100000, "node_id": 1},
            {"type": "dynamic_generation", "timestamp": 1640995200000, "node_id": 2},
            {"type": "bug_fixer", "timestamp": None, "node_id": 4},  # case with no timestamp
            {"type": "dynamic_generation", "timestamp": 1640995050000, "node_id": 0},
        ]
        
        # Simulate the sorting logic
        interactions.sort(key=lambda x: x.get('timestamp', 0) or 0)
        
        # Verify the sort result
        expected_order = [4, 0, 1, 2, 3]  # in node_id order, since that corresponds to chronological order
        actual_order = [x['node_id'] for x in interactions]
        assert actual_order == expected_order

    def test_branch_node_path_consistency(self, service):
        """Test consistency of branch node paths"""
        with patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao') as mock_dg_dao:
            with patch('server.service.dynamic_generation_llm_monitor.edge_dao') as mock_edge_dao:
                # Set up a consistent node path: 100 -> 200 -> 300
                mock_dg_dao.find_by_id.return_value = Mock(previous_node_id=100)
                
                mock_edge_dao.find_by_target_node_id.side_effect = [
                    [Mock(source_node_id=200)],  # predecessor of 300 is 200
                    [Mock(source_node_id=100)],  # predecessor of 200 is 100
                    []  # 100 has no predecessor
                ]
                
                result = service._get_nodes_in_generation_path(123, 300)
                
                # Verify path continuity and correctness
                assert result == [100, 200, 300]
                
                # Verify the call order
                expected_calls = [((300,),), ((200,),), ((100,),)]
                actual_calls = mock_edge_dao.find_by_target_node_id.call_args_list
                assert actual_calls == expected_calls


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
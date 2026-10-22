"""
Performance and scalability tests for omicairn-worker.
Tests system performance under various load conditions and scenarios.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# Import classes under test
from handle_dynamic_generation.llm_interface import LlmInterface as DynamicLlmInterface
from handle_job_feedback.llm_interface import LlmInterface as JobFeedbackLlmInterface
from server.service.task import task_service


class TestPerformanceScenarios:
    """Test performance under various load scenarios."""
    
    def test_concurrent_dynamic_generation_requests(self, mock_requests, mock_logger):
        """Test handling multiple concurrent dynamic generation requests."""
        # Setup mock responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "function_block": "def test_function(): return 'success'",
                "code": 200,
                "message": "Success"
            }
        }
        mock_requests['post'].return_value = mock_response
        
        def make_request(request_id):
            """Make a single request and measure response time."""
            start_time = time.time()
            
            llm_interface = DynamicLlmInterface()
            response = llm_interface.dynamic_fb(
                user_request=f"Create function {request_id}",
                node_id=f"node_{request_id}",
                history=[{"node": {"id": f"node_{request_id}"}, "latestComputation": {"id": f"comp_{request_id}"}}],
                user_id=f"user_{request_id}",
                llm_model="gpt-4o"
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == 200
            }
        
        # Execute concurrent requests
        num_requests = 10
        results = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        successful_requests = [r for r in results if r['success']]
        response_times = [r['response_time'] for r in results]
        
        # Assertions
        assert len(successful_requests) == num_requests, "All requests should succeed"
        assert max(response_times) < 5.0, "Max response time should be under 5 seconds"
        assert sum(response_times) / len(response_times) < 1.0, "Average response time should be under 1 second"
        
        # Verify all requests were made
        assert mock_requests['post'].call_count == num_requests

    def test_large_dataset_processing_performance(self, mock_requests, mock_logger):
        """Test performance with large dataset processing requests."""
        # Mock response for large data processing
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "function_block": "import pandas as pd\ndef process_large_dataset(df):\n    return df.describe()",
                "code": 200,
                "message": "Success"
            }
        }
        mock_requests['post'].return_value = mock_response
        
        # Simulate processing request for large dataset
        large_history = []
        for i in range(100):  # Large history with many nodes
            large_history.append({
                "node": {
                    "id": f"node_{i}",
                    "name": f"Processing Node {i}",
                    "data_size": "10GB",
                    "processing_time": random.randint(30, 300)
                },
                "latestComputation": {
                    "id": f"comp_{i}",
                    "status": "completed",
                    "memory_usage": f"{random.randint(1, 8)}GB",
                    "cpu_usage": f"{random.randint(10, 90)}%"
                }
            })
        
        start_time = time.time()
        
        llm_interface = DynamicLlmInterface()
        response = llm_interface.dynamic_fb(
            user_request="Process this large genomic dataset with RNA-seq analysis pipeline",
            node_id="large_processing_node",
            history=large_history,
            user_id="researcher_123",
            llm_model="gpt-4o"
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Performance assertions
        assert response.status_code == 200
        assert processing_time < 10.0, "Large dataset processing should complete within 10 seconds"
        
        # Verify request was made with large history
        call_args = mock_requests['post'].call_args
        request_body = call_args[1]['json']
        assert len(request_body['nodeHistoryList']) == 100

    def test_memory_usage_under_load(self, mock_requests, mock_logger):
        """Test memory usage during intensive operations."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"function_block": "def test(): return True"}
        }
        mock_requests['post'].return_value = mock_response
        
        # Perform memory-intensive operations
        llm_interface = DynamicLlmInterface()
        
        for i in range(50):
            # Create large mock data structures
            large_history = [
                {
                    "node": {"id": f"node_{j}", "data": "x" * 1000},
                    "latestComputation": {"id": f"comp_{j}", "result": "y" * 1000}
                }
                for j in range(20)
            ]
            
            response = llm_interface.dynamic_fb(
                user_request=f"Process batch {i}",
                node_id=f"batch_node_{i}",
                history=large_history,
                user_id="performance_test_user",
                llm_model="gpt-4o"
            )
            
            assert response.status_code == 200
        
        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory should not increase dramatically (allowing for some growth)
        assert memory_increase < 100 * 1024 * 1024, "Memory increase should be less than 100MB"

    def test_database_query_performance(self, mock_database_globally, mock_logger):
        """Test database query performance under load."""
        from server.dao.node import node_dao
        from server.dao.task import task_dao
        
        with patch('server.dao.node.session') as mock_session:
            # Mock database query results
            mock_nodes = [
                Mock(id=f"node_{i}", name=f"Node {i}", state="running")
                for i in range(1000)
            ]
            mock_session.query.return_value.filter.return_value.all.return_value = mock_nodes
            
            # Time multiple database queries
            start_time = time.time()
            
            for batch in range(10):
                node_ids = [f"node_{i}" for i in range(batch * 100, (batch + 1) * 100)]
                results = node_dao.find_by_ids(node_ids)
                assert len(results) == 1000  # Mock returns all nodes regardless
            
            end_time = time.time()
            total_query_time = end_time - start_time
            
            # Performance assertion
            assert total_query_time < 2.0, "10 batch queries should complete within 2 seconds"
            assert mock_session.query.call_count == 10


class TestScalabilityTests:
    """Test system scalability and limits."""
    
    def test_maximum_concurrent_users(self, mock_requests, mock_logger):
        """Test system behavior with maximum concurrent users."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "success"}
        mock_requests['post'].return_value = mock_response
        
        def simulate_user_session(user_id):
            """Simulate a complete user session with multiple requests."""
            llm_interface = DynamicLlmInterface()
            
            # User makes multiple requests in their session
            requests_per_user = 5
            for request_num in range(requests_per_user):
                response = llm_interface.dynamic_fb(
                    user_request=f"User {user_id} request {request_num}",
                    node_id=f"node_{user_id}_{request_num}",
                    history=[{"node": {"id": f"node_{user_id}"}, "latestComputation": {"id": f"comp_{user_id}"}}],
                    user_id=f"user_{user_id}",
                    llm_model="gpt-4o"
                )
                assert response.status_code == 200
            
            return user_id
        
        # Simulate maximum concurrent users (50 users)
        max_concurrent_users = 50
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(simulate_user_session, user_id)
                for user_id in range(max_concurrent_users)
            ]
            
            completed_users = []
            for future in as_completed(futures):
                completed_users.append(future.result())
        
        # All users should complete successfully
        assert len(completed_users) == max_concurrent_users
        
        # Verify total requests made (50 users * 5 requests each)
        expected_total_requests = max_concurrent_users * 5
        assert mock_requests['post'].call_count == expected_total_requests

    def test_large_workflow_processing(self, mock_requests, mock_logger):
        """Test processing of large, complex workflows."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "function_block": "def complex_analysis(): pass",
                "code": 200
            }
        }
        mock_requests['post'].return_value = mock_response
        
        # Create a complex workflow with many interconnected nodes
        num_nodes = 200
        complex_history = []
        
        for i in range(num_nodes):
            node_data = {
                "node": {
                    "id": f"workflow_node_{i}",
                    "name": f"Analysis Step {i}",
                    "node_type": "computation" if i % 2 == 0 else "data_processing",
                    "dependencies": [f"workflow_node_{j}" for j in range(max(0, i-3), i)],
                    "processing_time": random.randint(10, 120),
                    "memory_requirement": f"{random.randint(1, 16)}GB"
                },
                "latestComputation": {
                    "id": f"workflow_comp_{i}",
                    "status": "completed",
                    "result_size": f"{random.randint(100, 5000)}MB",
                    "computation_time": random.randint(30, 600)
                }
            }
            complex_history.append(node_data)
        
        start_time = time.time()
        
        llm_interface = DynamicLlmInterface()
        response = llm_interface.create_workflow_report(
            node_ids=[f"workflow_node_{i}" for i in range(num_nodes)],
            computation_details_list=[
                {
                    "node_id": f"workflow_node_{i}",
                    "status": "completed",
                    "result": "success",
                    "processing_time": random.randint(30, 600)
                }
                for i in range(num_nodes)
            ],
            analysis_id="large_workflow_analysis",
            uuid_str="large_workflow_uuid",
            user_id="workflow_researcher"
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Performance assertions
        assert response.status_code == 200
        assert processing_time < 15.0, "Large workflow processing should complete within 15 seconds"
        
        # Verify the request handled large data
        call_args = mock_requests['get'].call_args
        request_body = call_args[1]['json']
        assert len(request_body['nodeIDs']) == num_nodes

    def test_stress_test_task_service(self, mock_database_globally, mock_logger):
        """Stress test the task service with rapid task creation."""
        with patch('server.service.task.task_dao') as mock_task_dao, \
             patch('server.service.task.task_node_relation_dao') as mock_task_node_dao, \
             patch('server.service.task.task_edge_relation_dao') as mock_task_edge_dao, \
             patch('server.service.task.ComputationLauncher') as mock_launcher:
            
            # Mock DAO responses
            def create_mock_task(task_data):
                return Mock(id=f"task_{random.randint(1000, 9999)}", **task_data)
            
            mock_task_dao.create.side_effect = create_mock_task
            mock_launcher_instance = Mock()
            mock_launcher.return_value = mock_launcher_instance
            
            # Rapidly create many tasks
            num_tasks = 100
            start_time = time.time()
            
            created_tasks = []
            for i in range(num_tasks):
                task = task_service.create(
                    analysis_id=f"stress_analysis_{i}",
                    node_id_list=list(range(i * 5, (i + 1) * 5)),  # 5 nodes per task
                    edge_id_list=list(range(i * 3, (i + 1) * 3)),  # 3 edges per task
                    user_id=f"stress_user_{i % 10}"  # 10 different users
                )
                created_tasks.append(task)
            
            end_time = time.time()
            creation_time = end_time - start_time
            
            # Performance assertions
            assert len(created_tasks) == num_tasks
            assert creation_time < 5.0, "Creating 100 tasks should take less than 5 seconds"
            
            # Verify DAO interactions
            assert mock_task_dao.create.call_count == num_tasks
            assert mock_task_node_dao.create.call_count == num_tasks * 5  # 5 nodes per task
            assert mock_task_edge_dao.create.call_count == num_tasks * 3  # 3 edges per task


class TestResourceUtilizationTests:
    """Test resource utilization and limits."""
    
    def test_cpu_intensive_operations(self, mock_requests, mock_logger):
        """Test CPU-intensive operations performance."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "cpu_intensive_result"}
        mock_requests['post'].return_value = mock_response
        
        def cpu_intensive_task(task_id):
            """Simulate CPU-intensive processing."""
            # Simulate complex computation (matrix multiplication)
            import numpy as np
            
            # Create large matrices for computation
            size = 100
            matrix1 = np.random.rand(size, size)
            matrix2 = np.random.rand(size, size)
            
            start_time = time.time()
            
            # Perform multiple matrix multiplications
            for _ in range(10):
                result = np.dot(matrix1, matrix2)
                matrix1 = result
            
            # Also make API call during computation
            llm_interface = DynamicLlmInterface()
            response = llm_interface.dynamic_fb(
                user_request=f"CPU intensive task {task_id}",
                node_id=f"cpu_node_{task_id}",
                history=[{"node": {"id": f"cpu_node_{task_id}"}, "latestComputation": {"id": f"cpu_comp_{task_id}"}}],
                user_id=f"cpu_user_{task_id}",
                llm_model="gpt-4o"
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            return {
                "task_id": task_id,
                "processing_time": processing_time,
                "api_status": response.status_code,
                "result_shape": result.shape
            }
        
        # Run multiple CPU-intensive tasks concurrently
        num_cpu_tasks = 5
        
        with ThreadPoolExecutor(max_workers=num_cpu_tasks) as executor:
            futures = [executor.submit(cpu_intensive_task, i) for i in range(num_cpu_tasks)]
            results = [future.result() for future in as_completed(futures)]
        
        # Verify all tasks completed successfully
        assert len(results) == num_cpu_tasks
        for result in results:
            assert result['api_status'] == 200
            assert result['processing_time'] < 30.0, "CPU intensive task should complete within 30 seconds"
            assert result['result_shape'] == (100, 100), "Matrix computation should maintain shape"

    def test_network_latency_simulation(self, mock_requests, mock_logger):
        """Test system behavior under network latency conditions."""
        def slow_response():
            """Simulate slow network response."""
            time.sleep(random.uniform(1.0, 3.0))  # Random latency 1-3 seconds
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": "delayed_response"}
            return mock_response
        
        mock_requests['post'].side_effect = lambda *args, **kwargs: slow_response()
        
        # Measure response times with latency
        response_times = []
        num_requests = 10
        
        llm_interface = DynamicLlmInterface()
        
        for i in range(num_requests):
            start_time = time.time()
            
            response = llm_interface.dynamic_fb(
                user_request=f"Latency test {i}",
                node_id=f"latency_node_{i}",
                history=[{"node": {"id": f"node_{i}"}, "latestComputation": {"id": f"comp_{i}"}}],
                user_id=f"latency_user_{i}",
                llm_model="gpt-4o"
            )
            
            end_time = time.time()
            response_times.append(end_time - start_time)
            
            assert response.status_code == 200
        
        # Analyze response times under latency
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        # Should handle latency gracefully (within expected range)
        assert 1.0 <= avg_response_time <= 4.0, "Average response time should be within latency range"
        assert max_response_time < 5.0, "Maximum response time should not exceed 5 seconds"

    def test_error_rate_under_load(self, mock_requests, mock_logger):
        """Test error handling and recovery under high load."""
        call_count = 0
        
        def intermittent_failure():
            """Simulate intermittent failures (20% failure rate)."""
            nonlocal call_count
            call_count += 1
            
            if call_count % 5 == 0:  # Every 5th request fails
                mock_response = Mock()
                mock_response.status_code = 500
                mock_response.json.return_value = {"error": "Temporary server error"}
                return mock_response
            else:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"data": "success"}
                return mock_response
        
        mock_requests['post'].side_effect = lambda *args, **kwargs: intermittent_failure()
        
        # Make many requests and track success/failure rates
        num_requests = 50
        success_count = 0
        failure_count = 0
        
        llm_interface = DynamicLlmInterface()
        
        for i in range(num_requests):
            try:
                response = llm_interface.dynamic_fb(
                    user_request=f"Load test {i}",
                    node_id=f"load_node_{i}",
                    history=[{"node": {"id": f"node_{i}"}, "latestComputation": {"id": f"comp_{i}"}}],
                    user_id=f"load_user_{i}",
                    llm_model="gpt-4o"
                )
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                failure_count += 1
        
        # Verify expected success/failure rates
        success_rate = success_count / num_requests
        failure_rate = failure_count / num_requests
        
        assert 0.7 <= success_rate <= 0.9, f"Success rate should be ~80%, got {success_rate}"
        assert 0.1 <= failure_rate <= 0.3, f"Failure rate should be ~20%, got {failure_rate}"
        assert success_count + failure_count == num_requests, "All requests should be accounted for"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
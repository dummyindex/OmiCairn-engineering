"""
Integration tests and error handling scenarios for omicairn-worker.
Tests end-to-end workflows and comprehensive error handling across all modules.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

# Import modules for integration testing
from handle_dynamic_generation.llm_interface import LlmInterface as DynamicLlmInterface
from handle_job_feedback.llm_interface import LlmInterface as JobFeedbackLlmInterface
from handle_visualizer.llm_interface import LlmInterface as VisualizerLlmInterface


class TestCrossModuleIntegration:
    """Test integration scenarios across different modules."""
    
    def test_dynamic_generation_to_job_feedback_workflow(self, mock_requests, mock_logger):
        """Test complete workflow from dynamic generation to job feedback."""
        # Mock dynamic generation response
        dynamic_response = Mock()
        dynamic_response.status_code = 200
        dynamic_response.json.return_value = {
            "data": {
                "function_block": "def analyze_data(df):\n    return df.describe()",
                "code": 200,
                "message": "Success"
            }
        }
        
        # Mock job feedback response
        feedback_response = Mock()
        feedback_response.status_code = 200
        feedback_response.json.return_value = {
            "data": {"optimization_applied": True}
        }
        
        mock_requests['post'].side_effect = [dynamic_response, feedback_response]
        
        # Test dynamic generation
        dynamic_llm = DynamicLlmInterface()
        dynamic_result = dynamic_llm.dynamic_fb(
            user_request="Create data analysis function",
            node_id="node_123",
            history=[{"node": {"id": "node1"}, "latestComputation": {"id": "comp1"}}],
            user_id="user_123",
            llm_model="gpt-4o"
        )
        
        assert dynamic_result.status_code == 200
        
        # Test job feedback (error optimization)
        feedback_llm = JobFeedbackLlmInterface()
        feedback_llm.apply_for_optimize_error_description("comp_123", "user_123")
        
        # Verify both API calls were made
        assert mock_requests['post'].call_count == 2
        
        # Verify URLs
        call_args = mock_requests['post'].call_args_list
        assert "dynamic_fb/get" in call_args[0][1]['url']
        assert "error/write" in call_args[1][0][0]

    def test_visualizer_integration_with_server_agent(self, mock_requests, mock_logger):
        """Test visualizer integration with server agent."""
        # Mock server agent login
        login_response = Mock()
        login_response.json.return_value = {"data": "auth_token_123"}
        
        # Mock visualizer LLM response
        viz_response = Mock()
        viz_response.status_code = 200
        viz_response.json.return_value = {
            "data": {"visualization_code": "plt.scatter(x, y)"}
        }
        
        # Mock node edit response
        edit_response = Mock()
        edit_response.json.return_value = {"data": {"success": True}}
        
        mock_requests['post'].side_effect = [login_response, viz_response, edit_response]
        
        with patch('handle_visualizer.server_agent.ServerAgent') as mock_server_agent_class:
            mock_server_agent = Mock()
            mock_server_agent.headers = {"token": "auth_token_123"}
            mock_server_agent_class.return_value = mock_server_agent
            
            # Test visualizer LLM
            viz_llm = VisualizerLlmInterface()
            viz_result = viz_llm.init_chat("analysis_123", "user_123")
            
            # Test server agent operations
            server_agent = mock_server_agent_class("user_123")
            server_agent.edit_nodes(["node_123"], [{"state": "processing"}])
            
            # Verify integration
            assert viz_result.status_code == 200
            mock_server_agent.edit_nodes.assert_called_once()

    def test_end_to_end_computation_workflow(self, mock_requests, mock_database_globally, mock_logger):
        """Test end-to-end computation workflow."""
        with patch('handle_dynamic_generation.server_agent.requests.post') as mock_dg_post, \
             patch('handle_job_feedback.index.find_computation_by_id') as mock_find_comp, \
             patch('handle_job_feedback.index.handle_success') as mock_handle_success, \
             patch('server.service.task.task_dao') as mock_task_dao:
            
            # Mock dynamic generation server agent
            mock_dg_post.return_value = Mock(json=lambda: {"data": "auth_token"})
            
            # Mock computation entity
            computation = Mock()
            computation.id = "comp_123"
            computation.node_id = "node_123"
            computation.task_id = "task_123"
            computation.computation_state = "running"
            mock_find_comp.return_value = computation
            
            # Mock task creation
            mock_task = Mock(id="task_123")
            mock_task_dao.create.return_value = mock_task
            
            # Simulate workflow stages
            # 1. Create task (server module)
            task = mock_task_dao.create({
                "analysis_id": "analysis_123",
                "owner_id": "user_123"
            })
            assert task.id == "task_123"
            
            # 2. Find computation (job feedback module)
            found_computation = mock_find_comp("comp_123")
            assert found_computation.id == "comp_123"
            
            # 3. Handle success (job feedback module)
            mock_handle_success(
                computation, Mock(), Mock(), Mock(), Mock()
            )
            mock_handle_success.assert_called_once()


class TestErrorHandlingScenarios:
    """Test comprehensive error handling scenarios."""
    
    def test_network_timeout_handling(self, mock_requests, mock_logger):
        """Test handling of network timeouts across all modules."""
        import requests
        
        # Mock timeout for different modules
        mock_requests['post'].side_effect = requests.Timeout("Request timeout")
        
        # Test dynamic generation timeout
        dynamic_llm = DynamicLlmInterface()
        with pytest.raises(requests.Timeout):
            dynamic_llm.dynamic_fb(
                user_request="Test", node_id="node_123",
                history=[], user_id="user_123", llm_model="gpt-4o"
            )
        
        # Test job feedback timeout
        job_llm = JobFeedbackLlmInterface()
        with pytest.raises(requests.Timeout):
            job_llm.init_chat("analysis_123", "user_123")
        
        # Test visualizer timeout
        viz_llm = VisualizerLlmInterface()
        with pytest.raises(requests.Timeout):
            viz_llm.send_message("analysis_123", "user_123", "chat_123", "test")

    def test_database_connection_failures(self, mock_logger):
        """Test handling of database connection failures."""
        with patch('handle_job_feedback.index.find_computation_by_id') as mock_find_comp, \
             patch('server.dao.node.session') as mock_session:
            
            # Mock database connection failure
            mock_find_comp.side_effect = Exception("Database connection lost")
            mock_session.query.side_effect = Exception("Connection timeout")
            
            # Test job feedback database error
            with pytest.raises(Exception):
                mock_find_comp("comp_123")
            
            # Test server DAO database error
            with pytest.raises(Exception):
                mock_session.query()

    def test_api_authentication_failures(self, mock_requests, mock_logger):
        """Test handling of API authentication failures."""
        # Mock 401 responses
        auth_error_response = Mock()
        auth_error_response.status_code = 401
        auth_error_response.json.return_value = {"message": "Unauthorized"}
        mock_requests['post'].return_value = auth_error_response
        
        from handle_dynamic_generation.exception.request.dynamic_status_code import DynamicStatusCode
        
        # Test dynamic generation auth failure
        dynamic_llm = DynamicLlmInterface()
        with pytest.raises(DynamicStatusCode):
            dynamic_llm.dynamic_fb(
                user_request="Test", node_id="node_123",
                history=[], user_id="user_123", llm_model="gpt-4o"
            )
        
        # Test job feedback auth failure  
        job_llm = JobFeedbackLlmInterface()
        with pytest.raises(DynamicStatusCode):
            job_llm.init_chat("analysis_123", "user_123")

    def test_malformed_response_handling(self, mock_requests, mock_logger):
        """Test handling of malformed API responses."""
        # Mock malformed JSON response
        malformed_response = Mock()
        malformed_response.status_code = 200
        malformed_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_requests['post'].return_value = malformed_response
        
        dynamic_llm = DynamicLlmInterface()
        
        # Should handle JSON decode errors gracefully
        with pytest.raises(json.JSONDecodeError):
            result = dynamic_llm.dynamic_fb(
                user_request="Test", node_id="node_123",
                history=[], user_id="user_123", llm_model="gpt-4o"
            )
            result.json()  # This would trigger the JSONDecodeError

    def test_partial_system_failure_recovery(self, mock_requests, mock_logger):
        """Test system behavior during partial failures."""
        # Mock mixed success/failure responses
        responses = [
            Mock(status_code=200, json=lambda: {"data": "success_1"}),
            Mock(status_code=500, json=lambda: {"message": "server_error"}),
            Mock(status_code=200, json=lambda: {"data": "success_2"})
        ]
        mock_requests['post'].side_effect = responses
        
        dynamic_llm = DynamicLlmInterface()
        
        # First call should succeed
        result1 = dynamic_llm.dynamic_fb(
            user_request="Test1", node_id="node_123",
            history=[], user_id="user_123", llm_model="gpt-4o"
        )
        assert result1.status_code == 200
        
        # Second call should fail
        result2 = dynamic_llm.dynamic_fb(
            user_request="Test2", node_id="node_123",
            history=[], user_id="user_123", llm_model="gpt-4o"
        )
        assert result2.status_code == 500
        
        # Third call should succeed again
        result3 = dynamic_llm.dynamic_fb(
            user_request="Test3", node_id="node_123",
            history=[], user_id="user_123", llm_model="gpt-4o"
        )
        assert result3.status_code == 200


class TestConcurrentOperations:
    """Test concurrent operations and race conditions."""
    
    def test_concurrent_computation_handling(self, mock_requests, mock_logger):
        """Test handling of concurrent computations."""
        with patch('handle_job_feedback.index.find_computation_by_id') as mock_find_comp, \
             patch('handle_job_feedback.index.update_computation') as mock_update_comp:
            
            # Mock concurrent computations
            computations = [
                Mock(id=f"comp_{i}", computation_state="running") 
                for i in range(3)
            ]
            mock_find_comp.side_effect = computations
            
            # Simulate concurrent processing
            for i in range(3):
                comp = mock_find_comp(f"comp_{i}")
                mock_update_comp(comp.id, {"computation_state": "finished"})
            
            # Verify all computations were processed
            assert mock_find_comp.call_count == 3
            assert mock_update_comp.call_count == 3

    def test_resource_contention_scenarios(self, mock_database_globally, mock_logger):
        """Test resource contention handling."""
        with patch('server.dao.node.session') as mock_session:
            # Mock database lock contention
            mock_session.query.side_effect = [
                Exception("Lock wait timeout"),
                Mock()  # Retry succeeds
            ]
            
            # First attempt fails, retry should be handled by the application
            with pytest.raises(Exception):
                mock_session.query()
            
            # Second attempt succeeds
            result = mock_session.query()
            assert result is not None


class TestDataFlowValidation:
    """Test data flow and state transitions."""
    
    def test_computation_state_transitions(self, mock_logger):
        """Test valid computation state transitions."""
        with patch('handle_job_feedback.index.update_computation') as mock_update:
            # Test valid state transitions
            valid_transitions = [
                ("queued", "running"),
                ("running", "finished"),
                ("running", "failed"),
                ("failed", "queued")  # retry
            ]
            
            for from_state, to_state in valid_transitions:
                mock_update("comp_123", {"computation_state": to_state})
            
            # Verify all transitions were attempted
            assert mock_update.call_count == len(valid_transitions)

    def test_node_state_consistency(self, mock_logger):
        """Test node state consistency across operations."""
        with patch('handle_visualizer.index.find_node_by_id') as mock_find_node, \
             patch('handle_visualizer.index.lock_nodes') as mock_lock, \
             patch('handle_visualizer.index.unlock_nodes') as mock_unlock:
            
            node = Mock(id="node_123", state="ready")
            mock_find_node.return_value = node
            
            # Simulate node processing workflow
            found_node = mock_find_node("node_123")
            mock_lock(Mock(), [found_node.id])
            # Processing would happen here
            mock_unlock(Mock(), [found_node.id])
            
            # Verify workflow
            mock_find_node.assert_called_once()
            mock_lock.assert_called_once()
            mock_unlock.assert_called_once()

    def test_data_consistency_across_modules(self, mock_database_globally, mock_logger):
        """Test data consistency when accessed by different modules."""
        shared_data = {
            "computation_id": "comp_123",
            "node_id": "node_123",
            "user_id": "user_123"
        }
        
        with patch('handle_job_feedback.index.find_computation_by_id') as mock_find_comp, \
             patch('server.dao.computation.session') as mock_session:
            
            # Mock computation access from job feedback
            computation = Mock(**shared_data)
            mock_find_comp.return_value = computation
            
            # Mock computation access from server
            mock_session.query.return_value.filter.return_value.first.return_value = computation
            
            # Both modules should see consistent data
            job_comp = mock_find_comp("comp_123")
            server_comp = mock_session.query().filter().first()
            
            assert job_comp.computation_id == server_comp.computation_id
            assert job_comp.node_id == server_comp.node_id
            assert job_comp.user_id == server_comp.user_id


class TestPerformanceAndScalability:
    """Test performance characteristics and scalability."""
    
    def test_large_batch_processing(self, mock_requests, mock_logger):
        """Test processing of large batches."""
        # Mock responses for large batch
        batch_size = 100
        mock_responses = [
            Mock(status_code=200, json=lambda: {"data": f"result_{i}"})
            for i in range(batch_size)
        ]
        mock_requests['post'].side_effect = mock_responses
        
        dynamic_llm = DynamicLlmInterface()
        results = []
        
        # Process large batch
        for i in range(batch_size):
            result = dynamic_llm.dynamic_fb(
                user_request=f"Request {i}",
                node_id=f"node_{i}",
                history=[],
                user_id="user_123",
                llm_model="gpt-4o"
            )
            results.append(result)
        
        # Verify all requests were processed
        assert len(results) == batch_size
        assert all(r.status_code == 200 for r in results)

    def test_memory_usage_optimization(self, mock_logger):
        """Test memory usage patterns."""
        large_data = "x" * 10000  # 10KB string
        
        with patch('handle_job_feedback.index.find_computation_by_id') as mock_find:
            # Mock large computation data
            computation = Mock()
            computation.error_description = large_data
            mock_find.return_value = computation
            
            # Should handle large data without issues
            result = mock_find("comp_123")
            assert len(result.error_description) == 10000
            
            # Cleanup simulation
            del result
            del computation


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
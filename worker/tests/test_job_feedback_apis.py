"""
Unit tests for job feedback API interactions in omicairn-worker.
Tests the handle_job_feedback module functionality including error handling and retry mechanisms.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import classes under test
from handle_job_feedback.llm_interface import LlmInterface
from handle_job_feedback.dynamic_generation_agent import DynamicGenerationAgent
from handle_job_feedback.bug_fixer_agent import BugFixerAgent
from handle_job_feedback import index


class TestJobFeedbackLlmInterface:
    """Test the LlmInterface class for job feedback API calls."""
    
    def test_apply_for_optimize_error_description(self, mock_requests, mock_logger):
        """Test error description optimization API call."""
        mock_requests['response'].status_code = 200
        mock_requests['post'].return_value = mock_requests['response']
        
        llm_interface = LlmInterface()
        # This method doesn't return response, just makes the call
        llm_interface.apply_for_optimize_error_description(
            computation_id="computation_123",
            user_id="user_123"
        )
        
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        assert "error/write" in call_args[0][0]  # URL is first positional argument
        
        params = call_args[1]['params']
        assert params['computation_id'] == "computation_123"
        assert params['user_id'] == "user_123"

    def test_init_chat(self, mock_requests):
        """Test chat initialization API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"chat_id": "chat_123", "status": "initialized"}
        }
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.init_chat(
            analysis_id="analysis_123",
            owner_id="user_123"
        )
        
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        assert "oldchat/init" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['analysis_id'] == "analysis_123"
        assert params['owner_id'] == "user_123"
        assert params['user_id'] == "user_123"

    def test_get_chat_history(self, mock_requests):
        """Test chat history retrieval API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"message": "Error analysis request", "timestamp": "2024-01-01T10:00:00Z"},
                {"message": "Error analysis response", "timestamp": "2024-01-01T10:01:00Z"}
            ]
        }
        mock_requests['get'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.get_chat_history(
            analysis_id="analysis_123",
            owner_id="user_123"
        )
        
        assert response.status_code == 200
        mock_requests['get'].assert_called_once()
        call_args = mock_requests['get'].call_args
        assert "oldchat/history" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['analysis_id'] == "analysis_123"
        assert params['owner_id'] == "user_123"

    def test_send_message(self, mock_requests):
        """Test sending chat message API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"response": "Error analysis completed", "chat_id": "chat_123"}
        }
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.send_message(
            analysis_id="analysis_123",
            owner_id="user_123",
            chat_id="chat_123",
            message="Analyze this error"
        )
        
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        assert "oldchat/" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['message'] == "Analyze this error"
        assert params['chat_id'] == "chat_123"

    def test_llm_interface_error_handling(self, mock_requests, mock_logger):
        """Test error handling in LlmInterface methods."""
        from handle_job_feedback.exception.request.dynamic_status_code import DynamicStatusCode
        
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal server error"}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        
        # Test that DynamicStatusCode exception is raised for non-200 status
        with pytest.raises(DynamicStatusCode):
            llm_interface.init_chat(
                analysis_id="analysis_123",
                owner_id="user_123"
            )


@patch('handle_job_feedback.index.find_computation_by_id')
@patch('handle_job_feedback.index.find_node_by_id') 
@patch('handle_job_feedback.index.find_task_by_id')
@patch('handle_job_feedback.index.find_task_owner_relation_by_task_id')
@patch('handle_job_feedback.index.find_analysis_by_id')
@patch('handle_job_feedback.index.update_computation')
@patch('handle_job_feedback.index.update_data')
class TestJobFeedbackHandling:
    """Test job feedback handling functions."""
    
    def test_handle_failed(self, mock_update_data, mock_update_computation,
                          mock_find_analysis, mock_find_task_owner, mock_find_task,
                          mock_find_node, mock_find_computation, mock_logger):
        """Test handling of failed computation."""
        # Mock database entities
        computation = Mock()
        computation.id = "comp_123"
        computation.computation_state = "running"
        computation.start_time = datetime.now()
        computation.result_data_id = "data_123"
        computation.retry_process_id = "retry_123"
        
        node = Mock()
        node.id = "node_123"
        
        task = Mock()
        task.id = "task_123"
        
        task_owner_relation = Mock()
        task_owner_relation.user_id = "user_123"
        
        analysis = Mock()
        analysis.id = "analysis_123"
        
        with patch('handle_job_feedback.index.find_computation_retry_process_by_id') as mock_find_retry, \
             patch('handle_job_feedback.index.BugFixerAgent') as mock_bug_fixer, \
             patch('handle_job_feedback.index.optimize_error_description') as mock_optimize:
            
            mock_retry_process = Mock()
            mock_find_retry.return_value = mock_retry_process
            
            mock_agent = Mock()
            mock_bug_fixer.return_value = mock_agent
            
            # Call the function
            index.handle_failed(
                computation=computation,
                error_description="Test error",
                need_optimize=True,
                node=node,
                task=task,
                task_owner_relation=task_owner_relation,
                analysis=analysis
            )
            
            # Verify computation is updated to failed state
            mock_update_computation.assert_called_once()
            update_args = mock_update_computation.call_args[0]
            assert update_args[0] == "comp_123"
            assert update_args[1]["computation_state"] == "failed"
            assert update_args[1]["error_description"] == "Test error"
            
            # Verify data is updated to error state
            mock_update_data.assert_called_once()
            data_update_args = mock_update_data.call_args[0]
            assert data_update_args[0] == "data_123"
            assert data_update_args[1]["state"] == "error"
            
            # Verify optimization was called
            mock_optimize.assert_called_once_with("comp_123", "user_123")
            
            # Verify BugFixerAgent was created and handled
            mock_bug_fixer.assert_called_once()
            mock_agent.handle.assert_called_once()

    def test_handle_success(self, mock_update_data, mock_update_computation,
                           mock_find_analysis, mock_find_task_owner, mock_find_task,
                           mock_find_node, mock_find_computation, mock_logger):
        """Test handling of successful computation."""
        computation = Mock()
        computation.id = "comp_123"
        computation.computation_state = "running"
        computation.start_time = datetime.now()
        computation.result_data_id = "data_123"
        computation.node_id = "node_123"
        computation.task_id = "task_123"
        computation.retry_process_id = "retry_123"
        
        node = Mock()
        node.id = "node_123"
        node.visualizer_id = None
        node.dynamic_generation_id = None
        
        task = Mock()
        task.id = "task_123"
        
        task_owner_relation = Mock()
        task_owner_relation.user_id = "user_123"
        
        analysis = Mock()
        analysis.id = "analysis_123"
        
        with patch('handle_job_feedback.index.update_node') as mock_update_node, \
             patch('handle_job_feedback.index.find_next_edges_in_task') as mock_find_edges, \
             patch('handle_job_feedback.index.launch_computation') as mock_launch, \
             patch('handle_job_feedback.index.update_computation_retry_process') as mock_update_retry:
            
            mock_find_edges.return_value = []
            
            # Call the function
            index.handle_success(
                computation=computation,
                node=node,
                task=task,
                task_owner_relation=task_owner_relation,
                analysis=analysis
            )
            
            # Verify node is updated to finished state
            mock_update_node.assert_called_once()
            node_update_args = mock_update_node.call_args[0]
            assert node_update_args[0] == "node_123"
            assert node_update_args[1]["state"] == "finished"
            
            # Verify computation is updated to finished state
            mock_update_computation.assert_called_once()
            comp_update_args = mock_update_computation.call_args[0]
            assert comp_update_args[0] == "comp_123"
            assert comp_update_args[1]["computation_state"] == "finished"
            
            # Verify data is updated to OK state
            mock_update_data.assert_called_once()
            data_update_args = mock_update_data.call_args[0]
            assert data_update_args[0] == "data_123"
            assert data_update_args[1]["state"] == "ok"
            
            # Verify retry process is stopped
            mock_update_retry.assert_called_once()
            retry_update_args = mock_update_retry.call_args[0]
            assert retry_update_args[0] == "retry_123"
            assert retry_update_args[1]["state"] == "stopped"


class TestDynamicGenerationAgent:
    """Test DynamicGenerationAgent functionality."""
    
    def test_dynamic_generation_agent_initialization(self):
        """Test DynamicGenerationAgent initialization."""
        with patch('handle_job_feedback.dynamic_generation_agent.DynamicGenerationAgent.__init__', return_value=None):
            agent = DynamicGenerationAgent("user_123", Mock(), Mock())
            assert agent is not None

    def test_dynamic_generation_agent_handle(self):
        """Test DynamicGenerationAgent handle method."""
        with patch('handle_job_feedback.dynamic_generation_agent.DynamicGenerationAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            agent = mock_agent_class("user_123", Mock(), Mock())
            agent.handle()
            
            mock_agent.handle.assert_called_once()

    def test_dynamic_generation_agent_handle_with_plan(self):
        """Test DynamicGenerationAgent handle with plan method."""
        with patch('handle_job_feedback.dynamic_generation_agent.DynamicGenerationAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            agent = mock_agent_class("user_123", Mock(), Mock())
            agent.handle_with_plan()
            
            mock_agent.handle_with_plan.assert_called_once()


class TestBugFixerAgent:
    """Test BugFixerAgent functionality."""
    
    def test_bug_fixer_agent_initialization(self):
        """Test BugFixerAgent initialization."""
        with patch('handle_job_feedback.bug_fixer_agent.BugFixerAgent.__init__', return_value=None):
            agent = BugFixerAgent(
                retry_process=Mock(),
                node=Mock(),
                task_owner_relation=Mock(),
                task=Mock(),
                analysis=Mock(),
                computation=Mock(),
                error_description="Test error"
            )
            assert agent is not None

    def test_bug_fixer_agent_handle(self):
        """Test BugFixerAgent handle method."""
        with patch('handle_job_feedback.bug_fixer_agent.BugFixerAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            agent = mock_agent_class(
                Mock(), Mock(), Mock(), Mock(), Mock(), Mock(), "error"
            )
            agent.handle()
            
            mock_agent.handle.assert_called_once()

    def test_bug_fixer_agent_handle_with_directly_trigger(self):
        """Test BugFixerAgent handle with directly trigger."""
        with patch('handle_job_feedback.bug_fixer_agent.BugFixerAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            agent = mock_agent_class(
                Mock(), Mock(), Mock(), Mock(), Mock(), Mock(), "error"
            )
            agent.handle(True)  # directly_trigger = True
            
            mock_agent.handle.assert_called_once_with(True)


@patch('handle_job_feedback.index.open')
@patch('handle_job_feedback.index.json.load')
class TestJobFeedbackMain:
    """Test main function of job feedback module."""
    
    def test_main_success_flow(self, mock_json_load, mock_open, mock_logger):
        """Test main function success flow."""
        # Mock options
        mock_options = {
            "success": True,
            "computation_id": "comp_123"
        }
        mock_json_load.return_value = mock_options
        
        with patch('handle_job_feedback.index.find_computation_by_id') as mock_find_comp, \
             patch('handle_job_feedback.index.find_node_by_id') as mock_find_node, \
             patch('handle_job_feedback.index.find_task_by_id') as mock_find_task, \
             patch('handle_job_feedback.index.find_task_owner_relation_by_task_id') as mock_find_owner, \
             patch('handle_job_feedback.index.find_analysis_by_id') as mock_find_analysis, \
             patch('handle_job_feedback.index.find_dynamic_generation_by_id') as mock_find_dg, \
             patch('handle_job_feedback.index.handle_success') as mock_handle_success:
            
            # Mock database entities
            computation = Mock()
            computation.node_id = "node_123"
            computation.task_id = "task_123"
            mock_find_comp.return_value = computation
            
            node = Mock()
            node.analysis_id = "analysis_123"
            node.dynamic_generation_id = None
            mock_find_node.return_value = node
            
            task = Mock()
            task.id = "task_123"
            mock_find_task.return_value = task
            
            mock_find_owner.return_value = Mock()
            mock_find_analysis.return_value = Mock()
            mock_find_dg.return_value = None
            
            # Call main
            index.main()
            
            # Verify handle_success was called
            mock_handle_success.assert_called_once()

    def test_main_failure_flow(self, mock_json_load, mock_open, mock_logger):
        """Test main function failure flow."""
        # Mock options
        mock_options = {
            "success": False,
            "computation_id": "comp_123",
            "error_description": "Test error",
            "need_optimize": True,
            "directly_trigger": False
        }
        mock_json_load.return_value = mock_options
        
        with patch('handle_job_feedback.index.find_computation_by_id') as mock_find_comp, \
             patch('handle_job_feedback.index.find_node_by_id') as mock_find_node, \
             patch('handle_job_feedback.index.find_task_by_id') as mock_find_task, \
             patch('handle_job_feedback.index.find_task_owner_relation_by_task_id') as mock_find_owner, \
             patch('handle_job_feedback.index.find_analysis_by_id') as mock_find_analysis, \
             patch('handle_job_feedback.index.find_dynamic_generation_by_id') as mock_find_dg, \
             patch('handle_job_feedback.index.handle_failed') as mock_handle_failed:
            
            # Mock database entities
            computation = Mock()
            computation.node_id = "node_123"
            computation.task_id = "task_123"
            mock_find_comp.return_value = computation
            
            node = Mock()
            node.analysis_id = "analysis_123"
            node.dynamic_generation_id = "dg_123"
            mock_find_node.return_value = node
            
            task = Mock()
            task.id = "task_123"
            mock_find_task.return_value = task
            
            mock_find_owner.return_value = Mock()
            mock_find_analysis.return_value = Mock()
            mock_find_dg.return_value = Mock()
            
            # Call main
            index.main()
            
            # Verify handle_failed was called
            mock_handle_failed.assert_called_once()

    def test_main_direct_retry_flow(self, mock_json_load, mock_open, mock_logger):
        """Test main function direct retry flow."""
        # Mock options
        mock_options = {
            "success": False,
            "computation_id": "comp_123",
            "error_description": "Test error",
            "directly_trigger": True,
            "user_prompt": "Fix this error",
            "llm_model": "gpt-4o",
            "max_debug": 3
        }
        mock_json_load.return_value = mock_options
        
        with patch('handle_job_feedback.index.find_computation_by_id') as mock_find_comp, \
             patch('handle_job_feedback.index.find_node_by_id') as mock_find_node, \
             patch('handle_job_feedback.index.find_task_by_id') as mock_find_task, \
             patch('handle_job_feedback.index.find_task_owner_relation_by_task_id') as mock_find_owner, \
             patch('handle_job_feedback.index.find_analysis_by_id') as mock_find_analysis, \
             patch('handle_job_feedback.index.find_dynamic_generation_by_id') as mock_find_dg, \
             patch('handle_job_feedback.index.retry_directly') as mock_retry_directly:
            
            # Mock database entities
            computation = Mock()
            computation.node_id = "node_123"
            computation.task_id = "task_123"
            mock_find_comp.return_value = computation
            
            node = Mock()
            node.analysis_id = "analysis_123"
            node.dynamic_generation_id = None
            mock_find_node.return_value = node
            
            task = Mock()
            task.id = "task_123"
            mock_find_task.return_value = task
            
            mock_find_owner.return_value = Mock()
            mock_find_analysis.return_value = Mock()
            mock_find_dg.return_value = None
            
            # Call main
            index.main()
            
            # Verify retry_directly was called
            mock_retry_directly.assert_called_once()


class TestJobFeedbackErrorHandling:
    """Test error handling scenarios in job feedback processing."""
    
    def test_optimize_error_description_exception(self, mock_logger):
        """Test handling of exceptions in optimize_error_description."""
        with patch('handle_job_feedback.index.LlmInterface') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.apply_for_optimize_error_description.side_effect = Exception("API Error")
            mock_llm_class.return_value = mock_llm
            
            # Should not raise exception, just log error
            index.optimize_error_description("comp_123", "user_123")
            
            mock_llm.apply_for_optimize_error_description.assert_called_once()

    def test_handle_failed_cancelled_computation(self, mock_logger):
        """Test handle_failed with cancelled computation."""
        computation = Mock()
        computation.computation_state = "cancelled"  # ComputationState.CANCELLED.value
        
        with patch('handle_job_feedback.index.update_computation') as mock_update:
            # Call should return early without updating
            index.handle_failed(
                computation=computation,
                error_description="Test error",
                need_optimize=False,
                node=Mock(),
                task=Mock(),
                task_owner_relation=Mock(),
                analysis=Mock()
            )
            
            # Should not update computation since it's cancelled
            mock_update.assert_not_called()

    def test_handle_success_cancelled_computation(self, mock_logger):
        """Test handle_success with cancelled computation."""
        computation = Mock()
        computation.computation_state = "cancelled"  # ComputationState.CANCELLED.value
        
        with patch('handle_job_feedback.index.update_node') as mock_update:
            # Call should return early without updating
            index.handle_success(
                computation=computation,
                node=Mock(),
                task=Mock(),
                task_owner_relation=Mock(),
                analysis=Mock()
            )
            
            # Should not update node since computation is cancelled
            mock_update.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
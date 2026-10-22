"""
Unit tests for server task controller endpoints.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestTaskController:
    """Test task controller API endpoints."""
    
    def test_task_previous_check_api_all_ready(self):
        """Test task previous check API when all nodes are ready."""
        with patch('server.controller.task.request') as mock_request, \
             patch('server.controller.task.task_service') as mock_task_service, \
             patch('server.controller.task.ResponseManager') as mock_response_manager:
            
            # Mock request data
            mock_request.get_json.return_value = {
                "node_id_list": ["node_1", "node_2", "node_3"]
            }
            
            # Mock service response - all nodes ready
            mock_check_result = {
                "all_ready": True,
                "ready_nodes": ["node_1", "node_2", "node_3"],
                "pending_nodes": []
            }
            mock_task_service.check_params.return_value = mock_check_result
            
            # Mock response manager
            mock_response_manager.new_success_response.return_value = {
                "code": 200,
                "data": mock_check_result
            }
            
            # Import and test
            from server.controller.task import TaskPreviousCheckAPI
            api = TaskPreviousCheckAPI()
            result = api.get()
            
            # Verify
            mock_task_service.check_params.assert_called_once_with(["node_1", "node_2", "node_3"])
            assert result["code"] == 200
            assert result["data"]["all_ready"] is True
    
    def test_task_previous_check_api_with_pending_nodes(self):
        """Test task previous check API when some nodes are pending."""
        with patch('server.controller.task.request') as mock_request, \
             patch('server.controller.task.task_service') as mock_task_service, \
             patch('server.controller.task.ResponseManager') as mock_response_manager:
            
            # Mock request data
            mock_request.get_json.return_value = {
                "node_id_list": ["node_1", "node_2", "node_3"]
            }
            
            # Mock service response - some nodes pending
            mock_check_result = {
                "all_ready": False,
                "ready_nodes": ["node_1"],
                "pending_nodes": ["node_2", "node_3"]
            }
            mock_task_service.check_params.return_value = mock_check_result
            
            # Mock response manager
            mock_response_manager.new_success_response.return_value = {
                "code": 200,
                "data": mock_check_result
            }
            
            # Import and test
            from server.controller.task import TaskPreviousCheckAPI
            api = TaskPreviousCheckAPI()
            result = api.get()
            
            # Verify
            assert result["data"]["all_ready"] is False
            assert len(result["data"]["pending_nodes"]) == 2
    
    def test_task_dispatch_api_success(self):
        """Test successful task dispatch."""
        with patch('server.controller.task.request') as mock_request, \
             patch('server.controller.task.task_service') as mock_task_service, \
             patch('server.controller.task.AuthorityGuardianFactory') as mock_guardian_factory, \
             patch('server.controller.task.ResponseManager') as mock_response_manager:
            
            # Mock request data
            mock_request.get_json.return_value = {
                "analysis_id": "123",
                "node_id_list": ["1", "2", "3"],
                "edge_id_list": ["10", "20"]
            }
            
            # Mock authority guardian
            mock_guardian = Mock()
            mock_guardian.get_user_id.return_value = "user_123"
            mock_guardian.check_authority.return_value = None  # Success, no exception
            mock_guardian_factory.get_authority_guardian.return_value = mock_guardian
            
            # Mock service response
            mock_task = {
                "task_id": "task_123",
                "analysis_id": "123",
                "status": "created",
                "created_at": datetime.now().isoformat()
            }
            mock_task_service.create.return_value = mock_task
            
            # Mock response manager
            mock_response_manager.new_success_response.return_value = {
                "code": 200,
                "data": mock_task
            }
            
            # Import and test
            from server.controller.task import TaskDispatchAPI
            api = TaskDispatchAPI()
            result = api.post()
            
            # Verify authority check
            mock_guardian.check_authority.assert_called_once_with("123", True)
            
            # Verify service was called
            mock_task_service.create.assert_called_once()
            
            # Verify response
            assert result["code"] == 200
            assert result["data"]["task_id"] == "task_123"
    
    def test_task_dispatch_api_unauthorized(self):
        """Test task dispatch with unauthorized access."""
        with patch('server.controller.task.request') as mock_request, \
             patch('server.controller.task.AuthorityGuardianFactory') as mock_guardian_factory:
            
            # Mock request data
            mock_request.get_json.return_value = {
                "analysis_id": "123",
                "node_id_list": ["1", "2", "3"],
                "edge_id_list": ["10", "20"]
            }
            
            # Mock authority guardian - unauthorized
            mock_guardian = Mock()
            mock_guardian.check_authority.side_effect = PermissionError("Unauthorized access")
            mock_guardian_factory.get_authority_guardian.return_value = mock_guardian
            
            # Import and test
            from server.controller.task import TaskDispatchAPI
            api = TaskDispatchAPI()
            
            with pytest.raises(PermissionError):
                api.post()
    
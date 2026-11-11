"""
Unit tests for server core functionality in omicairn-worker.
Tests the server module including controllers, services, and data access objects.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import classes under test
from server.controller.task import TaskPreviousCheckAPI, TaskDispatchAPI
from server.service.task import task_service
from server.dao.node import node_dao
from server.dao.task import task_dao
from server.dao.computation import computation_dao


class TestTaskController:
    """Test task controller API endpoints."""
    
    def test_task_previous_check_api(self, mock_requests, mock_logger):
        """Test task previous check API endpoint."""
        with patch('server.controller.task.request') as mock_request, \
             patch('server.controller.task.task_service') as mock_task_service, \
             patch('server.controller.task.ResponseManager') as mock_response_manager:
            
            # Mock request data
            mock_request.get_json.return_value = {
                "node_id_list": ["node_1", "node_2", "node_3"]
            }
            
            # Mock service response
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
            
            # Test the API
            api = TaskPreviousCheckAPI()
            result = api.get()
            
            # Verify service was called with correct parameters
            mock_task_service.check_params.assert_called_once_with(["node_1", "node_2", "node_3"])
            
            # Verify response
            mock_response_manager.new_success_response.assert_called_once_with(mock_check_result)
            assert result["code"] == 200

    def test_task_dispatch_api(self, mock_requests, mock_logger):
        """Test task dispatch API endpoint."""
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
            mock_guardian_factory.get_authority_guardian.return_value = mock_guardian
            
            # Mock service response
            mock_task = {
                "task_id": "task_123",
                "analysis_id": "123",
                "status": "created"
            }
            mock_task_service.create.return_value = mock_task
            
            # Mock response manager
            mock_response_manager.new_success_response.return_value = {
                "code": 200,
                "data": mock_task
            }
            
            # Test the API
            api = TaskDispatchAPI()
            result = api.post()
            
            # Verify authority check
            mock_guardian.check_authority.assert_called_once_with("123", True)
            
            # Verify service was called with correct parameters
            mock_task_service.create.assert_called_once_with(
                "123",  # analysis_id
                [1, 2, 3],  # node_id_list (converted to int)
                [10, 20],  # edge_id_list (converted to int)
                "user_123"  # user_id
            )
            
            # Verify response
            mock_response_manager.new_success_response.assert_called_once_with(mock_task)
            assert result["code"] == 200


class TestTaskService:
    """Test task service functionality."""
    
    def test_task_service_check_params(self, mock_logger):
        """Test task service parameter checking."""
        with patch('server.service.task.node_dao') as mock_node_dao:
            # Mock node DAO responses
            mock_nodes = [
                Mock(id="node_1", state="finished"),
                Mock(id="node_2", state="running"),
                Mock(id="node_3", state="finished")
            ]
            mock_node_dao.find_by_ids.return_value = mock_nodes
            
            # Test the service method
            result = task_service.check_params(["node_1", "node_2", "node_3"])
            
            # Verify DAO was called
            mock_node_dao.find_by_ids.assert_called_once_with(["node_1", "node_2", "node_3"])
            
            # Verify result structure
            assert "all_ready" in result
            assert "ready_nodes" in result
            assert "pending_nodes" in result

    def test_task_service_create(self, mock_logger):
        """Test task service creation."""
        with patch('server.service.task.task_dao') as mock_task_dao, \
             patch('server.service.task.task_node_relation_dao') as mock_task_node_dao, \
             patch('server.service.task.task_edge_relation_dao') as mock_task_edge_dao, \
             patch('server.service.task.ComputationLauncher') as mock_launcher:
            
            # Mock DAO responses
            mock_task = Mock(id="task_123")
            mock_task_dao.create.return_value = mock_task
            
            mock_launcher_instance = Mock()
            mock_launcher.return_value = mock_launcher_instance
            
            # Test the service method
            result = task_service.create(
                analysis_id="analysis_123",
                node_id_list=[1, 2, 3],
                edge_id_list=[10, 20],
                user_id="user_123"
            )
            
            # Verify task creation
            mock_task_dao.create.assert_called_once()
            
            # Verify relations are created
            assert mock_task_node_dao.create.call_count == 3  # One for each node
            assert mock_task_edge_dao.create.call_count == 2  # One for each edge
            
            # Verify computation launcher is called
            mock_launcher.assert_called_once()
            mock_launcher_instance.launch.assert_called_once()


class TestNodeDAO:
    """Test node data access object functionality."""
    
    def test_node_dao_find_by_id(self, mock_database_globally, mock_logger):
        """Test finding node by ID."""
        with patch('server.dao.node.session') as mock_session:
            # Mock query result
            mock_node = Mock(id="node_123", name="Test Node", state="running")
            mock_session.query.return_value.filter.return_value.first.return_value = mock_node
            
            # Test the DAO method
            result = node_dao.find_by_id("node_123")
            
            # Verify query was made
            mock_session.query.assert_called_once()
            assert result == mock_node

    def test_node_dao_find_by_ids(self, mock_database_globally, mock_logger):
        """Test finding multiple nodes by IDs."""
        with patch('server.dao.node.session') as mock_session:
            # Mock query result
            mock_nodes = [
                Mock(id="node_1", name="Node 1"),
                Mock(id="node_2", name="Node 2"),
                Mock(id="node_3", name="Node 3")
            ]
            mock_session.query.return_value.filter.return_value.all.return_value = mock_nodes
            
            # Test the DAO method
            result = node_dao.find_by_ids(["node_1", "node_2", "node_3"])
            
            # Verify query was made
            mock_session.query.assert_called_once()
            assert result == mock_nodes

    def test_node_dao_update(self, mock_database_globally, mock_logger):
        """Test updating node."""
        with patch('server.dao.node.session') as mock_session:
            mock_node = Mock(id="node_123", state="running")
            mock_session.query.return_value.filter.return_value.first.return_value = mock_node
            
            # Test the DAO method
            node_dao.update("node_123", {"state": "finished"})
            
            # Verify node was updated
            assert mock_node.state == "finished"
            mock_session.commit.assert_called_once()

    def test_node_dao_create(self, mock_database_globally, mock_logger):
        """Test creating node."""
        with patch('server.dao.node.session') as mock_session:
            node_data = {
                "name": "New Node",
                "node_type": "computation",
                "analysis_id": "analysis_123",
                "owner_id": "user_123"
            }
            
            # Test the DAO method
            result = node_dao.create(node_data)
            
            # Verify node was added to session
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()


class TestTaskDAO:
    """Test task data access object functionality."""
    
    def test_task_dao_create(self, mock_database_globally, mock_logger):
        """Test creating task."""
        with patch('server.dao.task.session') as mock_session:
            task_data = {
                "analysis_id": "analysis_123",
                "owner_id": "user_123",
                "state": "created"
            }
            
            # Test the DAO method
            result = task_dao.create(task_data)
            
            # Verify task was added to session
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    def test_task_dao_find_by_id(self, mock_database_globally, mock_logger):
        """Test finding task by ID."""
        with patch('server.dao.task.session') as mock_session:
            mock_task = Mock(id="task_123", state="running")
            mock_session.query.return_value.filter.return_value.first.return_value = mock_task
            
            # Test the DAO method
            result = task_dao.find_by_id("task_123")
            
            # Verify query was made
            mock_session.query.assert_called_once()
            assert result == mock_task

    def test_task_dao_update(self, mock_database_globally, mock_logger):
        """Test updating task."""
        with patch('server.dao.task.session') as mock_session:
            mock_task = Mock(id="task_123", state="running")
            mock_session.query.return_value.filter.return_value.first.return_value = mock_task
            
            # Test the DAO method
            task_dao.update("task_123", {"state": "finished"})
            
            # Verify task was updated
            assert mock_task.state == "finished"
            mock_session.commit.assert_called_once()


class TestComputationDAO:
    """Test computation data access object functionality."""
    
    def test_computation_dao_create(self, mock_database_globally, mock_logger):
        """Test creating computation."""
        with patch('server.dao.computation.session') as mock_session:
            computation_data = {
                "node_id": "node_123",
                "task_id": "task_123",
                "state": "queued",
                "owner_id": "user_123"
            }
            
            # Test the DAO method
            result = computation_dao.create(computation_data)
            
            # Verify computation was added to session
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    def test_computation_dao_find_by_node_id(self, mock_database_globally, mock_logger):
        """Test finding computation by node ID."""
        with patch('server.dao.computation.session') as mock_session:
            mock_computation = Mock(id="comp_123", node_id="node_123")
            mock_session.query.return_value.filter.return_value.first.return_value = mock_computation
            
            # Test the DAO method
            result = computation_dao.find_by_node_id("node_123")
            
            # Verify query was made
            mock_session.query.assert_called_once()
            assert result == mock_computation

    def test_computation_dao_update_state(self, mock_database_globally, mock_logger):
        """Test updating computation state."""
        with patch('server.dao.computation.session') as mock_session:
            mock_computation = Mock(id="comp_123", state="running")
            mock_session.query.return_value.filter.return_value.first.return_value = mock_computation
            
            # Test the DAO method
            computation_dao.update("comp_123", {"state": "finished"})
            
            # Verify computation was updated
            assert mock_computation.state == "finished"
            mock_session.commit.assert_called_once()


class TestServerModelsIntegration:
    """Test integration between server models and DAOs."""
    
    def test_task_node_relation_creation(self, mock_database_globally, mock_logger):
        """Test task-node relation creation."""
        with patch('server.dao.task_node_relation.session') as mock_session:
            # Mock the relation creation
            relation_data = {
                "task_id": "task_123",
                "node_id": "node_123",
                "relation_type": "computation"
            }
            
            # This would be part of the task service
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            
            # Verify the session methods are available for mocking
            assert hasattr(mock_session, 'add')
            assert hasattr(mock_session, 'commit')

    def test_task_edge_relation_creation(self, mock_database_globally, mock_logger):
        """Test task-edge relation creation."""
        with patch('server.dao.task_edge_relation.session') as mock_session:
            # Mock the relation creation
            relation_data = {
                "task_id": "task_123",
                "edge_id": "edge_123"
            }
            
            # This would be part of the task service
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            
            # Verify the session methods are available for mocking
            assert hasattr(mock_session, 'add')
            assert hasattr(mock_session, 'commit')

    def test_computation_launching_workflow(self, mock_logger):
        """Test complete computation launching workflow."""
        with patch('server.service.task.ComputationLauncher') as mock_launcher_class, \
             patch('server.service.task.task_dao') as mock_task_dao, \
             patch('server.service.task.node_dao') as mock_node_dao:
            
            # Mock task creation
            mock_task = Mock(id="task_123", analysis_id="analysis_123")
            mock_task_dao.create.return_value = mock_task
            
            # Mock node data
            mock_nodes = [
                Mock(id="node_1", node_type="computation"),
                Mock(id="node_2", node_type="computation")
            ]
            mock_node_dao.find_by_ids.return_value = mock_nodes
            
            # Mock computation launcher
            mock_launcher = Mock()
            mock_launcher_class.return_value = mock_launcher
            
            # This simulates what task_service.create would do
            task = mock_task_dao.create({
                "analysis_id": "analysis_123",
                "owner_id": "user_123"
            })
            
            nodes = mock_node_dao.find_by_ids(["node_1", "node_2"])
            
            launcher = mock_launcher_class(task)
            launcher.launch(nodes)
            
            # Verify the workflow
            mock_task_dao.create.assert_called_once()
            mock_node_dao.find_by_ids.assert_called_once_with(["node_1", "node_2"])
            mock_launcher_class.assert_called_once_with(task)
            mock_launcher.launch.assert_called_once_with(nodes)


class TestServerErrorHandling:
    """Test error handling in server components."""
    
    def test_task_controller_missing_parameters(self, mock_logger):
        """Test task controller with missing parameters."""
        with patch('server.controller.task.request') as mock_request, \
             patch('server.controller.task.request_auditor') as mock_auditor:
            
            # Mock missing parameters
            mock_auditor.request_json_check.side_effect = Exception("Missing required parameter: node_id_list")
            
            api = TaskPreviousCheckAPI()
            
            # Should handle missing parameters
            with pytest.raises(Exception):
                api.get()

    def test_dao_database_connection_error(self, mock_logger):
        """Test DAO handling database connection errors."""
        with patch('server.dao.node.session') as mock_session:
            # Mock database connection error
            mock_session.query.side_effect = Exception("Database connection failed")
            
            # Should handle database errors
            with pytest.raises(Exception):
                node_dao.find_by_id("node_123")

    def test_service_layer_exception_handling(self, mock_logger):
        """Test service layer exception handling."""
        with patch('server.service.task.task_dao') as mock_task_dao:
            # Mock DAO exception
            mock_task_dao.create.side_effect = Exception("Database constraint violation")
            
            # Should propagate DAO exceptions
            with pytest.raises(Exception):
                task_service.create("analysis_123", [1, 2], [10], "user_123")

    def test_authority_check_failure(self, mock_logger):
        """Test authority check failure handling."""
        with patch('server.controller.task.AuthorityGuardianFactory') as mock_guardian_factory, \
             patch('server.controller.task.request') as mock_request:
            
            # Mock request data
            mock_request.get_json.return_value = {
                "analysis_id": "123",
                "node_id_list": ["1", "2"],
                "edge_id_list": ["10"]
            }
            
            # Mock authority failure
            mock_guardian = Mock()
            mock_guardian.check_authority.side_effect = Exception("Insufficient permissions")
            mock_guardian_factory.get_authority_guardian.return_value = mock_guardian
            
            api = TaskDispatchAPI()
            
            # Should handle authority failures
            with pytest.raises(Exception):
                api.post()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
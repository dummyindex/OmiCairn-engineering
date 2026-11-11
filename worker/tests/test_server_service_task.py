"""
Unit tests for server task service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestTaskService:
    """Test task service business logic."""
    
    def test_check_params_all_nodes_ready(self):
        """Test parameter checking when all nodes are ready."""
        with patch('server.service.task.node_dao') as mock_node_dao, \
             patch('server.service.task.computation_dao') as mock_comp_dao:
            
            # Mock nodes
            mock_nodes = [
                Mock(id="node_1", type="data", state="ready"),
                Mock(id="node_2", type="computation", state="ready"),
                Mock(id="node_3", type="data", state="ready")
            ]
            mock_node_dao.find_by_id_list.return_value = mock_nodes
            
            # Mock computations - all successful
            for node in mock_nodes:
                mock_computation = Mock()
                mock_computation.state = "success"
                mock_comp_dao.find_latest_by_node.return_value = mock_computation
            
            # Import and test
            from server.service.task import TaskService
            service = TaskService()
            result = service.check_params(["node_1", "node_2", "node_3"])
            
            # Verify
            assert result["all_ready"] is True
            assert len(result["ready_nodes"]) == 3
            assert len(result["pending_nodes"]) == 0
    
    def test_check_params_with_pending_nodes(self):
        """Test parameter checking with pending nodes."""
        with patch('server.service.task.node_dao') as mock_node_dao, \
             patch('server.service.task.computation_dao') as mock_comp_dao:
            
            # Mock nodes - mixed states
            mock_node_1 = Mock(id="node_1", type="computation", state="ready")
            mock_node_2 = Mock(id="node_2", type="computation", state="running")
            mock_node_3 = Mock(id="node_3", type="computation", state="failed")
            
            mock_node_dao.find_by_id_list.return_value = [
                mock_node_1, mock_node_2, mock_node_3
            ]
            
            # Mock computations
            mock_comp_dao.find_latest_by_node.side_effect = [
                Mock(state="success"),  # node_1
                Mock(state="running"),   # node_2
                Mock(state="failed")     # node_3
            ]
            
            # Import and test
            from server.service.task import TaskService
            service = TaskService()
            result = service.check_params(["node_1", "node_2", "node_3"])
            
            # Verify
            assert result["all_ready"] is False
            assert len(result["pending_nodes"]) > 0
    
    def test_create_task_success(self):
        """Test successful task creation."""
        with patch('server.service.task.task_dao') as mock_task_dao, \
             patch('server.service.task.node_dao') as mock_node_dao, \
             patch('server.service.task.edge_dao') as mock_edge_dao, \
             patch('server.service.task.task_node_relation_dao') as mock_tn_dao, \
             patch('server.service.task.task_edge_relation_dao') as mock_te_dao, \
             patch('server.service.task.FlowTool') as mock_flow_tool:
            
            # Mock task creation
            mock_task = Mock()
            mock_task.id = "task_123"
            mock_task.analysis_id = "analysis_123"
            mock_task.state = "created"
            mock_task_dao.insert.return_value = mock_task
            
            # Mock nodes and edges
            mock_node_dao.find_by_id_list.return_value = [
                Mock(id="node_1"),
                Mock(id="node_2")
            ]
            mock_edge_dao.find_by_id_list.return_value = [
                Mock(id="edge_1")
            ]
            
            # Mock flow tool
            mock_flow_tool.get_execution_order.return_value = ["node_1", "node_2"]
            
            # Import and test
            from server.service.task import TaskService
            service = TaskService()
            result = service.create(
                "analysis_123",
                "user_123",
                ["node_1", "node_2"],
                ["edge_1"]
            )
            
            # Verify
            mock_task_dao.insert.assert_called_once()
            assert result.id == "task_123"
    
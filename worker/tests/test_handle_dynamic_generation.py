"""
Unit tests for handle_dynamic_generation core functions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
import json
import sys
import os

# Mock database before importing modules
with patch('sqlalchemy.create_engine'):
    with patch('sqlalchemy.orm.sessionmaker'):
        # Add the handle_dynamic_generation module to the path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'handle_dynamic_generation'))
        
        from handle_dynamic_generation.index import (
            DynamicGenerationController,
            lock_nodes,
            unlock_nodes,
        )
        from handle_dynamic_generation.constants import NodeType, NodeState


class TestLockNodes:
    """Test lock_nodes function"""

    def test_lock_nodes_success(self):
        """Test locking nodes successfully"""
        mock_server_agent = Mock()
        node_ids = ["node1", "node2", "node3"]
        
        lock_nodes(mock_server_agent, node_ids)
        
        mock_server_agent.edit_nodes.assert_called_once_with(
            node_ids,
            {"dynamic_generation_locked": True}
        )

    def test_lock_nodes_empty_list(self):
        """Test locking with empty node list"""
        mock_server_agent = Mock()
        node_ids = []
        
        lock_nodes(mock_server_agent, node_ids)
        
        mock_server_agent.edit_nodes.assert_called_once_with(
            [],
            {"dynamic_generation_locked": True}
        )

    def test_lock_nodes_single_node(self):
        """Test locking a single node"""
        mock_server_agent = Mock()
        node_ids = ["single_node"]
        
        lock_nodes(mock_server_agent, node_ids)
        
        mock_server_agent.edit_nodes.assert_called_once_with(
            node_ids,
            {"dynamic_generation_locked": True}
        )


class TestUnlockNodes:
    """Test unlock_nodes function"""

    def test_unlock_nodes_success(self):
        """Test unlocking nodes successfully"""
        mock_server_agent = Mock()
        node_ids = ["node1", "node2", "node3"]
        
        unlock_nodes(mock_server_agent, node_ids)
        
        mock_server_agent.edit_nodes.assert_called_once_with(
            node_ids,
            {"dynamic_generation_locked": False}
        )

    def test_unlock_nodes_empty_list(self):
        """Test unlocking with empty node list"""
        mock_server_agent = Mock()
        node_ids = []
        
        unlock_nodes(mock_server_agent, node_ids)
        
        mock_server_agent.edit_nodes.assert_called_once_with(
            [],
            {"dynamic_generation_locked": False}
        )


class TestDynamicGenerationController:
    """Test DynamicGenerationController class"""

    @pytest.fixture
    def mock_dynamic_generation(self):
        """Create a mock DynamicGeneration object"""
        dg = Mock()
        dg.generation_id = "test_gen_id"
        dg.max_node = 10
        dg.max_branch = 5
        dg.previous_node_id = "prev_node_id"
        dg.user_request = "test request"
        dg.llm_model = "gpt-4"
        dg.max_branch = 3
        dg.generation_mode = "standard"
        dg.computation_resource_configure = None
        dg.version = "v1"
        dg.state = "running"
        dg.rest_node_count = 10
        return dg

    @pytest.fixture
    def mock_previous_node(self):
        """Create a mock previous node"""
        node = Mock()
        node.id = "prev_node_id"
        node.analysis_id = "analysis_123"
        node.type = NodeType.COMPUTATION_NODE.value
        node.x = 100
        node.y = 100
        return node

    @pytest.fixture
    def mock_server_agent(self):
        """Create a mock ServerAgent"""
        return Mock()

    @patch('handle_dynamic_generation.index.find_node_by_id')
    def test_controller_initialization(self, mock_find_node, mock_dynamic_generation, mock_previous_node, mock_server_agent):
        """Test DynamicGenerationController initialization"""
        mock_find_node.return_value = mock_previous_node
        
        controller = DynamicGenerationController(mock_dynamic_generation, mock_server_agent)
        
        assert controller._dynamic_generation == mock_dynamic_generation
        assert controller.rest_node_count == 10
        assert controller.rest_branch_count == 5
        assert controller.previous_node == mock_previous_node
        assert controller.analysis_id == "analysis_123"
        assert controller.server_agent == mock_server_agent
        assert controller.locked_nodes == []

    @patch('handle_dynamic_generation.index.find_node_by_id')
    def test_collect_previous_nodes(self, mock_find_node, mock_dynamic_generation, mock_previous_node, mock_server_agent):
        """Test collecting previous nodes"""
        mock_find_node.return_value = mock_previous_node
        mock_server_agent.find_all_previous_nodes.return_value = {
            "data": [
                {"id": "node1", "name": "Node 1"},
                {"id": "node2", "name": "Node 2"}
            ]
        }
        
        controller = DynamicGenerationController(mock_dynamic_generation, mock_server_agent)
        controller.collect_preivous_nodes()
        
        assert len(controller.locked_nodes) == 2
        mock_server_agent.find_all_previous_nodes.assert_called_once_with(mock_previous_node.id)

    @patch('handle_dynamic_generation.index.find_node_by_id')
    @patch('handle_dynamic_generation.index.lock_nodes')
    def test_lock_nodes_method(self, mock_lock_nodes_func, mock_find_node, mock_dynamic_generation, mock_previous_node, mock_server_agent):
        """Test lock_nodes method"""
        mock_find_node.return_value = mock_previous_node
        
        controller = DynamicGenerationController(mock_dynamic_generation, mock_server_agent)
        controller.locked_nodes = [
            {"id": "node1"},
            {"id": "node2"}
        ]
        controller.lock_nodes()
        
        mock_lock_nodes_func.assert_called_once_with(
            mock_server_agent,
            ["node1", "node2"]
        )

    @patch('handle_dynamic_generation.index.find_node_by_id')
    @patch('handle_dynamic_generation.index.find_dynamic_generation_by_id')
    def test_check_excutable_running(self, mock_find_dg, mock_find_node, mock_dynamic_generation, mock_previous_node, mock_server_agent):
        """Test _check_excutable when generation is running"""
        mock_find_node.return_value = mock_previous_node
        mock_dg_updated = Mock()
        mock_dg_updated.state = "running"
        mock_dg_updated.rest_node_count = 5
        mock_find_dg.return_value = mock_dg_updated
        
        controller = DynamicGenerationController(mock_dynamic_generation, mock_server_agent)
        executable, dg = controller._check_excutable()
        
        assert executable is True
        assert dg == mock_dg_updated

    @patch('handle_dynamic_generation.index.find_node_by_id')
    @patch('handle_dynamic_generation.index.find_dynamic_generation_by_id')
    def test_check_excutable_stopped(self, mock_find_dg, mock_find_node, mock_dynamic_generation, mock_previous_node, mock_server_agent):
        """Test _check_excutable when generation is stopped"""
        mock_find_node.return_value = mock_previous_node
        mock_dg_updated = Mock()
        mock_dg_updated.state = "stopped"
        mock_dg_updated.rest_node_count = 5
        mock_find_dg.return_value = mock_dg_updated
        
        controller = DynamicGenerationController(mock_dynamic_generation, mock_server_agent)
        executable, dg = controller._check_excutable()
        
        assert executable is False

    @patch('handle_dynamic_generation.index.find_node_by_id')
    @patch('handle_dynamic_generation.index.find_dynamic_generation_by_id')
    def test_check_excutable_no_rest_nodes(self, mock_find_dg, mock_find_node, mock_dynamic_generation, mock_previous_node, mock_server_agent):
        """Test _check_excutable when no rest nodes"""
        mock_find_node.return_value = mock_previous_node
        mock_dg_updated = Mock()
        mock_dg_updated.state = "running"
        mock_dg_updated.rest_node_count = 0
        mock_find_dg.return_value = mock_dg_updated
        
        controller = DynamicGenerationController(mock_dynamic_generation, mock_server_agent)
        executable, dg = controller._check_excutable()
        
        assert executable is False

    @patch('handle_dynamic_generation.index.find_node_by_id')
    @patch('handle_dynamic_generation.index.find_dynamic_generation_by_id')
    def test_check_excutable_not_found(self, mock_find_dg, mock_find_node, mock_dynamic_generation, mock_previous_node, mock_server_agent):
        """Test _check_excutable when generation not found"""
        mock_find_node.return_value = mock_previous_node
        mock_find_dg.return_value = None
        
        controller = DynamicGenerationController(mock_dynamic_generation, mock_server_agent)
        executable, dg = controller._check_excutable()
        
        assert executable is False
        assert dg is None

    @patch('handle_dynamic_generation.index.find_node_by_id')
    @patch('handle_dynamic_generation.index.update_node')
    @patch('handle_dynamic_generation.index.create_next_level_fbs')
    def test_launch_empty_fb_list(self, mock_create_fbs, mock_update_node, mock_find_node, mock_dynamic_generation, mock_previous_node, mock_server_agent):
        """Test launch with empty FB list"""
        mock_find_node.return_value = mock_previous_node
        mock_create_fbs.return_value = []
        
        controller = DynamicGenerationController(mock_dynamic_generation, mock_server_agent)
        controller.launch(mock_previous_node)
        
        # Should update node state twice: GENERATING and FINISHED
        assert mock_update_node.call_count == 2
        mock_server_agent.report_dynamic_generation_branch_done.assert_called_once()

    @patch('handle_dynamic_generation.index.find_node_by_id')
    @patch('handle_dynamic_generation.index.update_node')
    @patch('handle_dynamic_generation.index.create_next_level_fbs')
    @patch('handle_dynamic_generation.index.update_dynamic_generation')
    @patch('handle_dynamic_generation.index.update_dynamic_generation_branch')
    @patch('handle_dynamic_generation.index.DynamicGenerationWaiter')
    @patch('handle_dynamic_generation.index.lock_nodes')
    @patch('handle_dynamic_generation.index.find_dynamic_generation_by_id')
    def test_launch_with_fb_list(self, mock_find_dg, mock_lock_nodes_func, mock_waiter_class, 
                                  mock_update_dg_branch, mock_update_dg, mock_create_fbs, 
                                  mock_update_node, mock_find_node, mock_dynamic_generation, 
                                  mock_previous_node, mock_server_agent):
        """Test launch with FB list"""
        mock_find_node.side_effect = [mock_previous_node, Mock(id="new_node_1")]
        mock_dg_updated = Mock()
        mock_dg_updated.state = "running"
        mock_dg_updated.rest_node_count = 5
        mock_find_dg.return_value = mock_dg_updated
        
        mock_create_fbs.return_value = [
            {
                "fb_id": "fb1",
                "fb_version_id": "fbv1",
                "fb_name": "Test FB 1",
                "session_id": "session1",
                "remaining_tasks": "task1"
            }
        ]
        
        mock_server_agent.create_computation_node.return_value = {
            "data": {"id": "new_node_1"}
        }
        mock_server_agent.create_edge.return_value = {
            "data": {"id": "new_edge_1"}
        }
        
        mock_waiter = Mock()
        mock_waiter_class.return_value = mock_waiter
        
        controller = DynamicGenerationController(mock_dynamic_generation, mock_server_agent)
        controller.launch(mock_previous_node)
        
        # Verify node creation
        mock_server_agent.create_computation_node.assert_called_once()
        # Verify edge creation
        mock_server_agent.create_edge.assert_called_once()
        # Verify task launch
        mock_server_agent.launch_task.assert_called_once()
        # Verify dynamic generation update
        mock_update_dg.assert_called_once()

    @patch('handle_dynamic_generation.index.find_node_by_id')
    def test_launch_v2(self, mock_find_node, mock_dynamic_generation, mock_previous_node, mock_server_agent):
        """Test launch_v2 method"""
        mock_find_node.return_value = mock_previous_node
        mock_server_agent.create_computation_node.return_value = {
            "data": {"id": "new_node_v2"}
        }
        mock_server_agent.create_edge.return_value = {
            "data": {"id": "new_edge_v2"}
        }
        
        controller = DynamicGenerationController(mock_dynamic_generation, mock_server_agent)
        controller.launch_v2(mock_previous_node)
        
        # Verify node creation with specific parameters
        call_args = mock_server_agent.create_computation_node.call_args
        assert call_args[1]['function_block_id'] == 151
        assert call_args[1]['function_block_version_id'] == 164
        assert call_args[1]['name'] == "First Step"
        
        # Verify edge and task launch
        mock_server_agent.create_edge.assert_called_once()
        mock_server_agent.launch_task.assert_called_once()

    @patch('handle_dynamic_generation.index.find_node_by_id')
    @patch('handle_dynamic_generation.index.update_dynamic_generation_branch')
    def test_launch_v3(self, mock_update_branch, mock_find_node, mock_dynamic_generation, mock_previous_node, mock_server_agent):
        """Test launch_v3 method for notebook node creation"""
        mock_find_node.return_value = mock_previous_node
        mock_server_agent.create_notebook_node.return_value = {
            "data": {"id": "new_notebook_node"}
        }
        mock_server_agent.create_edge.return_value = {
            "data": {"id": "new_edge_v3"}
        }
        
        controller = DynamicGenerationController(mock_dynamic_generation, mock_server_agent)
        controller.launch_v3(mock_previous_node)
        
        # Verify notebook node creation
        call_args = mock_server_agent.create_notebook_node.call_args
        assert call_args[1]['node_type'] == NodeType.NOTEBOOK_NODE.value
        assert call_args[1]['name'] == "Notebook Node"
        
        # Verify branch update
        mock_update_branch.assert_called_once()
        
        # Verify edge and task launch
        mock_server_agent.create_edge.assert_called_once()
        mock_server_agent.launch_task.assert_called_once()

    @patch('handle_dynamic_generation.index.find_node_by_id')
    @patch('handle_dynamic_generation.index.create_next_level_fbs')
    @patch('handle_dynamic_generation.index.update_node')
    def test_launch_with_resource_configure(self, mock_update_node, mock_create_fbs, mock_find_node, mock_server_agent):
        """Test launch with computation resource configuration"""
        mock_previous_node = Mock()
        mock_previous_node.id = "prev_node_id"
        mock_previous_node.analysis_id = "analysis_123"
        mock_previous_node.type = NodeType.COMPUTATION_NODE.value
        mock_previous_node.x = 100
        mock_previous_node.y = 100
        
        mock_find_node.return_value = mock_previous_node
        mock_create_fbs.return_value = []
        
        mock_dg = Mock()
        mock_dg.generation_id = "test_gen_id"
        mock_dg.max_node = 10
        mock_dg.max_branch = 5
        mock_dg.previous_node_id = "prev_node_id"
        mock_dg.user_request = "test request"
        mock_dg.llm_model = "gpt-4"
        mock_dg.generation_mode = "standard"
        mock_dg.version = "v1"
        mock_dg.state = "running"
        mock_dg.rest_node_count = 10
        mock_dg.computation_resource_configure = json.dumps({
            "system_env": "production",
            "cpu": 4,
            "memory": "8GB"
        })
        
        controller = DynamicGenerationController(mock_dg, mock_server_agent)
        controller.launch(mock_previous_node)
        
        # Verify report is called when FB list is empty
        mock_server_agent.report_dynamic_generation_branch_done.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

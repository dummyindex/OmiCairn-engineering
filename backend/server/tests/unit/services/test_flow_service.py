import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime
import pytest
import json

from main import create_app
from service.flow import FlowService
from model.node import Node
from model.edge import Edge
from constants.node import NodeType, NodeState
from constants.authority import Relation, Permission, SpecialUserId


@pytest.mark.service
@pytest.mark.unit
class TestFlowService(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()
        self.flow_service = FlowService()
        
        self.sample_node = Node(
            id=1,
            analysis_id=1,
            name="test_node",
            x=100,
            y=200,
            function_block_id=1,
            type=NodeType.FUNCTION_BLOCK,
            state=NodeState.PENDING,
            created_time=datetime.now()
        )
        
        self.sample_edge = Edge(
            id=1,
            analysis_id=1,
            source_node_id=1,
            target_node_id=2,
            source_param_name="output",
            target_param_name="input"
        )

    def tearDown(self):
        self.ctx.pop()

    @patch('dao.node.node_dao.find_by_id')
    def test_get_node_by_id_exists(self, mock_find_by_id):
        mock_find_by_id.return_value = self.sample_node
        
        result = self.flow_service.get_node_by_id(1)
        
        self.assertEqual(result, self.sample_node)
        mock_find_by_id.assert_called_once_with(1)

    @patch('dao.node.node_dao.find_by_id')
    def test_get_node_by_id_not_exists(self, mock_find_by_id):
        mock_find_by_id.return_value = None
        
        result = self.flow_service.get_node_by_id(999)
        
        self.assertIsNone(result)
        mock_find_by_id.assert_called_once_with(999)

    @patch('dao.node.node_dao.find_by_analysis_id_with_computation')
    def test_get_node_list_by_analysis_id_with_computation(self, mock_find_with_comp):
        mock_find_with_comp.return_value = [self.sample_node]
        
        result = self.flow_service.get_node_list_by_analysis_id(1, with_computation=True)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_find_with_comp.assert_called_once_with(1)

    @patch('dao.node.node_dao.find_by_analysis_id')
    def test_get_node_list_by_analysis_id_without_computation(self, mock_find):
        mock_find.return_value = [self.sample_node]
        
        result = self.flow_service.get_node_list_by_analysis_id(1, with_computation=False)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_find.assert_called_once_with(1)

    @patch('dao.node.node_dao.find_by_id_list')
    def test_get_node_list_by_idx(self, mock_find_by_list):
        node_ids = [1, 2, 3]
        mock_find_by_list.return_value = [self.sample_node]
        
        result = self.flow_service.get_node_list_by_idx(node_ids)
        
        self.assertIsNotNone(result)
        mock_find_by_list.assert_called_once_with(node_ids)

    @patch('dao.node.node_dao.update')
    def test_edit_node_success(self, mock_update):
        mock_update.return_value = 1
        
        node_data = {"name": "updated_node", "x": 150, "y": 250}
        result = self.flow_service.edit_node(1, node_data)
        
        mock_update.assert_called_once()

    @patch('dao.node.node_dao.create')
    def test_create_node_success(self, mock_create):
        mock_create.return_value = self.sample_node
        
        node_data = {
            "name": "new_node",
            "x": 100,
            "y": 200,
            "function_block_id": 1,
            "analysis_id": 1
        }
        
        result = self.flow_service.create_node(1, node_data)
        
        mock_create.assert_called_once()

    @patch('dao.node.node_dao.delete_by_id')
    def test_delete_node_success(self, mock_delete):
        mock_delete.return_value = 1
        
        result = self.flow_service.delete_node(1)
        
        mock_delete.assert_called_once_with(1)

    @patch('dao.edge.edge_dao.create')
    def test_create_edge_success(self, mock_create):
        mock_create.return_value = self.sample_edge
        
        edge_data = {
            "analysis_id": 1,
            "source_node_id": 1,
            "target_node_id": 2,
            "source_param_name": "output",
            "target_param_name": "input"
        }
        
        result = self.flow_service.create_edge(edge_data)
        
        mock_create.assert_called_once()

    @patch('dao.edge.edge_dao.delete_by_id')
    def test_delete_edge_success(self, mock_delete):
        mock_delete.return_value = 1
        
        result = self.flow_service.delete_edge(1)
        
        mock_delete.assert_called_once_with(1)

    @patch('dao.edge.edge_dao.find_by_analysis_id')
    def test_get_edge_list_by_analysis_id(self, mock_find):
        mock_find.return_value = [self.sample_edge]
        
        result = self.flow_service.get_edge_list_by_analysis_id(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_find.assert_called_once_with(1)

    @patch('dao.node.node_dao.find_by_analysis_id')
    def test_get_node_previte_dict_by_analysis_id(self, mock_find):
        mock_find.return_value = [self.sample_node]
        
        result = self.flow_service.get_node_previte_dict_by_analysis_id(1)
        
        self.assertIsNotNone(result)
        mock_find.assert_called_once_with(1)

    @patch('dao.node.node_dao.update_batch')
    def test_batch_edit_nodes_success(self, mock_batch_update):
        mock_batch_update.return_value = 2
        
        nodes_data = [
            {"id": 1, "name": "node1", "x": 100},
            {"id": 2, "name": "node2", "x": 200}
        ]
        
        result = self.flow_service.batch_edit_nodes(nodes_data)
        
        mock_batch_update.assert_called_once()

    @patch('dao.node.node_dao.find_by_id')
    @patch('dao.computation.computation_dao.find_by_node_id')
    def test_get_node_with_computations(self, mock_find_computations, mock_find_node):
        mock_find_node.return_value = self.sample_node
        mock_computations = [Mock(id=1, state="completed"), Mock(id=2, state="pending")]
        mock_find_computations.return_value = mock_computations
        
        result = self.flow_service.get_node_with_computations(1)
        
        self.assertIsNotNone(result)
        mock_find_node.assert_called_once_with(1)
        mock_find_computations.assert_called_once_with(1)

    def test_validate_node_data_valid(self):
        valid_data = {
            "name": "test_node",
            "x": 100,
            "y": 200,
            "function_block_id": 1
        }
        
        result = self.flow_service._validate_node_data(valid_data)
        self.assertTrue(result)

    def test_validate_node_data_invalid(self):
        invalid_data = {
            "name": "",  # Empty name
            "x": "invalid",  # Non-numeric x
            "y": 200
        }
        
        with self.assertRaises(Exception):
            self.flow_service._validate_node_data(invalid_data)

    def test_validate_edge_data_valid(self):
        valid_data = {
            "source_node_id": 1,
            "target_node_id": 2,
            "source_param_name": "output",
            "target_param_name": "input"
        }
        
        result = self.flow_service._validate_edge_data(valid_data)
        self.assertTrue(result)

    def test_validate_edge_data_invalid(self):
        invalid_data = {
            "source_node_id": 1,
            "target_node_id": 1,  # Same as source
            "source_param_name": "output",
            "target_param_name": "input"
        }
        
        with self.assertRaises(Exception):
            self.flow_service._validate_edge_data(invalid_data)

    @patch('dao.node.node_dao.count_by_analysis_id')
    def test_count_nodes_by_analysis(self, mock_count):
        mock_count.return_value = 5
        
        result = self.flow_service.count_nodes_by_analysis(1)
        
        self.assertEqual(result, 5)
        mock_count.assert_called_once_with(1)

    @patch('dao.edge.edge_dao.count_by_analysis_id')
    def test_count_edges_by_analysis(self, mock_count):
        mock_count.return_value = 3
        
        result = self.flow_service.count_edges_by_analysis(1)
        
        self.assertEqual(result, 3)
        mock_count.assert_called_once_with(1)

    def test_calculate_node_position_grid(self):
        # Test automatic node positioning
        result = self.flow_service._calculate_node_position(0, 3)  # First node in grid of 3
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)  # (x, y)
        self.assertIsInstance(result[0], (int, float))
        self.assertIsInstance(result[1], (int, float))

    @patch('tool.flow.FlowTool.validate_flow_connectivity')
    def test_validate_flow_connectivity(self, mock_validate):
        mock_validate.return_value = True
        
        nodes = [self.sample_node]
        edges = [self.sample_edge]
        
        result = self.flow_service.validate_flow_connectivity(nodes, edges)
        
        self.assertTrue(result)
        mock_validate.assert_called_once_with(nodes, edges)

    def test_get_node_dependencies(self):
        # Test getting node dependencies through edges
        with patch('dao.edge.edge_dao.find_by_target_node_id') as mock_find_edges:
            mock_edges = [self.sample_edge]
            mock_find_edges.return_value = mock_edges
            
            result = self.flow_service.get_node_dependencies(2)  # target_node_id
            
            self.assertIsNotNone(result)
            mock_find_edges.assert_called_once_with(2)

    @patch('waiter.node_space_waiter.NodeSpaceWaiter')
    def test_node_space_waiter_integration(self, mock_waiter_class):
        mock_waiter = Mock()
        mock_waiter_class.return_value = mock_waiter
        
        result = self.flow_service.get_node_space_waiter(1)
        
        self.assertEqual(result, mock_waiter)
        mock_waiter_class.assert_called_once_with(1)
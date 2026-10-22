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
from service.computation import ComputationService, reduct_params
from model.computation import Computation
from model.node import Node
from model.figure import Figure
from constants.node import NodeType, NodeState
from constants.computation import ComputationState


@pytest.mark.service
@pytest.mark.unit
@pytest.mark.computation
class TestComputationService(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()
        self.computation_service = ComputationService()
        
        self.sample_computation = Computation(
            id=1,
            node_id=1,
            task_id="task_123",
            state=ComputationState.PENDING.value,
            created_time=datetime.now(),
            started_time=None,
            finished_time=None,
            params=json.dumps({"param1": "value1"}),
            output=None,
            error_message=None
        )
        
        self.sample_node = Node(
            id=1,
            analysis_id=1,
            name="test_node",
            x=100,
            y=100,
            function_block_id=1,
            type=NodeType.FUNCTION_BLOCK,
            state=NodeState.PENDING,
            created_time=datetime.now()
        )

    def tearDown(self):
        self.ctx.pop()

    @patch('dao.computation.computation_dao.find_by_id')
    def test_get_computation_exists(self, mock_find_by_id):
        mock_find_by_id.return_value = self.sample_computation
        
        result = self.computation_service.get(1)
        
        self.assertEqual(result, self.sample_computation)
        mock_find_by_id.assert_called_once_with(1)

    @patch('dao.computation.computation_dao.find_by_id')
    def test_get_computation_not_exists(self, mock_find_by_id):
        mock_find_by_id.return_value = None
        
        result = self.computation_service.get(999)
        
        self.assertIsNone(result)
        mock_find_by_id.assert_called_once_with(999)

    @patch('dao.computation.computation_dao.find_by_node_id')
    def test_get_list_by_node(self, mock_find_by_node):
        mock_find_by_node.return_value = [self.sample_computation]
        
        result = self.computation_service.get_list_by_node(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_find_by_node.assert_called_once_with(1)

    @patch('dao.computation.computation_dao.find_by_task_id')
    def test_get_list_by_task(self, mock_find_by_task):
        mock_find_by_task.return_value = [self.sample_computation]
        
        result = self.computation_service.get_list_by_task("task_123")
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_find_by_task.assert_called_once_with("task_123")

    @patch('dao.computation.computation_dao.create')
    def test_create_computation(self, mock_create):
        mock_create.return_value = self.sample_computation
        
        params = {"param1": "value1"}
        result = self.computation_service.create(1, "task_123", params)
        
        self.assertEqual(result, self.sample_computation)
        mock_create.assert_called_once()

    @patch('dao.computation.computation_dao.update')
    def test_update_computation_state(self, mock_update):
        mock_update.return_value = 1
        
        result = self.computation_service.update_state(1, ComputationState.RUNNING.value)
        
        self.assertTrue(result)
        mock_update.assert_called_once()

    @patch('dao.computation.computation_dao.update')
    def test_update_computation_output(self, mock_update):
        mock_update.return_value = 1
        
        output = {"result": "success"}
        result = self.computation_service.update_output(1, output)
        
        self.assertTrue(result)
        mock_update.assert_called_once()

    @patch('dao.computation.computation_dao.update')
    def test_update_computation_error(self, mock_update):
        mock_update.return_value = 1
        
        result = self.computation_service.update_error_message(1, "Error occurred")
        
        self.assertTrue(result)
        mock_update.assert_called_once()

    @patch('dao.computation.computation_dao.delete_by_id')
    def test_delete_computation(self, mock_delete):
        mock_delete.return_value = 1
        
        result = self.computation_service.delete(1)
        
        self.assertTrue(result)
        mock_delete.assert_called_once_with(1)

    @patch('dao.figure.figure_dao.find_by_computation_id')
    def test_get_figures_by_computation(self, mock_find_figures):
        mock_figure = Figure(
            id=1,
            computation_id=1,
            file_path="test.png",
            created_time=datetime.now()
        )
        mock_find_figures.return_value = [mock_figure]
        
        result = self.computation_service.get_figures_by_computation(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_find_figures.assert_called_once_with(1)

    def test_reduct_params_cells_selector(self):
        arg_rules = [
            {"name": "cells", "render_type": "cells-selector"}
        ]
        params = {
            "cells": ["cell1", "cell2", "cell3", "cell4", "cell5", 
                     "cell6", "cell7", "cell8", "cell9", "cell10", "cell11"]
        }
        
        result = reduct_params(arg_rules, params)
        
        self.assertEqual(len(result["cells"]), 10)

    def test_reduct_params_genes_selector(self):
        arg_rules = [
            {"name": "genes", "render_type": "genes-selector"}
        ]
        params = {
            "genes": ["gene1", "gene2", "gene3", "gene4", "gene5",
                     "gene6", "gene7", "gene8", "gene9", "gene10", "gene11"]
        }
        
        result = reduct_params(arg_rules, params)
        
        self.assertEqual(len(result["genes"]), 10)

    def test_reduct_params_non_list(self):
        arg_rules = [
            {"name": "cells", "render_type": "cells-selector"}
        ]
        params = {
            "cells": "not_a_list"
        }
        
        result = reduct_params(arg_rules, params)
        
        self.assertEqual(result["cells"], [])

    def test_reduct_params_other_types(self):
        arg_rules = [
            {"name": "param1", "render_type": "text-input"}
        ]
        params = {
            "param1": "value1"
        }
        
        result = reduct_params(arg_rules, params)
        
        self.assertEqual(result["param1"], "value1")

    @patch('dao.computation.computation_dao.find_by_state')
    def test_get_computations_by_state(self, mock_find_by_state):
        mock_find_by_state.return_value = [self.sample_computation]
        
        result = self.computation_service.get_computations_by_state(ComputationState.PENDING.value)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_find_by_state.assert_called_once_with(ComputationState.PENDING.value)

    @patch('dao.computation.computation_dao.count_by_user')
    def test_count_computations_by_user(self, mock_count):
        mock_count.return_value = 5
        
        result = self.computation_service.count_computations_by_user(1)
        
        self.assertEqual(result, 5)
        mock_count.assert_called_once_with(1)

    def test_validate_params_valid_json(self):
        params = {"param1": "value1", "param2": 123}
        result = self.computation_service._validate_params(params)
        self.assertTrue(result)

    def test_validate_params_invalid_json(self):
        with self.assertRaises(Exception):
            self.computation_service._validate_params("invalid_json")

    @patch('waiter.computation.ComputationWaiter.wait_for_completion')
    def test_wait_for_completion(self, mock_wait):
        mock_wait.return_value = True
        
        result = self.computation_service.wait_for_completion(1)
        
        self.assertTrue(result)
        mock_wait.assert_called_once_with(1)
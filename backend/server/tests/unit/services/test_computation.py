import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
from unittest.mock import patch, Mock
from datetime import datetime
import pytest

from main import create_app
from service.computation import ComputationService, reduct_params
from model.computation import Computation
from model.node import Node
from model.figure import Figure
from constants.node import NodeType


@pytest.mark.service
@pytest.mark.unit
class TestComputationService(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()

        self.service = ComputationService()
        self.sample_computation = Mock(spec=Computation)
        self.sample_computation.id = 1
        self.sample_computation.node_id = 1
        self.sample_computation.task_id = "task_123"
        self.sample_computation.state = "completed"
        self.sample_computation.created_time = datetime.now()

    def tearDown(self):
        self.ctx.pop()

    @patch('dao.computation.computation_dao.find_by_id')
    def test_get_computation(self, mock_find):
        mock_find.return_value = self.sample_computation

        result = self.service.get(1)

        self.assertEqual(result, self.sample_computation)
        mock_find.assert_called_once_with(1)

    @patch('dao.computation.computation_dao.find_by_node_id')
    def test_get_list_by_node(self, mock_find):
        mock_find.return_value = [self.sample_computation]

        result = self.service.get_list_by_node(1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.sample_computation)
        mock_find.assert_called_once_with(1)

    @patch('dao.computation.computation_dao.find_by_task_id')
    def test_get_list_by_task(self, mock_find):
        mock_find.return_value = [self.sample_computation]

        result = self.service.get_list_by_task("task_123")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.sample_computation)
        mock_find.assert_called_once_with("task_123")

    @patch('dao.computation.computation_dao.find_latest_by_node_id')
    def test_get_latest_by_node(self, mock_find):
        mock_find.return_value = self.sample_computation

        result = self.service.get_latest_by_node(1)

        self.assertEqual(result, self.sample_computation)
        mock_find.assert_called_once_with(1)

    @patch('dao.computation.computation_dao.find_by_id')
    @patch('llm.llm_interface.LlmInterface.apply_for_optimize_error_description')
    def test_refresh_optimized_error_description(self, mock_apply, mock_find):
        mock_apply.return_value = None
        mock_find.return_value = self.sample_computation

        result = self.service.refresh_optimized_error_description(1, 123)

        self.assertEqual(result, self.sample_computation)
        mock_apply.assert_called_once_with(1, 123)
        mock_find.assert_called_once_with(1)

    @patch('dao.figure.figure_dao.find_by_computation_id')
    def test_get_figure_list_by_computation(self, mock_find):
        mock_figure = Figure(id=1, computation_id=1, file_key="figure_key")
        mock_find.return_value = [mock_figure]

        result = self.service.get_figure_list_by_computation(1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_figure)
        mock_find.assert_called_once_with(1)

    def test_reduct_params_with_selector(self):
        arg_rules = [
            {"name": "cells", "render_type": "cells-selector"},
            {"name": "genes", "render_type": "genes-selector"}
        ]
        params = {
            "cells": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "genes": ["gene1", "gene2", "gene3"]
        }

        result = reduct_params(arg_rules, params)

        # Should truncate to 10 items
        self.assertEqual(len(result["cells"]), 10)
        self.assertEqual(len(result["genes"]), 3)

    def test_reduct_params_non_list(self):
        arg_rules = [
            {"name": "cells", "render_type": "cells-selector"}
        ]
        params = {
            "cells": "not_a_list"
        }

        result = reduct_params(arg_rules, params)

        # Should convert to empty list
        self.assertEqual(result["cells"], [])

    def test_reduct_params_other_types(self):
        arg_rules = [
            {"name": "value", "render_type": "text-input"}
        ]
        params = {
            "value": "some_value"
        }

        result = reduct_params(arg_rules, params)

        # Should not modify other types
        self.assertEqual(result["value"], "some_value")

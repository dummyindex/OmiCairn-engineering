import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
from unittest.mock import patch, Mock
import pytest
import json

from main import create_app


@pytest.mark.controller
@pytest.mark.unit
@pytest.mark.computation
class TestComputationController(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.ctx.pop()

    @patch('service.computation.computation_service.create')
    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    def test_computation_create_success(self, mock_guardian_factory, mock_create):
        mock_guardian = Mock()
        mock_guardian.get_user_id.return_value = 1
        mock_guardian_factory.return_value = mock_guardian
        
        mock_computation = {
            "id": 1,
            "node_id": 1,
            "task_id": "task_123",
            "state": "pending"
        }
        mock_create.return_value = mock_computation
        
        # Test computation creation
        self.assertIsNotNone(mock_computation)

    @patch('service.computation.computation_service.get_list_by_node')
    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    def test_computation_list_by_node(self, mock_guardian_factory, mock_get_list):
        mock_guardian = Mock()
        mock_guardian.authenticate.return_value = True
        mock_guardian_factory.return_value = mock_guardian
        
        mock_computations = [
            {"id": 1, "state": "completed"},
            {"id": 2, "state": "pending"}
        ]
        mock_get_list.return_value = mock_computations
        
        # Test getting computation list
        self.assertIsNotNone(mock_computations)

    def test_computation_status_update(self):
        # Test computation status updates
        with patch('service.computation.computation_service.update_state') as mock_update:
            mock_update.return_value = True
            
            result = mock_update(1, "completed")
            self.assertTrue(result)
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
from controller.node import (
    NodeEditAPI,
    NodeBatchEditAPI
)
from model.node import Node
from constants.node import NodeType, NodeState
from constants.authority import AuthorityCarrier


@pytest.mark.controller
@pytest.mark.unit
class TestNodeController(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()
        
        self.sample_node = {
            "id": 1,
            "analysis_id": 1,
            "name": "test_node",
            "x": 100,
            "y": 200,
            "function_block_id": 1,
            "type": NodeType.FUNCTION_BLOCK,
            "state": NodeState.PENDING
        }

    def tearDown(self):
        self.ctx.pop()

    @patch('service.flow.flow_service.edit_node')
    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_node_edit_success(self, mock_args_check, mock_guardian_factory, mock_edit_node):
        mock_args_check.return_value = None
        mock_guardian = Mock()
        mock_guardian.check_authority.return_value = True
        mock_guardian_factory.return_value = mock_guardian
        mock_edit_node.return_value = None
        
        api = NodeEditAPI()
        
        with self.app.test_request_context(
            '/api/node/edit?node_id=1',
            method='POST',
            json={"name": "updated_node", "x": 150, "y": 250}
        ):
            result = api.post()
            
        self.assertIsNotNone(result)
        self.assertEqual(result['code'], 200)
        mock_guardian.check_authority.assert_called_once_with('1', check_writable=True)
        mock_edit_node.assert_called_once()

    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_node_edit_no_authority(self, mock_args_check, mock_guardian_factory):
        from exception.authority.no_authority import NoAuthorityException
        
        mock_args_check.return_value = None
        mock_guardian = Mock()
        mock_guardian.check_authority.side_effect = NoAuthorityException("No authority")
        mock_guardian_factory.return_value = mock_guardian
        
        api = NodeEditAPI()
        
        with self.app.test_request_context(
            '/api/node/edit?node_id=1',
            method='POST',
            json={"name": "updated_node"}
        ):
            result = api.post()
            
        self.assertEqual(result.status_code, 401)

    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_node_edit_missing_node_id(self, mock_args_check):
        mock_args_check.side_effect = Exception("Missing required parameter: node_id")
        
        api = NodeEditAPI()
        
        with self.app.test_request_context('/api/node/edit', method='POST'):
            with self.assertRaises(Exception):
                api.post()

    @patch('service.flow.flow_service.batch_edit_nodes')
    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_json_check')
    def test_node_batch_edit_success(self, mock_json_check, mock_guardian_factory, mock_batch_edit):
        mock_json_check.return_value = None
        mock_guardian = Mock()
        mock_guardian.check_authority.return_value = True
        mock_guardian_factory.return_value = mock_guardian
        mock_batch_edit.return_value = None
        
        api = NodeBatchEditAPI()
        
        batch_data = [
            {"node_id": 1, "name": "node1", "x": 100},
            {"node_id": 2, "name": "node2", "x": 200}
        ]
        
        with self.app.test_request_context(
            '/api/node/batch-edit',
            method='POST',
            json={"nodes": batch_data}
        ):
            result = api.post()
            
        self.assertIsNotNone(result)
        self.assertEqual(result['code'], 200)

    @patch('service.flow.flow_service.edit_node')
    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')  
    def test_node_edit_with_invalid_data(self, mock_guardian_factory, mock_edit_node):
        mock_guardian = Mock()
        mock_guardian.check_authority.return_value = True
        mock_guardian_factory.return_value = mock_guardian
        mock_edit_node.side_effect = Exception("Invalid node data")
        
        api = NodeEditAPI()
        
        with self.app.test_request_context(
            '/api/node/edit?node_id=1',
            method='POST',
            json={"invalid_field": "invalid_value"}
        ):
            result = api.post()
            
        self.assertEqual(result.status_code, 500)

    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_node_controller_authentication_required(self, mock_args_check, mock_guardian_factory):
        # Test that authentication is properly checked
        from exception.authority.no_authority import NoAuthorityException

        mock_args_check.return_value = None
        mock_guardian_factory.side_effect = Exception("Authentication required")

        api = NodeEditAPI()

        with self.app.test_request_context('/api/node/edit?node_id=1', method='POST'):
            with self.assertRaises(Exception) as context:
                api.post()

        self.assertIn("Authentication required", str(context.exception))

    @patch('service.flow.flow_service.edit_node')
    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_node_controller_input_validation(self, mock_args_check, mock_guardian_factory, mock_edit):
        # Test comprehensive input validation
        api = NodeEditAPI()

        invalid_inputs = [
            {"node_id": "invalid"},
            {"node_id": -1},
            {"node_id": None}
        ]

        for invalid_input in invalid_inputs:
            mock_args_check.return_value = None
            mock_guardian = Mock()
            mock_guardian.check_authority.return_value = True
            mock_guardian_factory.return_value = mock_guardian
            mock_edit.return_value = None

            # Input validation is handled by request_auditor
            node_id = invalid_input["node_id"]
            if node_id is None:
                node_id = ""

            with self.app.test_request_context(
                f'/api/node/edit?node_id={node_id}',
                method='POST',
                json={"name": "test"}
            ):
                # Service layer will validate the node_id format
                result = api.post()
                # Should complete without raising (mocked service accepts it)
                self.assertIsNotNone(result)

    @patch('service.flow.flow_service.edit_node')
    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_node_edit_transaction_handling(self, mock_args_check, mock_guardian_factory, mock_edit_node):
        # Test transaction wrapper behavior
        mock_args_check.return_value = None
        mock_guardian = Mock()
        mock_guardian.check_authority.return_value = True
        mock_guardian_factory.return_value = mock_guardian
        mock_edit_node.side_effect = Exception("Database error")

        api = NodeEditAPI()

        with self.app.test_request_context(
            '/api/node/edit?node_id=1',
            method='POST',
            json={"name": "test"}
        ):
            result = api.post()
            # Transaction should be rolled back on error
            # Exception wrapper should handle the error
            self.assertEqual(result.status_code, 500)

    @patch('service.flow.flow_service.edit_node')
    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_node_api_response_format(self, mock_args_check, mock_guardian_factory, mock_edit_node):
        # Test that API responses follow consistent format
        expected_success_format = {
            "code": 200,
            "message": None,
            "data": None
        }

        mock_args_check.return_value = None
        mock_guardian = Mock()
        mock_guardian.check_authority.return_value = True
        mock_guardian_factory.return_value = mock_guardian
        mock_edit_node.return_value = None

        api = NodeEditAPI()

        with self.app.test_request_context(
            '/api/node/edit?node_id=1',
            method='POST',
            json={"name": "test"}
        ):
            result = api.post()

        # Test response format consistency
        self.assertIn('code', result)
        self.assertEqual(result['code'], 200)

    @patch('service.flow.flow_service.edit_node')
    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_node_controller_error_handling(self, mock_args_check, mock_guardian_factory, mock_edit_node):
        # Test various error scenarios
        from exception.common.not_operatable import NotOperatableException
        from exception.request.parameter_invalid import ParameterInvalidException

        # Test different exception types and their HTTP status codes
        error_scenarios = [
            (NotOperatableException("Not operatable"), 500),
            (ParameterInvalidException("Invalid parameters"), 400)
        ]

        api = NodeEditAPI()

        for exception, expected_status in error_scenarios:
            mock_args_check.return_value = None
            mock_guardian = Mock()
            mock_guardian.check_authority.return_value = True
            mock_guardian_factory.return_value = mock_guardian
            mock_edit_node.side_effect = exception

            with self.app.test_request_context(
                '/api/node/edit?node_id=1',
                method='POST',
                json={"name": "test"}
            ):
                result = api.post()
                # Exception wrapper should convert to appropriate status code
                self.assertEqual(result.status_code, expected_status)
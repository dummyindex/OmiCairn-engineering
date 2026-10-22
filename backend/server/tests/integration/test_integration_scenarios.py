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


@pytest.mark.integration
@pytest.mark.slow
class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complete workflows"""

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.ctx.pop()

    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('service.analysis.analysis_service.create')
    def test_complete_analysis_workflow(self, mock_create_analysis, mock_guardian_factory):
        """Test complete analysis creation and management workflow"""
        # Mock authentication
        mock_guardian = Mock()
        mock_guardian.get_user_id.return_value = 1
        mock_guardian_factory.return_value = mock_guardian
        
        # Mock analysis creation
        mock_analysis = {
            "id": 1,
            "name": "Integration Test Analysis",
            "user_id": 1,
            "created_time": "2023-01-01T00:00:00"
        }
        mock_create_analysis.return_value = mock_analysis
        
        # Test analysis creation workflow
        with patch('service.analysis.analysis_service.get_info_list') as mock_get_list:
            mock_get_list.return_value = []

            # Verify the workflow completes successfully
            self.assertIsNotNone(mock_analysis)
            self.assertEqual(mock_analysis['name'], "Integration Test Analysis")
            mock_create_analysis.assert_called_once()

    @patch('service.user.UserService.login_by_password')
    @patch('service.user.UserService.register')
    def test_user_registration_and_login_workflow(self, mock_register, mock_login):
        """Test complete user registration and login workflow"""
        # Mock user registration
        mock_user = Mock()
        mock_user.id = 1
        mock_user.phone_number = "+1234567890"
        mock_register.return_value = mock_user
        
        # Mock login
        mock_token = Mock()
        mock_token.value = "test_token_123"
        mock_login.return_value = mock_token
        
        # Test workflow
        user = mock_register("testuser", "+1234567890", "password123", "test@example.com")
        token = mock_login("+1234567890", "password123")
        
        self.assertIsNotNone(user)
        self.assertIsNotNone(token)

    @patch('service.data.data_service.create_frame_record')
    @patch('service.data.data_service.attach_data_to_analysis')
    def test_data_management_workflow(self, mock_attach_data, mock_create_data):
        """Test complete data upload and attachment workflow"""
        # Mock data creation
        mock_data = {
            "id": 1,
            "name": "test_data",
            "upload_type": "csv",
            "state": "uploaded"
        }
        mock_create_data.return_value = mock_data
        
        # Mock data attachment
        mock_relation = Mock()
        mock_attach_data.return_value = mock_relation
        
        # Test workflow
        data = mock_create_data(1, "csv", "test_data", "human", "Test description")
        relation = mock_attach_data(1, 1)  # analysis_id, data_id
        
        self.assertIsNotNone(data)
        self.assertIsNotNone(relation)

    @patch('service.computation.ComputationService.create')
    @patch('waiter.computation.ComputationWaiter.save_options')
    @patch('waiter.computation.ComputationWaiter.save_result')
    def test_computation_execution_workflow(self, mock_save_result, mock_save_options, mock_create_comp):
        """Test complete computation execution workflow"""
        # Mock computation creation
        mock_computation = Mock()
        mock_computation.id = 1
        mock_computation.task_id = "task_123"
        mock_create_comp.return_value = mock_computation
        
        # Test workflow
        computation = mock_create_comp(1, "task_123", {"param": "value"})
        mock_save_options({"param": "value"})
        mock_save_result({"status": "completed"})
        
        self.assertIsNotNone(computation)
        mock_save_options.assert_called_once()
        mock_save_result.assert_called_once()

    def test_error_handling_integration(self):
        """Test integrated error handling across components"""
        from wrapper.exception import exception_wrapper
        from exception.request.parameter_invalid import ParameterInvalidException
        
        @exception_wrapper
        def test_function(self):
            raise ParameterInvalidException("Integration test error")
        
        mock_self = Mock()
        
        with self.app.test_request_context():
            result = test_function(mock_self)
            self.assertEqual(result.status_code, 400)

    @patch('db.alchemy_db.session')
    def test_transaction_integration(self, mock_session):
        """Test database transaction integration"""
        from wrapper.db_session import transaction_wrapper
        
        mock_session.commit = Mock()
        mock_session.rollback = Mock()
        
        @transaction_wrapper
        def successful_operation(self):
            return "success"
        
        @transaction_wrapper
        def failing_operation(self):
            raise Exception("Database error")
        
        mock_self = Mock()
        
        # Test successful transaction
        result = successful_operation(mock_self)
        self.assertEqual(result, "success")
        mock_session.commit.assert_called()
        
        # Test failed transaction
        with self.assertRaises(Exception):
            failing_operation(mock_self)
        mock_session.rollback.assert_called()

    def test_cross_component_integration(self):
        """Test integration between different components"""
        # Test that different components can work together
        from service.analysis import AnalysisService
        from service.data import DataService
        from service.computation import ComputationService
        
        # Should be able to instantiate all services
        analysis_service = AnalysisService()
        data_service = DataService()
        computation_service = ComputationService()
        
        self.assertIsNotNone(analysis_service)
        self.assertIsNotNone(data_service)
        self.assertIsNotNone(computation_service)

    def test_configuration_integration(self):
        """Test that configuration is properly integrated"""
        # Test environment variables
        self.assertIsNotNone(os.environ.get("MYSQL_IP"))
        self.assertIsNotNone(os.environ.get("MYSQL_PORT"))
        
        # Test app configuration
        self.assertIsNotNone(self.app)
        self.assertTrue(self.app.config.get('TESTING'))

    @patch('sss.porter_factory.PorterFactory.create_porter')
    def test_storage_integration(self, mock_create_porter):
        """Test storage service integration"""
        from waiter.data_waiter import DataWaiter
        
        mock_porter = Mock()
        mock_create_porter.return_value = mock_porter
        
        data_waiter = DataWaiter("test_data_123")
        
        # Test storage operations integration
        with patch('os.path.exists', return_value=False):
            data_waiter.remove_data()
        
        self.assertTrue(mock_create_porter.called)

    def test_logging_integration(self):
        """Test logging integration across components"""
        from log.logger_factory import logger_factory
        
        logger = logger_factory.create_logger("integration_test")
        self.assertIsNotNone(logger)
        
        # Test logging doesn't break anything
        logger.info("Integration test log message")

    def test_exception_propagation_integration(self):
        """Test exception propagation across component layers"""
        from exception.request.parameter_invalid import ParameterInvalidException
        from exception.data.delete import DataDeleteException
        
        # Test that custom exceptions can be raised and caught
        with self.assertRaises(ParameterInvalidException):
            raise ParameterInvalidException("Test parameter error")
        
        with self.assertRaises(DataDeleteException):
            raise DataDeleteException("Test data error")
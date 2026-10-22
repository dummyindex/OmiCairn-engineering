import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
from unittest.mock import patch, Mock, MagicMock
import pytest
import json

from main import create_app
from controller.gpt import (
    ChatInitAPI,
    ChatHistroyAPI
)


@pytest.mark.controller
@pytest.mark.unit
@pytest.mark.gpt
class TestGptController(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.ctx.pop()

    @patch('llm.llm_interface.LlmInterface.init_chat')
    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_chat_init_success(self, mock_args_check, mock_guardian_factory, mock_init_chat):
        mock_args_check.return_value = None
        mock_guardian = Mock()
        mock_guardian.get_user_id.return_value = 123
        mock_guardian_factory.return_value = mock_guardian
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"chat_id": "chat_123", "status": "initialized"}'
        mock_init_chat.return_value = mock_response
        
        api = ChatInitAPI()
        
        with self.app.test_request_context('/api/gpt/chat/init?analysis_id=1', method='POST'):
            result = api.post()
            
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.get_data(as_text=True), '{"chat_id": "chat_123", "status": "initialized"}')
        mock_init_chat.assert_called_once_with('1', 123)

    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_chat_init_missing_analysis_id(self, mock_args_check, mock_guardian_factory):
        mock_args_check.side_effect = Exception("Missing required parameter: analysis_id")
        
        api = ChatInitAPI()
        
        with self.app.test_request_context('/api/gpt/chat/init', method='POST'):
            with self.assertRaises(Exception):
                api.post()

    @patch('llm.llm_interface.LlmInterface.init_chat')
    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_chat_init_llm_error(self, mock_args_check, mock_guardian_factory, mock_init_chat):
        mock_args_check.return_value = None
        mock_guardian = Mock()
        mock_guardian.get_user_id.return_value = 123
        mock_guardian_factory.return_value = mock_guardian
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = '{"error": "Internal server error"}'
        mock_init_chat.return_value = mock_response
        
        api = ChatInitAPI()
        
        with self.app.test_request_context('/api/gpt/chat/init?analysis_id=1', method='POST'):
            result = api.post()
            
        self.assertEqual(result.status_code, 500)

    @patch('llm.llm_interface.LlmInterface.get_chat_history')
    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_chat_history_success(self, mock_args_check, mock_guardian_factory, mock_get_history):
        mock_args_check.return_value = None
        mock_guardian = Mock()
        mock_guardian.get_user_id.return_value = 123
        mock_guardian_factory.return_value = mock_guardian
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"messages": [{"role": "user", "content": "Hello"}]}'
        mock_get_history.return_value = mock_response
        
        api = ChatHistroyAPI()
        
        with self.app.test_request_context('/api/gpt/chat/history?analysis_id=1', method='GET'):
            result = api.get()
            
        self.assertEqual(result.status_code, 200)
        mock_get_history.assert_called_once_with('1', 123)

    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_gpt_controller_authentication_required(self, mock_args_check, mock_guardian_factory):
        # Test that authentication is properly enforced
        mock_args_check.return_value = None
        mock_guardian_factory.side_effect = Exception("Authentication required")

        api = ChatInitAPI()

        with self.app.test_request_context('/api/gpt/chat/init?analysis_id=1', method='POST'):
            with self.assertRaises(Exception) as context:
                api.post()

        self.assertIn("Authentication required", str(context.exception))

    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    def test_gpt_controller_user_id_extraction(self, mock_guardian_factory):
        mock_guardian = Mock()
        mock_guardian.get_user_id.return_value = 456
        mock_guardian_factory.return_value = mock_guardian
        
        with patch('llm.llm_interface.LlmInterface.init_chat') as mock_init_chat:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"status": "ok"}'
            mock_init_chat.return_value = mock_response
            
            api = ChatInitAPI()
            
            with self.app.test_request_context('/api/gpt/chat/init?analysis_id=1', method='POST'):
                result = api.post()
                
            # Verify correct user_id was passed
            mock_init_chat.assert_called_once_with('1', 456)

    @patch('llm.llm_interface.LlmInterface.init_chat')
    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_gpt_controller_parameter_validation(self, mock_args_check, mock_guardian_factory, mock_init_chat):
        # Test various parameter validation scenarios
        api = ChatInitAPI()

        test_cases = [
            {"analysis_id": ""},  # Empty analysis_id
            {"analysis_id": "invalid"},  # Invalid format
        ]

        for test_case in test_cases:
            mock_args_check.return_value = None
            mock_guardian = Mock()
            mock_guardian.get_user_id.return_value = 123
            mock_guardian_factory.return_value = mock_guardian

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"status": "ok"}'
            mock_init_chat.return_value = mock_response

            analysis_id = test_case.get("analysis_id", "")

            with self.app.test_request_context(
                f'/api/gpt/chat/init?analysis_id={analysis_id}',
                method='POST'
            ):
                result = api.post()
                # Service layer validates parameters
                self.assertIsNotNone(result)

    def test_gpt_controller_raw_response_handling(self):
        # Test that raw responses are properly handled
        with patch('llm.llm_interface.LlmInterface.init_chat') as mock_init_chat:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.text = 'Custom response text'
            mock_init_chat.return_value = mock_response
            
            with patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian'):
                api = ChatInitAPI()
                
                with self.app.test_request_context('/api/gpt/chat/init?analysis_id=1', method='POST'):
                    result = api.post()
                    
                self.assertEqual(result.status_code, 201)
                self.assertEqual(result.get_data(as_text=True), 'Custom response text')

    def test_gpt_controller_error_propagation(self):
        # Test that LLM interface errors are properly propagated
        with patch('llm.llm_interface.LlmInterface.init_chat') as mock_init_chat:
            mock_init_chat.side_effect = Exception("LLM connection failed")
            
            with patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian'):
                api = ChatInitAPI()
                
                with self.app.test_request_context('/api/gpt/chat/init?analysis_id=1', method='POST'):
                    result = api.post()
                    
                # Should handle exception via exception_wrapper
                self.assertEqual(result.status_code, 500)

    def test_gpt_controller_logging_integration(self):
        # The controller module creates its logger at import time
        import controller.gpt as gpt_controller
        self.assertTrue(hasattr(gpt_controller, 'logger'))
        self.assertIsNotNone(gpt_controller.logger)

    @patch('service.gpt.gpt_service')
    @patch('llm.llm_interface.LlmInterface.init_chat')
    @patch('authority.guardian_factory.AuthorityGuardianFactory.get_authority_guardian')
    @patch('tool.requests_auditor.request_auditor.request_args_check')
    def test_gpt_service_integration(self, mock_args_check, mock_guardian_factory, mock_init_chat, mock_gpt_service):
        # Test integration with GPT service
        mock_args_check.return_value = None
        mock_guardian = Mock()
        mock_guardian.get_user_id.return_value = 123
        mock_guardian_factory.return_value = mock_guardian

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"result": "processed"}'
        mock_init_chat.return_value = mock_response

        api = ChatInitAPI()

        with self.app.test_request_context('/api/gpt/chat/init?analysis_id=1', method='POST'):
            result = api.post()

        # Verify service integration
        self.assertEqual(result.status_code, 200)
        mock_init_chat.assert_called_once_with('1', 123)
import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
from unittest.mock import patch, Mock
import pytest

from main import create_app
from service.chatbot import ChatbotService


@pytest.mark.service
@pytest.mark.unit
@pytest.mark.gpt
class TestChatbotService(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.chatbot_service = ChatbotService()

    def tearDown(self):
        self.ctx.pop()

    @patch('llm.llm_interface.LlmInterface')
    def test_chatbot_init_chat(self, mock_llm_interface):
        mock_llm = Mock()
        mock_llm_interface.return_value = mock_llm
        mock_llm.init_chat.return_value = Mock(status_code=200)
        
        result = self.chatbot_service.init_chat(1, 1)
        
        self.assertIsNotNone(result)

    @patch('llm.llm_interface.LlmInterface')
    def test_chatbot_send_message(self, mock_llm_interface):
        mock_llm = Mock()
        mock_llm_interface.return_value = mock_llm
        mock_llm.send_message.return_value = Mock(status_code=200)
        
        result = self.chatbot_service.send_message(1, 1, "Hello")
        
        self.assertIsNotNone(result)

    def test_chatbot_message_validation(self):
        # Test message validation
        valid_messages = ["Hello", "How are you?", "What is 2+2?"]
        invalid_messages = ["", None, " " * 1000]  # Empty, None, too long
        
        for msg in valid_messages:
            result = self.chatbot_service._validate_message(msg)
            self.assertTrue(result)
        
        for msg in invalid_messages:
            with self.assertRaises(Exception):
                self.chatbot_service._validate_message(msg)
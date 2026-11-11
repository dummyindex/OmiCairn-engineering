"""
Unit tests for chat API interactions in omicairn-worker.
Tests the communication between omicairn-worker and the LLM/agent service for chat functionalities.
"""

import pytest
from unittest.mock import Mock, patch

# Import classes under test
from handle_dynamic_generation.llm_interface import LlmInterface


class TestChatAPIInteractions:
    """Test chat-related API interactions between omicairn-worker and the LLM/agent service."""
    
    def test_init_chat(self, mock_requests):
        """Test chat initialization API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"chat_id": "chat_123", "status": "initialized"}
        }
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.init_chat(
            analysis_id="analysis_123",
            owner_id="user_123"
        )
        
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        assert "oldchat/init" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['analysis_id'] == "analysis_123"
        assert params['owner_id'] == "user_123"
        assert params['user_id'] == "user_123"

    def test_get_chat_history(self, mock_requests):
        """Test chat history retrieval API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"message": "Hello, can you help me analyze this data?", "timestamp": "2024-01-01T10:00:00Z"},
                {"message": "I'll help you analyze the data. What type of analysis are you looking for?", "timestamp": "2024-01-01T10:01:00Z"}
            ]
        }
        mock_requests['get'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.get_chat_history(
            analysis_id="analysis_123",
            owner_id="user_123"
        )
        
        assert response.status_code == 200
        mock_requests['get'].assert_called_once()
        call_args = mock_requests['get'].call_args
        assert "oldchat/history" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['analysis_id'] == "analysis_123"
        assert params['owner_id'] == "user_123"

    def test_send_message(self, mock_requests):
        """Test sending chat message API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"response": "I can help you create a data processing pipeline.", "chat_id": "chat_123"}
        }
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.send_message(
            analysis_id="analysis_123",
            owner_id="user_123",
            chat_id="chat_123",
            message="Can you help me create a data processing pipeline?"
        )
        
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        assert "oldchat/" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['message'] == "Can you help me create a data processing pipeline?"
        assert params['chat_id'] == "chat_123"

    def test_init_global_chat(self, mock_requests):
        """Test global chat initialization API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"chat_id": "global_chat_123"}}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.init_global_chat(
            analysis_id="analysis_123",
            user_id="user_123"
        )
        
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        assert "oldchat/init/global" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['analysis_id'] == "analysis_123"
        assert params['user_id'] == "user_123"

    def test_send_global_message(self, mock_requests):
        """Test sending global chat message API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"response": "Global analysis context established"}}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.send_global_message(
            analysis_id="analysis_123",
            user_id="user_123",
            chat_id="global_chat_123",
            message="Set up global analysis context"
        )
        
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        assert "oldchat/global" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['message'] == "Set up global analysis context"
        assert params['chat_id'] == "global_chat_123"

    def test_init_local_chat(self, mock_requests):
        """Test local chat initialization API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"chat_id": "local_chat_123"}}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.init_local_chat(
            analysis_id="analysis_123",
            node_id="node_123",
            owner_id="user_123"
        )
        
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        assert "oldchat/init/local" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['node_id'] == "node_123"
        assert params['analysis_id'] == "analysis_123"
        assert params['owner_id'] == "user_123"

    def test_send_local_message(self, mock_requests):
        """Test sending local chat message API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"response": "Local node analysis completed"}}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.send_local_message(
            analysis_id="analysis_123",
            owner_id="user_123",
            chat_id="local_chat_123",
            message="Analyze this specific node"
        )
        
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        assert "oldchat/local" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['message'] == "Analyze this specific node"
        assert params['chat_id'] == "local_chat_123"

    def test_get_complex_chat_list(self, mock_requests):
        """Test complex chat list retrieval API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"thread_id": "thread_123", "title": "RNA-seq Analysis Discussion"},
                {"thread_id": "thread_456", "title": "Data Preprocessing Chat"}
            ]
        }
        mock_requests['get'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.get_complex_chat_list(
            analysis_id="analysis_123",
            owner_id="user_123"
        )
        
        assert response.status_code == 200
        mock_requests['get'].assert_called_once()
        call_args = mock_requests['get'].call_args
        assert "chat/history/all" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['analysis_id'] == "analysis_123"
        assert params['owner_id'] == "user_123"

    def test_get_complex_chat_message_list(self, mock_requests):
        """Test complex chat message list retrieval API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"message": "How should I preprocess this RNA-seq data?", "timestamp": "2024-01-01T14:00:00Z"},
                {"message": "Start with quality control using FastQC", "timestamp": "2024-01-01T14:01:00Z"},
                {"message": "Then align reads using STAR aligner", "timestamp": "2024-01-01T14:02:00Z"}
            ]
        }
        mock_requests['get'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.get_complex_chat_message_list(
            thread_id="thread_123",
            user_id="user_123"
        )
        
        assert response.status_code == 200
        mock_requests['get'].assert_called_once()
        call_args = mock_requests['get'].call_args
        assert "chat/history" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['thread_id'] == "thread_123"
        assert params['user_id'] == "user_123"

    def test_init_complex_chat(self, mock_requests):
        """Test complex chat initialization API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"thread_id": "complex_thread_123"}}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.init_complex_chat(
            analysis_id="analysis_123",
            owner_id="user_123"
        )
        
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        assert "chat/init/analysis" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['analysis_id'] == "analysis_123"
        assert params['owner_id'] == "user_123"

    def test_send_complex_message(self, mock_requests):
        """Test sending complex chat message API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"response": "Complex analysis workflow initiated"}}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.send_complex_message(
            analysis_id="analysis_123",
            owner_id="user_123",
            thread_id="thread_123",
            message="Initiate complex multi-step analysis workflow"
        )
        
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        assert "chat/analysis" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['message'] == "Initiate complex multi-step analysis workflow"
        assert params['thread_id'] == "thread_123"


class TestChatErrorHandling:
    """Test error handling scenarios in chat API interactions."""
    
    def test_chat_initialization_error(self, mock_requests):
        """Test handling of chat initialization errors."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Invalid analysis_id"}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.init_chat(
            analysis_id="invalid_analysis",
            owner_id="user_123"
        )
        
        assert response.status_code == 400
        assert response.json()["message"] == "Invalid analysis_id"

    def test_message_send_timeout(self, mock_requests):
        """Test handling of message send timeouts."""
        import requests
        
        mock_requests['post'].side_effect = requests.Timeout("Request timeout")
        
        llm_interface = LlmInterface()
        
        with pytest.raises(requests.Timeout):
            llm_interface.send_message(
                analysis_id="analysis_123",
                owner_id="user_123",
                chat_id="chat_123",
                message="Test message"
            )

    def test_chat_history_retrieval_error(self, mock_requests):
        """Test handling of chat history retrieval errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Chat history not found"}
        mock_requests['get'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.get_chat_history(
            analysis_id="non_existent_analysis",
            owner_id="user_123"
        )
        
        assert response.status_code == 404
        assert response.json()["message"] == "Chat history not found"


class TestChatIntegrationScenarios:
    """Test realistic chat integration scenarios."""
    
    def test_complete_chat_workflow(self, mock_requests):
        """Test a complete chat workflow: init -> send -> get history."""
        llm_interface = LlmInterface()
        
        # Mock init response
        init_response = Mock()
        init_response.status_code = 200
        init_response.json.return_value = {"data": {"chat_id": "chat_123"}}
        
        # Mock send response
        send_response = Mock()
        send_response.status_code = 200
        send_response.json.return_value = {"data": {"response": "AI response to user query"}}
        
        # Mock history response
        history_response = Mock()
        history_response.status_code = 200
        history_response.json.return_value = {
            "data": [
                {"message": "User query", "sender": "user"},
                {"message": "AI response to user query", "sender": "assistant"}
            ]
        }
        
        mock_requests['post'].side_effect = [init_response, send_response]
        mock_requests['get'].return_value = history_response
        
        # Execute workflow
        init_resp = llm_interface.init_chat("analysis_123", "user_123")
        assert init_resp.status_code == 200
        
        send_resp = llm_interface.send_message("analysis_123", "user_123", "chat_123", "User query")
        assert send_resp.status_code == 200
        
        history_resp = llm_interface.get_chat_history("analysis_123", "user_123")
        assert history_resp.status_code == 200
        assert len(history_resp.json()["data"]) == 2

    def test_multi_level_chat_interaction(self, mock_requests):
        """Test multi-level chat interaction (global, local, complex)."""
        llm_interface = LlmInterface()
        
        # Mock responses for different chat types
        global_response = Mock()
        global_response.status_code = 200
        global_response.json.return_value = {"data": {"chat_id": "global_chat_123"}}
        
        local_response = Mock()
        local_response.status_code = 200
        local_response.json.return_value = {"data": {"chat_id": "local_chat_123"}}
        
        complex_response = Mock()
        complex_response.status_code = 200
        complex_response.json.return_value = {"data": {"thread_id": "complex_thread_123"}}
        
        mock_requests['post'].side_effect = [global_response, local_response, complex_response]
        
        # Test all chat types
        global_resp = llm_interface.init_global_chat("analysis_123", "user_123")
        assert global_resp.status_code == 200
        
        local_resp = llm_interface.init_local_chat("analysis_123", "node_123", "user_123")
        assert local_resp.status_code == 200
        
        complex_resp = llm_interface.init_complex_chat("analysis_123", "user_123")
        assert complex_resp.status_code == 200
        
        # Verify all three API calls were made
        assert mock_requests['post'].call_count == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
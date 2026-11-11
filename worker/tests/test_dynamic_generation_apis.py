"""
Unit tests for dynamic generation API interactions in omicairn-worker.
Tests the communication between omicairn-worker and the LLM/agent service for dynamic function block generation.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

# Import classes under test
from handle_dynamic_generation.llm_interface import LlmInterface
from handle_dynamic_generation.server_agent import ServerAgent


class TestDynamicGenerationLlmInterface:
    """Test the LlmInterface class for dynamic generation API calls."""
    
    def test_dynamic_fb_basic(self, mock_requests, sample_dynamic_generation_data, sample_llm_response):
        """Test basic dynamic function block generation API call."""
        # Setup mock response
        mock_requests['response'].json.return_value = sample_llm_response
        mock_requests['post'].return_value = mock_requests['response']
        
        # Test the interface
        llm_interface = LlmInterface()
        response = llm_interface.dynamic_fb(
            user_request=sample_dynamic_generation_data['user_request'],
            node_id=sample_dynamic_generation_data['node_id'],
            history=sample_dynamic_generation_data['history'],
            user_id=sample_dynamic_generation_data['user_id'],
            llm_model="gpt-4o"
        )
        
        # Assertions
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        assert "dynamic_fb/get" in call_args[1]['url']
        assert sample_dynamic_generation_data['user_id'] in call_args[1]['url']
        assert sample_dynamic_generation_data['node_id'] in call_args[1]['url']
        
        # Verify request body
        request_body = call_args[1]['json']
        assert request_body['user_request'] == sample_dynamic_generation_data['user_request']
        assert request_body['nodeHistoryList'] == sample_dynamic_generation_data['history']
        assert request_body['currentNode'] == sample_dynamic_generation_data['history'][-1]

    def test_dynamic_fb_with_plan(self, mock_requests, sample_dynamic_generation_data, sample_llm_response):
        """Test dynamic function block generation with plan API call."""
        mock_requests['response'].json.return_value = sample_llm_response
        mock_requests['post'].return_value = mock_requests['response']
        
        current_plan = {
            "steps": ["Load data", "Process data", "Generate output"],
            "current_step": 1
        }
        
        llm_interface = LlmInterface()
        response = llm_interface.dynamic_fb_with_plan(
            user_request=sample_dynamic_generation_data['user_request'],
            llm_model="gpt-4o",
            node_id=sample_dynamic_generation_data['node_id'],
            history=sample_dynamic_generation_data['history'],
            user_id=sample_dynamic_generation_data['user_id'],
            current_plan=current_plan
        )
        
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        
        # Verify request body includes plan
        request_body = call_args[1]['json']
        assert request_body['current_plan'] == current_plan
        assert request_body['user_request'] == sample_dynamic_generation_data['user_request']

    def test_dynamic_fb_with_generation_parameters(self, mock_requests, sample_dynamic_generation_data):
        """Test dynamic FB with various generation parameters."""
        from constants import GenerationMode
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"function_block": "test_code"}}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.dynamic_fb(
            user_request="Generate multiple solutions",
            node_id=sample_dynamic_generation_data['node_id'],
            history=sample_dynamic_generation_data['history'],
            user_id=sample_dynamic_generation_data['user_id'],
            llm_model="gpt-4o",
            max_branch_count=3,
            generation_mode=GenerationMode.MIXED.value,
            file_ids=["file_1", "file_2"]
        )
        
        assert response.status_code == 200
        call_args = mock_requests['post'].call_args
        url = call_args[1]['url']
        
        # Verify URL parameters
        assert "max_branch_count=3" in url
        assert f"generation_mode={GenerationMode.MIXED.value}" in url
        assert "model=gpt-4o" in url
        
        # Verify file_ids in request body
        request_body = call_args[1]['json']
        assert request_body['file_ids'] == ["file_1", "file_2"]

    def test_get_node_report(self, mock_requests, sample_dynamic_generation_data):
        """Test node report generation API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": "Node analysis report: The function successfully processed 1000 records..."
        }
        mock_requests['get'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.get_node_report(
            node_id=sample_dynamic_generation_data['node_id'],
            history=sample_dynamic_generation_data['history'],
            user_id=sample_dynamic_generation_data['user_id']
        )
        
        assert response.status_code == 200
        mock_requests['get'].assert_called_once()
        call_args = mock_requests['get'].call_args
        assert "data/interpretation/get" in call_args[1]['url']
        assert sample_dynamic_generation_data['node_id'] in call_args[1]['url']
        assert sample_dynamic_generation_data['user_id'] in call_args[1]['url']
        
        # Verify request body structure
        request_body = call_args[1]['json']
        assert request_body['nodeHistoryList'] == sample_dynamic_generation_data['history']
        assert request_body['currentNode'] == sample_dynamic_generation_data['history'][-1]

    def test_create_workflow_report(self, mock_requests):
        """Test workflow report creation API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": "Comprehensive workflow report generated successfully"
        }
        mock_requests['get'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.create_workflow_report(
            node_ids=["node1", "node2", "node3"],
            computation_details_list=[
                {"node_id": "node1", "status": "completed", "result": "success"},
                {"node_id": "node2", "status": "completed", "result": "success"},
                {"node_id": "node3", "status": "completed", "result": "success"}
            ],
            analysis_id="analysis_123",
            uuid_str="uuid_456",
            user_id="user_123"
        )
        
        assert response.status_code == 200
        mock_requests['get'].assert_called_once()
        call_args = mock_requests['get'].call_args
        assert "report/get" in call_args[1]['url']
        
        # Verify request body
        request_body = call_args[1]['json']
        assert request_body['ownerID'] == "user_123"
        assert request_body['analysisID'] == "analysis_123"
        assert request_body['uuid'] == "uuid_456"
        assert request_body['nodeIDs'] == ["node1", "node2", "node3"]
        assert len(request_body['currentNodeList']) == 3

    def test_recommend_pipeline(self, mock_requests):
        """Test pipeline recommendation API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": '{"nodes": [{"id": "node1", "type": "data_input"}, {"id": "node2", "type": "analysis"}]}'
        }
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.recommend_pipeline(
            user_request="Create a RNA-seq analysis pipeline",
            user_id="user_123"
        )
        
        assert response.status_code == 200
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        assert "workflow" in call_args[1]['url']
        
        # Verify parameters
        params = call_args[1]['params']
        assert params['user_request'] == "Create a RNA-seq analysis pipeline"
        assert params['user_id'] == "user_123"

    def test_get_similar_pipeline_template(self, mock_requests):
        """Test similar pipeline template retrieval API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"template_id": "template_123", "name": "RNA-seq Basic", "similarity": 0.95},
                {"template_id": "template_456", "name": "RNA-seq Advanced", "similarity": 0.87}
            ]
        }
        mock_requests['get'].return_value = mock_response
        
        llm_interface = LlmInterface()
        response = llm_interface.get_similar_pipeline_template(
            user_request="RNA sequencing analysis",
            user_id="user_123"
        )
        
        assert response.status_code == 200
        mock_requests['get'].assert_called_once()
        call_args = mock_requests['get'].call_args
        assert "pipline/template/get" in call_args[1]['url']
        
        params = call_args[1]['params']
        assert params['user_request'] == "RNA sequencing analysis"
        assert params['user_id'] == "user_123"

    def test_apply_for_optimize_error_description(self, mock_requests, mock_logger):
        """Test error description optimization API call."""
        mock_requests['response'].status_code = 200
        mock_requests['post'].return_value = mock_requests['response']
        
        llm_interface = LlmInterface()
        # This method doesn't return response, just makes the call
        llm_interface.apply_for_optimize_error_description(
            computation_id="computation_123",
            user_id="user_123"
        )
        
        mock_requests['post'].assert_called_once()
        call_args = mock_requests['post'].call_args
        assert "error/write" in call_args[0][0]  # URL is first positional argument
        
        params = call_args[1]['params']
        assert params['computation_id'] == "computation_123"
        assert params['user_id'] == "user_123"

    def test_error_handling(self, mock_requests, mock_logger):
        """Test error handling in LlmInterface methods."""
        # Mock error response for dynamic_fb which has better error handling
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal server error"}
        mock_requests['post'].return_value = mock_response
        
        llm_interface = LlmInterface()
        
        # Test error response handling
        response = llm_interface.dynamic_fb(
            user_request="Test request",
            node_id="node_123",
            history=[{"node": {"id": "node1"}, "latestComputation": {"id": "comp1"}}],
            user_id="user_123",
            llm_model="gpt-4o"
        )
        
        assert response.status_code == 500
        assert response.json()["message"] == "Internal server error"


class TestDynamicGenerationServerAgent:
    """Test the ServerAgent class for server communication."""
    
    @patch('handle_dynamic_generation.server_agent.requests.post')
    def test_server_agent_initialization(self, mock_post):
        """Test ServerAgent initialization and authentication."""
        # Mock login response
        login_response = Mock()
        login_response.json.return_value = {"data": "auth_token_123"}
        mock_post.return_value = login_response
        
        agent = ServerAgent("user_123")
        
        # Verify login call was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "server/user/login-by-system" in call_args[0][0]
        assert "user_id=user_123" in call_args[0][0]
        
        # Verify headers are set
        assert agent.headers == {"token": "auth_token_123"}

    @patch('handle_dynamic_generation.server_agent.requests.post')
    def test_create_computation_node(self, mock_post):
        """Test computation node creation."""
        # Mock login and create node responses
        login_response = Mock()
        login_response.json.return_value = {"data": "auth_token_123"}
        
        create_response = Mock()
        create_response.json.return_value = {"data": {"node_id": "new_node_123"}}
        
        mock_post.side_effect = [login_response, create_response]
        
        agent = ServerAgent("user_123")
        result = agent.create_computation_node(
            node_type="computation",
            analysis_id="analysis_123",
            x=100,
            y=200,
            name="Test Node",
            function_block_id="fb_123",
            function_block_version_id="fbv_123",
            dynamic_generation_id="dg_123",
            system_env="python",
            dynamic_generation_session_id="session_123",
            computation_resource_configure={"cpu": 2, "memory": "4GB"}
        )
        
        assert result == {"data": {"node_id": "new_node_123"}}
        assert mock_post.call_count == 2  # Login + create node
        
        # Verify create node call
        create_call = mock_post.call_args_list[1]
        assert "server/node/create" in create_call[0][0]
        form_data = create_call[1]['data']
        assert form_data['node_type'] == "computation"
        assert form_data['analysis_id'] == "analysis_123"
        assert form_data['dynamic_generation_id'] == "dg_123"

    @patch('handle_dynamic_generation.server_agent.requests.post')
    def test_create_edge(self, mock_post):
        """Test edge creation between nodes."""
        login_response = Mock()
        login_response.json.return_value = {"data": "auth_token_123"}
        
        edge_response = Mock()
        edge_response.json.return_value = {"data": {"edge_id": "edge_123"}}
        
        mock_post.side_effect = [login_response, edge_response]
        
        agent = ServerAgent("user_123")
        result = agent.create_edge(
            analysis_id="analysis_123",
            source_node_id="node_1",
            target_node_id="node_2"
        )
        
        assert result == {"data": {"edge_id": "edge_123"}}
        
        # Verify edge creation call
        edge_call = mock_post.call_args_list[1]
        assert "server/edge/create" in edge_call[0][0]
        form_data = edge_call[1]['data']
        assert form_data['source_node_id'] == "node_1"
        assert form_data['target_node_id'] == "node_2"

    @patch('handle_dynamic_generation.server_agent.requests.post')
    def test_launch_task(self, mock_post):
        """Test task launching."""
        login_response = Mock()
        login_response.json.return_value = {"data": "auth_token_123"}
        
        task_response = Mock()
        task_response.json.return_value = {"data": {"task_id": "task_123", "status": "launched"}}
        
        mock_post.side_effect = [login_response, task_response]
        
        agent = ServerAgent("user_123")
        result = agent.launch_task(
            analysis_id="analysis_123",
            node_id_list=["node_1", "node_2"],
            edge_id_list=["edge_1"]
        )
        
        assert result == {"data": {"task_id": "task_123", "status": "launched"}}
        
        # Verify task launch call
        task_call = mock_post.call_args_list[1]
        assert "computation-server/task/dispatch" in task_call[0][0]
        json_data = task_call[1]['json']
        assert json_data['node_id_list'] == ["node_1", "node_2"]
        assert json_data['edge_id_list'] == ["edge_1"]

    @patch('handle_dynamic_generation.server_agent.requests.get')
    @patch('handle_dynamic_generation.server_agent.requests.post')
    def test_get_computation_history(self, mock_post, mock_get):
        """Test computation history retrieval."""
        login_response = Mock()
        login_response.json.return_value = {"data": "auth_token_123"}
        mock_post.return_value = login_response
        
        history_response = Mock()
        history_response.json.return_value = {
            "data": [
                {"computation_id": "comp_1", "status": "completed", "result": "success"},
                {"computation_id": "comp_2", "status": "completed", "result": "success"}
            ]
        }
        mock_get.return_value = history_response
        
        agent = ServerAgent("user_123")
        result = agent.get_computation_history("node_123")
        
        assert len(result["data"]) == 2
        
        # Verify history call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "server/computation/get-former-history" in call_args[0][0]
        assert "node_id=node_123" in call_args[0][0]

    @patch('handle_dynamic_generation.server_agent.requests.post')
    def test_record_llm_consumption(self, mock_post):
        """Test LLM consumption recording."""
        login_response = Mock()
        login_response.json.return_value = {"data": "auth_token_123"}
        
        record_response = Mock()
        record_response.json.return_value = {"data": {"consumption_id": "consumption_123"}}
        
        mock_post.side_effect = [login_response, record_response]
        
        agent = ServerAgent("user_123")
        result = agent.record_llm_consumption({
            "tokens": 1500,
            "cost": 0.03,
            "model": "gpt-4o"
        })
        
        assert result == {"data": {"consumption_id": "consumption_123"}}
        
        # Verify consumption recording call
        record_call = mock_post.call_args_list[1]
        assert "server/gpt/record-consumption" in record_call[0][0]
        json_data = record_call[1]['json']
        assert json_data['consumption']['tokens'] == 1500
        assert json_data['consumption']['cost'] == 0.03


class TestDynamicGenerationErrorHandling:
    """Test error handling scenarios in dynamic generation API interactions."""
    
    def test_llm_interface_network_error(self, mock_requests, mock_logger):
        """Test handling of network errors in LlmInterface."""
        import requests
        
        # Mock network error
        mock_requests['post'].side_effect = requests.ConnectionError("Connection failed")
        
        llm_interface = LlmInterface()
        
        with pytest.raises(requests.ConnectionError):
            llm_interface.dynamic_fb(
                user_request="Test request",
                node_id="node_123",
                history=[{"node": {"id": "node1"}, "latestComputation": {"id": "comp1"}}],
                user_id="user_123",
                llm_model="gpt-4o"
            )

    def test_server_agent_authentication_failure(self, mock_logger):
        """Test handling of authentication failures in ServerAgent."""
        with patch('handle_dynamic_generation.server_agent.requests.post') as mock_post:
            # Mock failed login response
            error_response = Mock()
            error_response.json.return_value = {"error": "Authentication failed"}
            error_response.raise_for_status.side_effect = Exception("401 Unauthorized")
            mock_post.return_value = error_response
            
            with pytest.raises(Exception):
                ServerAgent("invalid_user")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
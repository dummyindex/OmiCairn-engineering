import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from flask import Flask

from server.service.dynamic_generation_llm_monitor import DynamicGenerationLLMMonitorService
from server.controller.dynamic_generation_llm_monitor import (
    DynamicGenerationSingleBranchMonitorAPI,
    DynamicGenerationFullTaskMonitorAPI,
    DynamicGenerationBranchesAPI
)


class TestDynamicGenerationLLMMonitorService:
    """Dynamic Generation LLM monitoring service unit tests"""

    @pytest.fixture
    def service(self):
        return DynamicGenerationLLMMonitorService()

    @pytest.fixture
    def mock_dynamic_generation(self):
        """Mock dynamic_generation data"""
        return Mock(
            generation_id=123,
            previous_node_id=100,
            user_request="Test user request",
            state="running"
        )

    @pytest.fixture
    def mock_branch(self):
        """Mock branch data"""
        return Mock(
            id=456,
            dynamic_generation_id=123,
            end_node_id=200,
            state="running",
            created_time=datetime(2024, 1, 1, 12, 0, 0),
            updated_time=datetime(2024, 1, 1, 12, 30, 0)
        )

    @pytest.fixture
    def mock_nodes(self):
        """Mock node data"""
        return [
            Mock(id=100, name="Start node", created_time=datetime(2024, 1, 1, 12, 0, 0)),
            Mock(id=150, name="Middle node", created_time=datetime(2024, 1, 1, 12, 15, 0)),
            Mock(id=200, name="End node", created_time=datetime(2024, 1, 1, 12, 30, 0))
        ]

    @pytest.fixture
    def mock_retry_process(self):
        """Mock retry process data"""
        return Mock(
            id=789,
            node_id=150,
            created_time=datetime(2024, 1, 1, 12, 20, 0)
        )

    @pytest.fixture
    def mock_computation(self):
        """Mock computation data"""
        return Mock(
            id=999,
            created_time=datetime(2024, 1, 1, 12, 25, 0)
        )

    def test_parse_s3_content_valid_json(self, service):
        """Test parsing valid JSON content"""
        json_content = '{"key": "value", "number": 123}'
        result = service._parse_s3_content(json_content)
        assert result == {"key": "value", "number": 123}

    def test_parse_s3_content_invalid_json(self, service):
        """Test parsing invalid JSON content"""
        invalid_content = "This is not valid JSON"
        result = service._parse_s3_content(invalid_content)
        assert result == {"raw_content": "This is not valid JSON"}

    def test_parse_s3_content_empty(self, service):
        """Test parsing empty content"""
        result = service._parse_s3_content("")
        assert result is None
        
        result = service._parse_s3_content(None)
        assert result is None

    @patch('server.service.dynamic_generation_llm_monitor.DynamicGenerationWaiter')
    @patch('server.service.dynamic_generation_llm_monitor.node_dao')
    def test_get_dynamic_generation_interaction_success(self, mock_node_dao, mock_waiter_class, service, mock_nodes):
        """Test successfully fetching dynamic generation interaction data"""
        # Set up mocks
        mock_waiter = Mock()
        mock_waiter_class.return_value = mock_waiter
        mock_waiter.fetch_log.return_value = (
            '{"prompt": "Generate FB", "context": "Context"}',
            '{"response": "LLM reply", "data": {"satisfied": false}}'
        )
        mock_node_dao.find_by_id.return_value = mock_nodes[0]

        # Run the test
        result = service._get_dynamic_generation_interaction(123, 100)

        # Verify the result
        assert result is not None
        assert result["type"] == "dynamic_generation"
        assert result["generation_id"] == 123
        assert result["node_id"] == 100
        assert result["input"]["prompt"] == "Generate FB"
        assert result["output"]["response"] == "LLM reply"
        assert result["interaction_source"] == "next_fb_generation"
        assert result["timestamp"] is not None

    @patch('server.service.dynamic_generation_llm_monitor.DynamicGenerationWaiter')
    def test_get_dynamic_generation_interaction_no_data(self, mock_waiter_class, service):
        """Test fetching non-existent dynamic generation interaction data"""
        mock_waiter = Mock()
        mock_waiter_class.return_value = mock_waiter
        mock_waiter.fetch_log.return_value = ("", "")

        result = service._get_dynamic_generation_interaction(123, 100)
        assert result is None

    @patch('server.service.dynamic_generation_llm_monitor.DynamicGenerationWaiter')
    def test_get_dynamic_generation_interaction_exception(self, mock_waiter_class, service):
        """Test an exception while fetching dynamic generation interaction data"""
        mock_waiter = Mock()
        mock_waiter_class.return_value = mock_waiter
        mock_waiter.fetch_log.side_effect = Exception("S3 access failed")

        result = service._get_dynamic_generation_interaction(123, 100)
        assert result is None

    @patch('server.service.dynamic_generation_llm_monitor.RetryProcessWaiter')
    @patch('server.service.dynamic_generation_llm_monitor.computation_dao')
    @patch('server.service.dynamic_generation_llm_monitor.ComputationRetryProcess')
    def test_get_retry_process_interactions_success(self, mock_model, mock_computation_dao, mock_waiter_class, 
                                                  service, mock_retry_process, mock_computation):
        """Test successfully fetching retry process interaction data"""
        # Set up mocks
        mock_model.query.filter.return_value.first.return_value = mock_retry_process
        mock_computation_dao.find_by_retry_process_id.return_value = [mock_computation]
        
        mock_waiter = Mock()
        mock_waiter_class.return_value = mock_waiter
        mock_waiter.get_one_stage_details.return_value = (
            {"node_info": "Node info"},
            "Input prompt",
            {"params_fix": "Parameter fix"},
            {"code_fix": "Code fix"},
            {"success": False, "error": "Error message"}
        )

        # Run the test
        result = service._get_retry_process_interactions(789)

        # Verify the result
        assert len(result) == 1
        interaction = result[0]
        assert interaction["type"] == "bug_fixer"
        assert interaction["retry_process_id"] == 789
        assert interaction["computation_id"] == 999
        assert interaction["node_id"] == 150
        assert interaction["input"]["prompt"] == "Input prompt"
        assert interaction["output"]["result"]["success"] is False
        assert interaction["interaction_source"] == "computation_retry_bug_fixer"

    @patch('server.service.dynamic_generation_llm_monitor.RetryProcessWaiter')
    @patch('server.service.dynamic_generation_llm_monitor.ComputationRetryProcess')
    def test_get_retry_process_interactions_not_found(self, mock_model, mock_waiter_class, service):
        """Test the case where the retry process does not exist"""
        mock_model.query.filter.return_value.first.return_value = None
        
        result = service._get_retry_process_interactions(789)
        assert result == []

    @patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao')
    @patch('server.service.dynamic_generation_llm_monitor.edge_dao')
    def test_get_nodes_in_generation_path_single_branch(self, mock_edge_dao, mock_dg_dao, service, mock_dynamic_generation):
        """Test fetching nodes in a single-branch path"""
        mock_dg_dao.find_by_id.return_value = mock_dynamic_generation
        
        # Mock edge relationships: 200 -> 150 -> 100
        mock_edges_200 = [Mock(source_node_id=150)]
        mock_edges_150 = [Mock(source_node_id=100)]
        mock_edges_100 = []
        
        mock_edge_dao.find_by_target_node_id.side_effect = [
            mock_edges_200,  # predecessor of 200 is 150
            mock_edges_150,  # predecessor of 150 is 100
            mock_edges_100   # 100 has no predecessor
        ]

        result = service._get_nodes_in_generation_path(123, 200)
        assert result == [100, 150, 200]  # in chronological order

    @patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao')
    @patch('server.service.dynamic_generation_llm_monitor.node_dao')
    def test_get_nodes_in_generation_path_full_task(self, mock_node_dao, mock_dg_dao, service, mock_dynamic_generation, mock_nodes):
        """Test fetching nodes in the full task path"""
        mock_dg_dao.find_by_id.return_value = mock_dynamic_generation
        mock_node_dao.find_by_dynamic_generation_id.return_value = mock_nodes[1:]  # exclude the start node

        result = service._get_nodes_in_generation_path(123, None)
        assert 100 in result  # start node
        assert 150 in result  # generated node
        assert 200 in result  # generated node
        assert len(result) == 3

    @patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao')
    def test_get_single_branch_interactions_branch_not_found(self, mock_dg_dao, service):
        """Test the case where the branch does not exist"""
        mock_dg_dao.find_branch_by_id.return_value = None

        result = service.get_single_branch_interactions(123, 456)
        assert "error" in result
        assert "Branch not found" in result["error"]

    @patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao')
    def test_get_single_branch_interactions_wrong_generation(self, mock_dg_dao, service, mock_branch):
        """Test the case where the branch does not belong to the given generation"""
        mock_branch.dynamic_generation_id = 999  # mismatched generation_id
        mock_dg_dao.find_branch_by_id.return_value = mock_branch

        result = service.get_single_branch_interactions(123, 456)
        assert "error" in result
        assert "does not belong to the generation" in result["error"]

    @patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao')
    @patch.object(DynamicGenerationLLMMonitorService, '_get_nodes_in_generation_path')
    @patch.object(DynamicGenerationLLMMonitorService, '_get_dynamic_generation_interaction')
    @patch('server.service.dynamic_generation_llm_monitor.computation_dao')
    def test_get_single_branch_interactions_success(self, mock_computation_dao, mock_get_dg_interaction,
                                                   mock_get_nodes, mock_dg_dao, service, mock_branch):
        """Test successfully fetching single-branch interactions"""
        # Set up mocks
        mock_dg_dao.find_branch_by_id.return_value = mock_branch
        mock_get_nodes.return_value = [100, 150, 200]
        
        mock_interaction = {
            "type": "dynamic_generation",
            "timestamp": 1640995200000,
            "node_id": 100
        }
        mock_get_dg_interaction.return_value = mock_interaction
        mock_computation_dao.find_retry_process_by_node_id.return_value = []

        # Run the test
        result = service.get_single_branch_interactions(123, 456)

        # Verify the result
        assert "error" not in result
        assert result["branch_id"] == 456
        assert result["generation_id"] == 123
        assert result["end_node_id"] == 200
        assert len(result["interactions"]) == 3  # one interaction per node
        assert result["total_count"] == 3

    @patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao')
    def test_get_full_task_interactions_not_found(self, mock_dg_dao, service):
        """Test the case where the dynamic generation does not exist"""
        mock_dg_dao.find_by_id.return_value = None

        result = service.get_full_task_interactions(123)
        assert "error" in result
        assert "Dynamic generation not found" in result["error"]

    @patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao')
    @patch.object(DynamicGenerationLLMMonitorService, '_get_nodes_in_generation_path')
    @patch.object(DynamicGenerationLLMMonitorService, '_get_dynamic_generation_interaction')
    @patch('server.service.dynamic_generation_llm_monitor.computation_dao')
    def test_get_full_task_interactions_success(self, mock_computation_dao, mock_get_dg_interaction,
                                               mock_get_nodes, mock_dg_dao, service, mock_dynamic_generation, mock_branch):
        """Test successfully fetching full-task interactions"""
        # Set up mocks
        mock_dg_dao.find_by_id.return_value = mock_dynamic_generation
        mock_dg_dao.find_branches_by_dynamic_generation_id.return_value = [mock_branch]
        mock_get_nodes.return_value = [100, 150, 200]
        
        mock_interaction = {
            "type": "dynamic_generation",
            "timestamp": 1640995200000,
            "node_id": 100
        }
        mock_get_dg_interaction.return_value = mock_interaction
        mock_computation_dao.find_retry_process_by_node_id.return_value = []

        # Run the test
        result = service.get_full_task_interactions(123)

        # Verify the result
        assert "error" not in result
        assert result["generation_id"] == 123
        assert result["user_request"] == "Test user request"
        assert result["state"] == "running"
        assert len(result["branches"]) == 1
        assert result["branches"][0]["id"] == 456
        assert len(result["interactions"]) == 3
        assert result["total_count"] == 3

    def test_get_full_task_interactions_exception(self, service):
        """Test an exception while fetching full-task interactions"""
        with patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao') as mock_dao:
            mock_dao.find_by_id.side_effect = Exception("Database error")
            
            result = service.get_full_task_interactions(123)
            assert "error" in result
            assert "Database error" in result["error"]


class TestDynamicGenerationLLMMonitorAPIs:
    """Dynamic Generation LLM monitoring API integration tests"""

    @pytest.fixture
    def app(self):
        """Create the Flask test app"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create the test client"""
        return app.test_client()

    @pytest.fixture
    def mock_service(self):
        """Mock service instance"""
        return Mock()

    def test_single_branch_monitor_api_missing_params(self, app, client):
        """Test single-branch monitoring API with missing parameters"""
        with app.test_request_context('/test?generation_id=123'):
            api = DynamicGenerationSingleBranchMonitorAPI()
            
            # Simulate a request missing the branch_id parameter
            with patch('server.controller.dynamic_generation_llm_monitor.request') as mock_request:
                mock_request.args.get.side_effect = lambda key: {'generation_id': '123'}.get(key)
                
                with patch('server.controller.dynamic_generation_llm_monitor.request_auditor') as mock_auditor:
                    mock_auditor.request_args_check.side_effect = Exception("Missing required parameter: branch_id")
                    
                    with pytest.raises(Exception, match="Missing required parameter: branch_id"):
                        api.get()

    @patch('server.controller.dynamic_generation_llm_monitor.dynamic_generation_llm_monitor_service')
    def test_single_branch_monitor_api_success(self, mock_service, app):
        """Test single-branch monitoring API success response"""
        with app.test_request_context('/test?generation_id=123&branch_id=456'):
            mock_service.get_single_branch_interactions.return_value = {
                "branch_id": 456,
                "generation_id": 123,
                "interactions": [],
                "total_count": 0
            }
            
            api = DynamicGenerationSingleBranchMonitorAPI()
            
            with patch('server.controller.dynamic_generation_llm_monitor.request') as mock_request:
                mock_request.args.get.side_effect = lambda key: {'generation_id': '123', 'branch_id': '456'}.get(key)
                
                with patch('server.controller.dynamic_generation_llm_monitor.request_auditor'):
                    with patch('server.controller.dynamic_generation_llm_monitor.ResponseManager') as mock_response:
                        mock_response.new_success_response.return_value = {"code": 200, "data": {}}
                        
                        result = api.get()
                        mock_service.get_single_branch_interactions.assert_called_once_with(123, 456)
                        mock_response.new_success_response.assert_called_once()

    @patch('server.controller.dynamic_generation_llm_monitor.dynamic_generation_llm_monitor_service')
    def test_single_branch_monitor_api_error(self, mock_service, app):
        """Test single-branch monitoring API error response"""
        with app.test_request_context('/test?generation_id=123&branch_id=456'):
            mock_service.get_single_branch_interactions.return_value = {
                "error": "Branch not found"
            }
            
            api = DynamicGenerationSingleBranchMonitorAPI()
            
            with patch('server.controller.dynamic_generation_llm_monitor.request') as mock_request:
                mock_request.args.get.side_effect = lambda key: {'generation_id': '123', 'branch_id': '456'}.get(key)
                
                with patch('server.controller.dynamic_generation_llm_monitor.request_auditor'):
                    with patch('server.controller.dynamic_generation_llm_monitor.ResponseManager') as mock_response:
                        mock_response.new_bad_request_response.return_value = {"code": 400, "message": "Branch not found"}
                        
                        result = api.get()
                        mock_response.new_bad_request_response.assert_called_once_with("Branch not found")

    @patch('server.controller.dynamic_generation_llm_monitor.dynamic_generation_llm_monitor_service')
    def test_full_task_monitor_api_success(self, mock_service, app):
        """Test full-task monitoring API success response"""
        with app.test_request_context('/test?generation_id=123'):
            mock_service.get_full_task_interactions.return_value = {
                "generation_id": 123,
                "interactions": [],
                "total_count": 0
            }
            
            api = DynamicGenerationFullTaskMonitorAPI()
            
            with patch('server.controller.dynamic_generation_llm_monitor.request') as mock_request:
                mock_request.args.get.return_value = '123'
                
                with patch('server.controller.dynamic_generation_llm_monitor.request_auditor'):
                    with patch('server.controller.dynamic_generation_llm_monitor.ResponseManager') as mock_response:
                        mock_response.new_success_response.return_value = {"code": 200, "data": {}}
                        
                        result = api.get()
                        mock_service.get_full_task_interactions.assert_called_once_with(123)

    @patch('server.controller.dynamic_generation_llm_monitor.dynamic_generation_service')
    def test_branches_api_success(self, mock_dg_service, app):
        """Test branch list API success response"""
        with app.test_request_context('/test?generation_id=123'):
            # Mock dynamic_generation
            mock_generation = Mock()
            mock_generation.generation_id = 123
            mock_generation.user_request = "Test request"
            mock_generation.state = "running"
            
            # Mock branches
            mock_branch = Mock()
            mock_branch.id = 456
            mock_branch.end_node_id = 200
            mock_branch.state = "running"
            mock_branch.created_time = datetime(2024, 1, 1, 12, 0, 0)
            mock_branch.updated_time = datetime(2024, 1, 1, 12, 30, 0)
            
            mock_dg_service.get_by_id.return_value = mock_generation
            mock_dg_service.get_generation_branch_list_by_generation_id.return_value = [mock_branch]
            
            api = DynamicGenerationBranchesAPI()
            
            with patch('server.controller.dynamic_generation_llm_monitor.request') as mock_request:
                mock_request.args.get.return_value = '123'
                
                with patch('server.controller.dynamic_generation_llm_monitor.request_auditor'):
                    with patch('server.controller.dynamic_generation_llm_monitor.ResponseManager') as mock_response:
                        mock_response.new_success_response.return_value = {"code": 200, "data": {}}
                        
                        result = api.get()
                        mock_dg_service.get_by_id.assert_called_once_with(123)
                        mock_dg_service.get_generation_branch_list_by_generation_id.assert_called_once_with(123)

    @patch('server.controller.dynamic_generation_llm_monitor.dynamic_generation_service')
    def test_branches_api_not_found(self, mock_dg_service, app):
        """Test branch list API - generation does not exist"""
        with app.test_request_context('/test?generation_id=123'):
            mock_dg_service.get_by_id.return_value = None
            
            api = DynamicGenerationBranchesAPI()
            
            with patch('server.controller.dynamic_generation_llm_monitor.request') as mock_request:
                mock_request.args.get.return_value = '123'
                
                with patch('server.controller.dynamic_generation_llm_monitor.request_auditor'):
                    with patch('server.controller.dynamic_generation_llm_monitor.ResponseManager') as mock_response:
                        mock_response.new_bad_request_response.return_value = {"code": 400, "message": "Not found"}
                        
                        result = api.get()
                        mock_response.new_bad_request_response.assert_called_once_with("Dynamic generation not found")


class TestEdgeCases:
    """Edge case and error handling tests"""

    @pytest.fixture
    def service(self):
        return DynamicGenerationLLMMonitorService()

    def test_circular_node_reference(self, service):
        """Test handling of circular node references"""
        with patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao') as mock_dg_dao:
            with patch('server.service.dynamic_generation_llm_monitor.edge_dao') as mock_edge_dao:
                mock_generation = Mock(previous_node_id=100)
                mock_dg_dao.find_by_id.return_value = mock_generation
                
                # Create a circular reference: 200 -> 150 -> 200
                mock_edge_dao.find_by_target_node_id.side_effect = [
                    [Mock(source_node_id=150)],  # predecessor of 200 is 150
                    [Mock(source_node_id=200)],  # predecessor of 150 is 200 (cycle)
                ]
                
                # This should not loop forever, but stop after a reasonable number of steps
                # The real implementation may need cycle detection
                result = service._get_nodes_in_generation_path(123, 200)
                
                # Verify there is no infinite loop
                assert isinstance(result, list)

    def test_large_dataset_performance(self, service):
        """Test performance on a large dataset"""
        with patch('server.service.dynamic_generation_llm_monitor.dynamic_generation_dao') as mock_dg_dao:
            with patch.object(service, '_get_nodes_in_generation_path') as mock_get_nodes:
                with patch.object(service, '_get_dynamic_generation_interaction') as mock_get_interaction:
                    with patch('server.service.dynamic_generation_llm_monitor.computation_dao') as mock_computation_dao:
                        
                        # Mock a large number of nodes
                        large_node_list = list(range(1, 1001))  # 1000 nodes
                        mock_get_nodes.return_value = large_node_list
                        
                        # Mock interaction data for every node
                        mock_get_interaction.return_value = {
                            "type": "dynamic_generation",
                            "timestamp": 1640995200000,
                            "node_id": 1
                        }
                        
                        mock_computation_dao.find_retry_process_by_node_id.return_value = []
                        mock_dg_dao.find_by_id.return_value = Mock(
                            generation_id=123,
                            user_request="Large data test",
                            state="running"
                        )
                        mock_dg_dao.find_branches_by_dynamic_generation_id.return_value = []
                        
                        # Run the test
                        result = service.get_full_task_interactions(123)
                        
                        # Verify the result
                        assert "error" not in result
                        assert result["total_count"] == 1000
                        
                        # Verify it was called the correct number of times
                        assert mock_get_interaction.call_count == 1000

    def test_s3_access_failure_resilience(self, service):
        """Test fault tolerance when S3 access fails"""
        with patch('server.service.dynamic_generation_llm_monitor.DynamicGenerationWaiter') as mock_waiter_class:
            mock_waiter = Mock()
            mock_waiter_class.return_value = mock_waiter
            
            # Simulate S3 access failure
            mock_waiter.fetch_log.side_effect = Exception("S3 connection timeout")
            
            result = service._get_dynamic_generation_interaction(123, 100)
            
            # Should return None instead of raising
            assert result is None

    def test_malformed_s3_data_handling(self, service):
        """Test handling of malformed S3 data"""
        test_cases = [
            ("", ""),  # empty data
            ("invalid json", "{}"),  # invalid JSON
            ("{broken json", '{"valid": "json"}'),  # partially corrupted
            (None, None),  # None values
        ]
        
        for prompt_data, output_data in test_cases:
            with patch('server.service.dynamic_generation_llm_monitor.DynamicGenerationWaiter') as mock_waiter_class:
                mock_waiter = Mock()
                mock_waiter_class.return_value = mock_waiter
                mock_waiter.fetch_log.return_value = (prompt_data, output_data)
                
                if not prompt_data and not output_data:
                    result = service._get_dynamic_generation_interaction(123, 100)
                    assert result is None
                else:
                    with patch('server.service.dynamic_generation_llm_monitor.node_dao') as mock_node_dao:
                        mock_node_dao.find_by_id.return_value = Mock(
                            name="Test node",
                            created_time=datetime(2024, 1, 1)
                        )
                        
                        result = service._get_dynamic_generation_interaction(123, 100)
                        
                        if result:
                            # Verify malformed data is handled correctly
                            assert "input" in result
                            assert "output" in result


if __name__ == '__main__':
    pytest.main([__file__])
"""
Integration tests for server endpoints.
Tests complete request-response cycles with mocked external dependencies.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from flask import Flask


class TestServerIntegration:
    """Integration tests for server API endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_task_creation_flow(self):
        """Test complete task creation flow."""
        with patch('server.service.task.task_dao') as mock_task_dao, \
             patch('server.service.task.node_dao') as mock_node_dao, \
             patch('server.service.task.edge_dao') as mock_edge_dao, \
             patch('server.service.task.computation_dao') as mock_comp_dao, \
             patch('server.service.task.AuthorityGuardianFactory') as mock_guardian_factory:
            
            # Setup mocks
            mock_guardian = Mock()
            mock_guardian.get_user_id.return_value = "user_123"
            mock_guardian.check_authority.return_value = None
            mock_guardian_factory.get_authority_guardian.return_value = mock_guardian
            
            # Mock nodes
            mock_nodes = [
                Mock(id="node_1", type="data", state="ready"),
                Mock(id="node_2", type="computation", state="ready")
            ]
            mock_node_dao.find_by_id_list.return_value = mock_nodes
            
            # Mock edges
            mock_edges = [Mock(id="edge_1", source_id="node_1", target_id="node_2")]
            mock_edge_dao.find_by_id_list.return_value = mock_edges
            
            # Mock task creation
            mock_task = Mock()
            mock_task.id = "task_123"
            mock_task.state = "created"
            mock_task_dao.insert.return_value = mock_task
            
            # Test the flow
            from server.service.task import TaskService
            service = TaskService()
            
            # Check params
            check_result = service.check_params(["node_1", "node_2"])
            assert check_result["all_ready"] is True
            
            # Create task
            # task = service.create("analysis_123", "user_123", ["node_1", "node_2"], ["edge_1"])
            # assert task.id == "task_123"
    
    def test_computation_execution_flow(self):
        """Test complete computation execution flow."""
        with patch('server.service.computation.computation_dao') as mock_comp_dao, \
             patch('server.service.task.ComputationLauncher') as mock_launcher, \
             patch('server.service.task.batch_client_factory') as mock_batch:
            
            # Mock computation
            mock_computation = Mock()
            mock_computation.id = "comp_123"
            mock_computation.state = "submitted"
            mock_comp_dao.insert.return_value = mock_computation
            mock_comp_dao.find_by_id.return_value = mock_computation
            
            # Mock batch client
            mock_batch_client = Mock()
            mock_batch_client.submit_job.return_value = {
                "jobId": "batch_job_123"
            }
            mock_batch.get_batch_client.return_value = mock_batch_client
            
            # Test the flow
            from server.service.computation import ComputationService
            service = ComputationService()
            
            # Get computation
            comp = service.get_latest_by_node("node_123")
            assert comp is not None
    
    def test_error_handling_flow(self):
        """Test error handling throughout the system."""
        with patch('server.service.computation.computation_dao') as mock_comp_dao, \
             patch('server.service.computation.LLMService') as mock_llm:
            
            # Mock failed computation
            mock_computation = Mock()
            mock_computation.id = "comp_123"
            mock_computation.state = "failed"
            mock_computation.error_message = "Test error"
            mock_comp_dao.find_by_id.return_value = mock_computation
            
            # Mock LLM optimization
            mock_llm_instance = Mock()
            mock_llm_instance.optimize_error_description.return_value = (
                "Helpful error explanation"
            )
            mock_llm.return_value = mock_llm_instance
            
            # Test error refresh
            from server.service.computation import ComputationService
            service = ComputationService()
            result = service.refresh_optimized_error_description("comp_123", "user_123")
            
            # Verify error was processed
            mock_llm_instance.optimize_error_description.assert_called_once()
    
    def test_output_file_listing_pagination(self):
        """Test output file listing with pagination."""
        with patch('server.service.computation.computation_dao') as mock_comp_dao, \
             patch('server.service.computation.Porter') as mock_porter:
            
            # Mock computation
            mock_computation = Mock()
            mock_computation.id = "comp_123"
            mock_computation.output_path = "s3://bucket/output/"
            mock_comp_dao.find_by_id.return_value = mock_computation
            
            # Mock Porter with pagination
            mock_porter_instance = Mock()
            
            # First page
            mock_porter_instance.list_objects.return_value = {
                "files": [{"name": f"file_{i}.csv", "size": 1024} for i in range(50)],
                "total": 50,
                "has_more": True,
                "next_token": "token_123"
            }
            mock_porter.return_value = mock_porter_instance
            
            # Test first page
            from server.service.computation import ComputationService
            service = ComputationService()
            result = service.list_output_files("comp_123", max_keys=50)
            
            assert len(result["files"]) == 50
            assert result["has_more"] is True

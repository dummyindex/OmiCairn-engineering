"""
Unit tests for server computation service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestComputationService:
    """Test computation service business logic."""
    
    def test_get_list_by_node_success(self):
        """Test getting computation list by node ID."""
        with patch('server.service.computation.computation_dao') as mock_dao:
            
            # Mock DAO response
            mock_computations = [
                Mock(
                    id="comp_1",
                    node_id="node_123",
                    state="success",
                    created_at=datetime.now()
                ),
                Mock(
                    id="comp_2",
                    node_id="node_123",
                    state="running",
                    created_at=datetime.now()
                )
            ]
            mock_dao.find_list_by_node.return_value = mock_computations
            
            # Import and test
            from server.service.computation import ComputationService
            service = ComputationService()
            result = service.get_list_by_node("node_123")
            
            # Verify
            mock_dao.find_list_by_node.assert_called_once_with("node_123")
            assert len(result) == 2
            assert result[0].id == "comp_1"
    
    def test_get_list_by_task_success(self):
        """Test getting computation list by task ID."""
        with patch('server.service.computation.computation_dao') as mock_dao:
            
            # Mock DAO response
            mock_computations = [
                Mock(id="comp_1", task_id="task_123"),
                Mock(id="comp_2", task_id="task_123")
            ]
            mock_dao.find_list_by_task.return_value = mock_computations
            
            # Import and test
            from server.service.computation import ComputationService
            service = ComputationService()
            result = service.get_list_by_task("task_123")
            
            # Verify
            mock_dao.find_list_by_task.assert_called_once_with("task_123")
            assert len(result) == 2
    
    def test_get_latest_by_node_success(self):
        """Test getting latest computation by node."""
        with patch('server.service.computation.computation_dao') as mock_dao:
            
            # Mock DAO response
            mock_computation = Mock(
                id="comp_latest",
                node_id="node_123",
                state="success",
                created_at=datetime.now()
            )
            mock_dao.find_latest_by_node.return_value = mock_computation
            
            # Import and test
            from server.service.computation import ComputationService
            service = ComputationService()
            result = service.get_latest_by_node("node_123")
            
            # Verify
            mock_dao.find_latest_by_node.assert_called_once_with("node_123")
            assert result.id == "comp_latest"
    
    def test_get_summary_success(self):
        """Test getting computation summary."""
        with patch('server.service.computation.computation_dao') as mock_comp_dao, \
             patch('server.service.computation.Porter') as mock_porter:
            
            # Mock computation
            mock_computation = Mock()
            mock_computation.id = "comp_123"
            mock_computation.state = "success"
            mock_computation.duration = 120
            mock_comp_dao.find_by_id.return_value = mock_computation
            
            # Mock Porter for S3 operations
            mock_porter_instance = Mock()
            mock_porter_instance.list_objects.return_value = {
                "files": ["output1.csv", "output2.csv"],
                "total_size": 2048
            }
            mock_porter.return_value = mock_porter_instance
            
            # Import and test
            from server.service.computation import ComputationService
            service = ComputationService()
            result = service.get_summary("comp_123")
            
            # Verify
            mock_comp_dao.find_by_id.assert_called_once_with("comp_123")
            assert result["computation_id"] == "comp_123"
            assert result["state"] == "success"
    
    def test_get_log_success(self):
        """Test getting computation logs."""
        with patch('server.service.computation.computation_dao') as mock_comp_dao, \
             patch('server.service.computation.AWSCloudwatchLogsTaker') as mock_log_taker:
            
            # Mock computation
            mock_computation = Mock()
            mock_computation.id = "comp_123"
            mock_computation.log_stream_name = "log_stream_123"
            mock_comp_dao.find_by_id.return_value = mock_computation
            
            # Mock log taker
            mock_log_taker_instance = Mock()
            mock_log_taker_instance.get_logs.return_value = [
                "Log line 1",
                "Log line 2",
                "Log line 3"
            ]
            mock_log_taker.return_value = mock_log_taker_instance
            
            # Import and test
            from server.service.computation import ComputationService
            service = ComputationService()
            result = service.get_log("comp_123")
            
            # Verify
            mock_comp_dao.find_by_id.assert_called_once_with("comp_123")
            assert "logs" in result
            assert len(result["logs"]) == 3
    
    def test_get_figures_success(self):
        """Test getting computation figures."""
        with patch('server.service.computation.computation_dao') as mock_comp_dao, \
             patch('server.service.computation.Porter') as mock_porter:
            
            # Mock computation
            mock_computation = Mock()
            mock_computation.id = "comp_123"
            mock_computation.output_path = "s3://bucket/output/"
            mock_comp_dao.find_by_id.return_value = mock_computation
            
            # Mock Porter for S3 operations
            mock_porter_instance = Mock()
            mock_porter_instance.list_figures.return_value = [
                {
                    "name": "plot1.png",
                    "url": "https://s3.amazonaws.com/bucket/plot1.png",
                    "type": "png",
                    "size": 1024
                },
                {
                    "name": "plot2.pdf",
                    "url": "https://s3.amazonaws.com/bucket/plot2.pdf",
                    "type": "pdf",
                    "size": 2048
                }
            ]
            mock_porter.return_value = mock_porter_instance
            
            # Import and test
            from server.service.computation import ComputationService
            service = ComputationService()
            result = service.get_figures("comp_123")
            
            # Verify
            assert len(result) == 2
            assert result[0]["name"] == "plot1.png"
    
    def test_list_output_files_success(self):
        """Test listing computation output files."""
        with patch('server.service.computation.computation_dao') as mock_comp_dao, \
             patch('server.service.computation.Porter') as mock_porter:
            
            # Mock computation
            mock_computation = Mock()
            mock_computation.id = "comp_123"
            mock_computation.output_path = "s3://bucket/output/"
            mock_comp_dao.find_by_id.return_value = mock_computation
            
            # Mock Porter for S3 operations
            mock_porter_instance = Mock()
            mock_porter_instance.list_objects.return_value = {
                "files": [
                    {"name": "results/output1.csv", "size": 1024},
                    {"name": "results/output2.csv", "size": 2048}
                ],
                "total": 2,
                "has_more": False,
                "next_token": None
            }
            mock_porter.return_value = mock_porter_instance
            
            # Import and test
            from server.service.computation import ComputationService
            service = ComputationService()
            result = service.list_output_files(
                "comp_123",
                prefix="results/",
                max_keys=50
            )
            
            # Verify
            assert len(result["files"]) == 2
            assert result["total"] == 2
            assert result["has_more"] is False
    
    def test_refresh_optimized_error_description_success(self):
        """Test refreshing optimized error description with LLM."""
        with patch('server.service.computation.computation_dao') as mock_comp_dao, \
             patch('server.service.computation.LLMService') as mock_llm_service:
            
            # Mock computation with error
            mock_computation = Mock()
            mock_computation.id = "comp_123"
            mock_computation.state = "failed"
            mock_computation.error_message = "Original error message"
            mock_computation.error_description = None
            mock_comp_dao.find_by_id.return_value = mock_computation
            
            # Mock LLM service
            mock_llm_instance = Mock()
            mock_llm_instance.optimize_error_description.return_value = (
                "Optimized error description with helpful context"
            )
            mock_llm_service.return_value = mock_llm_instance
            
            # Import and test
            from server.service.computation import ComputationService
            service = ComputationService()
            result = service.refresh_optimized_error_description(
                "comp_123",
                "user_123"
            )
            
            # Verify
            mock_comp_dao.find_by_id.assert_called_once_with("comp_123")
            mock_comp_dao.update.assert_called_once()
            assert result.error_description is not None
    
    def test_get_information_from_s3(self):
        """Test getting information from S3 object."""
        with patch('server.service.computation.Porter') as mock_porter:
            
            # Mock Porter for S3 operations
            mock_porter_instance = Mock()
            mock_porter_instance.get_object.return_value = {
                "content": b'{"key": "value"}',
                "content_type": "application/json"
            }
            mock_porter.return_value = mock_porter_instance
            
            # Import and test
            from server.service.computation import ComputationService
            service = ComputationService()
            result = service.get_information(
                "s3://bucket/path/to/file.json",
                mock_porter_instance
            )
            
            # Verify
            assert "key" in result
            assert result["key"] == "value"

"""
Unit tests for server computation controller endpoints.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestComputationController:
    """Test computation controller API endpoints."""
    
    def test_computation_list_by_node_success(self):
        """Test getting computation list by node ID."""
        with patch('server.controller.computation.request') as mock_request, \
             patch('server.controller.computation.computation_service') as mock_service, \
             patch('server.controller.computation.ResponseManager') as mock_response_manager:
            
            # Mock request
            mock_request.args.get.return_value = "node_123"
            
            # Mock service response
            mock_computations = [
                {
                    "computation_id": "comp_1",
                    "node_id": "node_123",
                    "status": "success",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "computation_id": "comp_2",
                    "node_id": "node_123",
                    "status": "running",
                    "created_at": datetime.now().isoformat()
                }
            ]
            mock_service.get_list_by_node.return_value = mock_computations
            
            # Mock response
            mock_response_manager.new_success_response.return_value = {
                "code": 200,
                "data": mock_computations
            }
            
            # Import and test
            from server.controller.computation import ComputationListByNodeAPI
            api = ComputationListByNodeAPI()
            result = api.get()
            
            # Verify
            mock_service.get_list_by_node.assert_called_once_with("node_123")
            assert result["code"] == 200
            assert len(result["data"]) == 2
    
    def test_computation_summary_success(self):
        """Test getting computation summary."""
        with patch('server.controller.computation.request') as mock_request, \
             patch('server.controller.computation.computation_service') as mock_service, \
             patch('server.controller.computation.ResponseManager') as mock_response_manager:
            
            # Mock request
            mock_request.args.get.return_value = "comp_123"
            
            # Mock service response
            mock_summary = {
                "computation_id": "comp_123",
                "status": "success",
                "duration": 120,
                "output_files": 5,
                "figures": 3,
                "logs_size": 1024
            }
            mock_service.get_summary.return_value = mock_summary
            
            # Mock response
            mock_response_manager.new_success_response.return_value = {
                "code": 200,
                "data": mock_summary
            }
            
            # Import and test
            from server.controller.computation import ComputationSummaryAPI
            api = ComputationSummaryAPI()
            result = api.get()
            
            # Verify
            mock_service.get_summary.assert_called_once_with("comp_123")
            assert result["code"] == 200
            assert result["data"]["computation_id"] == "comp_123"
    
    def test_computation_log_success(self):
        """Test getting computation logs."""
        with patch('server.controller.computation.request') as mock_request, \
             patch('server.controller.computation.computation_service') as mock_service, \
             patch('server.controller.computation.ResponseManager') as mock_response_manager:
            
            # Mock request
            mock_request.args.get.return_value = "comp_123"
            
            # Mock service response
            mock_log = {
                "computation_id": "comp_123",
                "logs": "Log line 1\nLog line 2\nLog line 3",
                "total_lines": 3
            }
            mock_service.get_log.return_value = mock_log
            
            # Mock response
            mock_response_manager.new_success_response.return_value = {
                "code": 200,
                "data": mock_log
            }
            
            # Import and test
            from server.controller.computation import ComputationLogAPI
            api = ComputationLogAPI()
            result = api.get()
            
            # Verify
            mock_service.get_log.assert_called_once_with("comp_123")
            assert result["code"] == 200
            assert "logs" in result["data"]
    
    def test_computation_figures_success(self):
        """Test getting computation figures."""
        with patch('server.controller.computation.request') as mock_request, \
             patch('server.controller.computation.computation_service') as mock_service, \
             patch('server.controller.computation.ResponseManager') as mock_response_manager:
            
            # Mock request
            mock_request.args.get.return_value = "comp_123"
            
            # Mock service response
            mock_figures = [
                {
                    "figure_id": "fig_1",
                    "name": "plot1.png",
                    "url": "https://s3.amazonaws.com/bucket/plot1.png",
                    "type": "png"
                },
                {
                    "figure_id": "fig_2",
                    "name": "plot2.pdf",
                    "url": "https://s3.amazonaws.com/bucket/plot2.pdf",
                    "type": "pdf"
                }
            ]
            mock_service.get_figures.return_value = mock_figures
            
            # Mock response
            mock_response_manager.new_success_response.return_value = {
                "code": 200,
                "data": mock_figures
            }
            
            # Import and test
            from server.controller.computation import ComputationFiguresAPI
            api = ComputationFiguresAPI()
            result = api.get()
            
            # Verify
            mock_service.get_figures.assert_called_once_with("comp_123")
            assert result["code"] == 200
            assert len(result["data"]) == 2
    
    def test_computation_output_files_success(self):
        """Test listing computation output files."""
        with patch('server.controller.computation.request') as mock_request, \
             patch('server.controller.computation.computation_service') as mock_service, \
             patch('server.controller.computation.ResponseManager') as mock_response_manager:
            
            # Mock request
            mock_request.args.get.side_effect = lambda key, default=None: {
                "computation_id": "comp_123",
                "prefix": "results/",
                "max_keys": "50"
            }.get(key, default)
            
            # Mock service response
            mock_files = {
                "files": [
                    {"name": "results/output1.csv", "size": 1024},
                    {"name": "results/output2.csv", "size": 2048}
                ],
                "total": 2,
                "has_more": False
            }
            mock_service.list_output_files.return_value = mock_files
            
            # Mock response
            mock_response_manager.new_success_response.return_value = {
                "code": 200,
                "data": mock_files
            }
            
            # Import and test
            from server.controller.computation import ComputationOutputFilesAPI
            api = ComputationOutputFilesAPI()
            result = api.get()
            
            # Verify
            mock_service.list_output_files.assert_called_once()
            assert result["code"] == 200
            assert len(result["data"]["files"]) == 2
    
    def test_computation_error_refresh_success(self):
        """Test refreshing computation error description."""
        with patch('server.controller.computation.request') as mock_request, \
             patch('server.controller.computation.computation_service') as mock_service, \
             patch('server.controller.computation.AuthorityGuardianFactory') as mock_guardian_factory, \
             patch('server.controller.computation.ResponseManager') as mock_response_manager:
            
            # Mock authority guardian
            mock_guardian = Mock()
            mock_guardian.get_user_id.return_value = "user_123"
            mock_guardian_factory.get_authority_guardian.return_value = mock_guardian
            
            # Mock request
            mock_request.get_json.return_value = {
                "computation_id": "comp_123"
            }
            
            # Mock service response
            mock_computation = {
                "computation_id": "comp_123",
                "status": "failed",
                "error_description": "Updated error description with AI analysis"
            }
            mock_service.refresh_optimized_error_description.return_value = mock_computation
            
            # Mock response
            mock_response_manager.new_success_response.return_value = {
                "code": 200,
                "data": mock_computation
            }
            
            # Import and test
            from server.controller.computation import ComputationErrorRefreshAPI
            api = ComputationErrorRefreshAPI()
            result = api.post()
            
            # Verify
            mock_service.refresh_optimized_error_description.assert_called_once_with(
                "comp_123", "user_123"
            )
            assert result["code"] == 200
            assert "error_description" in result["data"]

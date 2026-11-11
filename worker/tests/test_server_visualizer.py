"""
Unit tests for server visualizer functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestVisualizerController:
    """Test visualizer controller APIs."""
    
    def test_figure_list_api_success(self):
        """Test getting figure list."""
        with patch('server.controller.visualizer.request') as mock_request, \
             patch('server.controller.visualizer.visualizer_service') as mock_service, \
             patch('server.controller.visualizer.ResponseManager') as mock_response:
            
            # Mock request
            mock_request.args.get.return_value = "comp_123"
            
            # Mock service response
            mock_figures = [
                {
                    "figure_id": "fig_1",
                    "name": "plot1.png",
                    "url": "https://s3.amazonaws.com/bucket/plot1.png"
                },
                {
                    "figure_id": "fig_2",
                    "name": "plot2.pdf",
                    "url": "https://s3.amazonaws.com/bucket/plot2.pdf"
                }
            ]
            mock_service.get_figure_list.return_value = mock_figures
            
            # Mock response
            mock_response.new_success_response.return_value = {
                "code": 200,
                "data": mock_figures
            }
            
            # Import and test
            from server.controller.visualizer import FigureListAPI
            api = FigureListAPI()
            result = api.get()
            
            # Verify
            assert result["code"] == 200
            assert len(result["data"]) == 2
    
    def test_figure_detail_api_success(self):
        """Test getting figure details."""
        with patch('server.controller.visualizer.request') as mock_request, \
             patch('server.controller.visualizer.visualizer_service') as mock_service, \
             patch('server.controller.visualizer.ResponseManager') as mock_response:
            
            # Mock request
            mock_request.args.get.return_value = "fig_123"
            
            # Mock service response
            mock_figure = {
                "figure_id": "fig_123",
                "name": "scatter_plot.png",
                "url": "https://s3.amazonaws.com/bucket/scatter_plot.png",
                "type": "png",
                "size": 1024,
                "metadata": {
                    "width": 800,
                    "height": 600
                }
            }
            mock_service.get_figure_detail.return_value = mock_figure
            
            # Mock response
            mock_response.new_success_response.return_value = {
                "code": 200,
                "data": mock_figure
            }
            
            # Import and test
            from server.controller.visualizer import FigureDetailAPI
            api = FigureDetailAPI()
            result = api.get()
            
            # Verify
            assert result["code"] == 200
            assert result["data"]["figure_id"] == "fig_123"
    
    def test_figure_upload_api_success(self):
        """Test uploading figure."""
        with patch('server.controller.visualizer.request') as mock_request, \
             patch('server.controller.visualizer.visualizer_service') as mock_service, \
             patch('server.controller.visualizer.ResponseManager') as mock_response:
            
            # Mock request with file
            mock_file = Mock()
            mock_file.filename = "new_plot.png"
            mock_file.read.return_value = b"fake image data"
            mock_request.files.get.return_value = mock_file
            mock_request.form.get.return_value = "comp_123"
            
            # Mock service response
            mock_uploaded_figure = {
                "figure_id": "fig_new",
                "name": "new_plot.png",
                "url": "https://s3.amazonaws.com/bucket/new_plot.png"
            }
            mock_service.upload_figure.return_value = mock_uploaded_figure
            
            # Mock response
            mock_response.new_success_response.return_value = {
                "code": 200,
                "data": mock_uploaded_figure
            }
            
            # Import and test
            from server.controller.visualizer import FigureUploadAPI
            api = FigureUploadAPI()
            result = api.post()
            
            # Verify
            assert result["code"] == 200


class TestVisualizerService:
    """Test visualizer service logic."""
    
    def test_get_figure_list_success(self):
        """Test getting figure list from computation."""
        with patch('server.service.visualizer.computation_dao') as mock_comp_dao, \
             patch('server.service.visualizer.figure_dao') as mock_figure_dao:
            
            # Mock computation
            mock_computation = Mock()
            mock_computation.id = "comp_123"
            mock_comp_dao.find_by_id.return_value = mock_computation
            
            # Mock figures
            mock_figures = [
                Mock(
                    id="fig_1",
                    name="plot1.png",
                    path="s3://bucket/plot1.png",
                    computation_id="comp_123"
                ),
                Mock(
                    id="fig_2",
                    name="plot2.pdf",
                    path="s3://bucket/plot2.pdf",
                    computation_id="comp_123"
                )
            ]
            mock_figure_dao.find_by_computation.return_value = mock_figures
            
            # Import and test
            from server.service.visualizer import VisualizerService
            service = VisualizerService()
            result = service.get_figure_list("comp_123")
            
            # Verify
            assert len(result) == 2
            assert result[0].id == "fig_1"
    
    def test_get_figure_detail_with_metadata(self):
        """Test getting figure detail with metadata extraction."""
        with patch('server.service.visualizer.figure_dao') as mock_figure_dao, \
             patch('server.service.visualizer.Porter') as mock_porter:
            
            # Mock figure
            mock_figure = Mock()
            mock_figure.id = "fig_123"
            mock_figure.name = "plot.png"
            mock_figure.path = "s3://bucket/plot.png"
            mock_figure_dao.find_by_id.return_value = mock_figure
            
            # Mock Porter
            mock_porter_instance = Mock()
            mock_porter_instance.get_metadata.return_value = {
                "content_type": "image/png",
                "size": 2048,
                "last_modified": datetime.now().isoformat()
            }
            mock_porter.return_value = mock_porter_instance
            
            # Import and test
            from server.service.visualizer import VisualizerService
            service = VisualizerService()
            result = service.get_figure_detail("fig_123")
            
            # Verify
            assert result["id"] == "fig_123"
            assert "metadata" in result
    
    def test_upload_figure_to_s3(self):
        """Test uploading figure to S3."""
        with patch('server.service.visualizer.computation_dao') as mock_comp_dao, \
             patch('server.service.visualizer.figure_dao') as mock_figure_dao, \
             patch('server.service.visualizer.Porter') as mock_porter:
            
            # Mock computation
            mock_computation = Mock()
            mock_computation.id = "comp_123"
            mock_computation.output_path = "s3://bucket/output/"
            mock_comp_dao.find_by_id.return_value = mock_computation
            
            # Mock Porter upload
            mock_porter_instance = Mock()
            mock_porter_instance.upload_file.return_value = {
                "path": "s3://bucket/output/figures/uploaded.png",
                "url": "https://s3.amazonaws.com/bucket/output/figures/uploaded.png"
            }
            mock_porter.return_value = mock_porter_instance
            
            # Mock figure DAO
            mock_figure = Mock()
            mock_figure.id = "fig_new"
            mock_figure_dao.insert.return_value = mock_figure
            
            # Import and test
            from server.service.visualizer import VisualizerService
            service = VisualizerService()
            
            # Upload figure
            mock_file_data = b"fake image data"
            result = service.upload_figure(
                "comp_123",
                "uploaded.png",
                mock_file_data
            )
            
            # Verify
            mock_porter_instance.upload_file.assert_called_once()
            assert result.id == "fig_new"
    
    def test_delete_figure_success(self):
        """Test deleting figure."""
        with patch('server.service.visualizer.figure_dao') as mock_figure_dao, \
             patch('server.service.visualizer.Porter') as mock_porter:
            
            # Mock figure
            mock_figure = Mock()
            mock_figure.id = "fig_123"
            mock_figure.path = "s3://bucket/plot.png"
            mock_figure_dao.find_by_id.return_value = mock_figure
            
            # Mock Porter delete
            mock_porter_instance = Mock()
            mock_porter_instance.delete_file.return_value = {"success": True}
            mock_porter.return_value = mock_porter_instance
            
            # Mock DAO delete
            mock_figure_dao.delete.return_value = None
            
            # Import and test
            from server.service.visualizer import VisualizerService
            service = VisualizerService()
            result = service.delete_figure("fig_123")
            
            # Verify
            mock_porter_instance.delete_file.assert_called_once()
            mock_figure_dao.delete.assert_called_once()

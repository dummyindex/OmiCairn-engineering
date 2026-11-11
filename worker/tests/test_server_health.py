"""
Unit tests for server health check endpoints.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from server.controller.health import AvailabilityCheckAPI


class TestHealthController:
    """Test health check controller."""
    
    def test_availability_check_api_success(self):
        """Test successful health check."""
        with patch('server.controller.health.ResponseManager') as mock_response_manager:
            # Mock successful response
            mock_response_manager.new_success_response.return_value = {
                "code": 200,
                "message": "success",
                "data": {}
            }
            
            # Test the API
            api = AvailabilityCheckAPI()
            result = api.get()
            
            # Verify response
            mock_response_manager.new_success_response.assert_called_once()
            assert result["code"] == 200
            assert result["message"] == "success"
    
    def test_availability_check_api_exception_handling(self):
        """Test health check with exception handling."""
        with patch('server.controller.health.ResponseManager') as mock_response_manager:
            # Mock exception
            mock_response_manager.new_success_response.side_effect = Exception("Service error")
            
            # Test the API - exception should be caught by exception_wrapper
            api = AvailabilityCheckAPI()
            
            with pytest.raises(Exception) as exc_info:
                api.get()
            
            assert "Service error" in str(exc_info.value)

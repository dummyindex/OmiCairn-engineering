"""
Unit tests for daemon/scan_timeout_computations.py core functions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add daemon module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'daemon'))

from scan_timeout_computations import (
    init,
    scan_timeout_computations,
    scan_omissive_computations,
    unlock_nodes_interval,
    check_server_inited,
    scheduled_scan_timeout_computations,
    scheduled_unlock_nodes,
)


class TestInit:
    """Test init function"""

    @patch('scan_timeout_computations.requests.get')
    @patch('scan_timeout_computations.logger')
    def test_init_success(self, mock_logger, mock_get):
        """Test successful initialization"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        init()
        
        mock_get.assert_called_once_with("http://localhost:80/interval/init")
        mock_logger.info.assert_any_call("Initializing")
        mock_logger.info.assert_any_call("Initializing done")

    @patch('scan_timeout_computations.requests.get')
    @patch('scan_timeout_computations.logger')
    def test_init_failure(self, mock_logger, mock_get):
        """Test initialization failure"""
        mock_get.side_effect = Exception("Connection error")
        
        init()
        
        mock_logger.error.assert_called_once()
        assert "Failed to initialize" in str(mock_logger.error.call_args)


class TestScanTimeoutComputations:
    """Test scan_timeout_computations function"""

    @patch('scan_timeout_computations.requests.get')
    @patch('scan_timeout_computations.logger')
    def test_scan_timeout_computations_success(self, mock_logger, mock_get):
        """Test successful scanning of timeout computations"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        scan_timeout_computations()
        
        mock_get.assert_called_once_with("http://localhost:80/interval/scan-timeout")
        mock_logger.info.assert_any_call("Scanning timeout computations")
        mock_logger.info.assert_any_call("Scanning timeout computations done")

    @patch('scan_timeout_computations.requests.get')
    @patch('scan_timeout_computations.logger')
    def test_scan_timeout_computations_failure(self, mock_logger, mock_get):
        """Test scanning failure"""
        mock_get.side_effect = Exception("Network error")
        
        scan_timeout_computations()
        
        mock_logger.error.assert_called_once()
        assert "Failed to scan timeout computations" in str(mock_logger.error.call_args)


class TestScanOmissiveComputations:
    """Test scan_omissive_computations function"""

    @patch('scan_timeout_computations.requests.get')
    @patch('scan_timeout_computations.logger')
    def test_scan_omissive_computations_success(self, mock_logger, mock_get):
        """Test successful scanning of omissive computations"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        scan_omissive_computations()
        
        mock_get.assert_called_once_with("http://localhost:80/interval/scan-omissive")
        mock_logger.info.assert_any_call("Scanning omissive computations")
        mock_logger.info.assert_any_call("Scanning omissive computations done")

    @patch('scan_timeout_computations.requests.get')
    @patch('scan_timeout_computations.logger')
    def test_scan_omissive_computations_failure(self, mock_logger, mock_get):
        """Test scanning failure"""
        mock_get.side_effect = Exception("Timeout error")
        
        scan_omissive_computations()
        
        mock_logger.error.assert_called_once()
        assert "Failed to scan omissive computations" in str(mock_logger.error.call_args)


class TestUnlockNodesInterval:
    """Test unlock_nodes_interval function"""

    @patch('scan_timeout_computations.requests.post')
    @patch('scan_timeout_computations.logger')
    def test_unlock_nodes_interval_success(self, mock_logger, mock_post):
        """Test successful unlocking of nodes"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        unlock_nodes_interval()
        
        mock_post.assert_called_once_with("http://localhost:80/interval/unlock-nodes-interval")
        mock_logger.info.assert_any_call("Unlocking nodes interval")
        mock_logger.info.assert_any_call("Unlocking nodes interval done")

    @patch('scan_timeout_computations.requests.post')
    @patch('scan_timeout_computations.logger')
    def test_unlock_nodes_interval_failure(self, mock_logger, mock_post):
        """Test unlocking failure"""
        mock_post.side_effect = Exception("Service unavailable")
        
        unlock_nodes_interval()
        
        mock_logger.error.assert_called_once()
        assert "Failed to unlock nodes interval" in str(mock_logger.error.call_args)


class TestCheckServerInited:
    """Test check_server_inited function"""

    @patch('scan_timeout_computations.requests.get')
    def test_check_server_inited_success(self, mock_get):
        """Test server is initialized"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = check_server_inited()
        
        assert result is True
        mock_get.assert_called_once_with("http://localhost:80/health/check", timeout=5)

    @patch('scan_timeout_computations.requests.get')
    def test_check_server_inited_wrong_status(self, mock_get):
        """Test server returns wrong status code"""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response
        
        result = check_server_inited()
        
        assert result is False

    @patch('scan_timeout_computations.requests.get')
    def test_check_server_inited_timeout(self, mock_get):
        """Test server check timeout"""
        mock_get.side_effect = Exception("Timeout")
        
        result = check_server_inited()
        
        assert result is False

    @patch('scan_timeout_computations.requests.get')
    def test_check_server_inited_connection_error(self, mock_get):
        """Test server check connection error"""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        result = check_server_inited()
        
        assert result is False


class TestScheduledScanTimeoutComputations:
    """Test scheduled_scan_timeout_computations function"""

    @patch('scan_timeout_computations.scan_timeout_computations')
    @patch('scan_timeout_computations.logger')
    def test_scheduled_scan_timeout_computations_success(self, mock_logger, mock_scan):
        """Test successful scheduled scan"""
        scheduled_scan_timeout_computations()
        
        mock_scan.assert_called_once()
        mock_logger.info.assert_called_once_with(
            "[Scheduled Task] Scanning timeout computations triggered"
        )

    @patch('scan_timeout_computations.scan_timeout_computations')
    @patch('scan_timeout_computations.logger')
    def test_scheduled_scan_timeout_computations_failure(self, mock_logger, mock_scan):
        """Test scheduled scan with exception"""
        mock_scan.side_effect = Exception("Scan error")
        
        scheduled_scan_timeout_computations()
        
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args
        assert "[Scheduled Task] Failed to scan timeout computations" in str(error_call)


class TestScheduledUnlockNodes:
    """Test scheduled_unlock_nodes function"""

    @patch('scan_timeout_computations.unlock_nodes_interval')
    @patch('scan_timeout_computations.logger')
    def test_scheduled_unlock_nodes_success(self, mock_logger, mock_unlock):
        """Test successful scheduled unlock"""
        scheduled_unlock_nodes()
        
        mock_unlock.assert_called_once()
        mock_logger.info.assert_called_once_with(
            "[Scheduled Task] Unlocking nodes triggered"
        )

    @patch('scan_timeout_computations.unlock_nodes_interval')
    @patch('scan_timeout_computations.logger')
    def test_scheduled_unlock_nodes_failure(self, mock_logger, mock_unlock):
        """Test scheduled unlock with exception"""
        mock_unlock.side_effect = Exception("Unlock error")
        
        scheduled_unlock_nodes()
        
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args
        assert "[Scheduled Task] Failed to unlock nodes" in str(error_call)


class TestIntegrationScenarios:
    """Test integration scenarios"""

    @patch('scan_timeout_computations.requests.get')
    @patch('scan_timeout_computations.requests.post')
    def test_full_cycle_success(self, mock_post, mock_get):
        """Test full cycle of init, scan, and unlock"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        
        # Initialize
        init()
        
        # Check server
        assert check_server_inited() is True
        
        # Scan timeout computations
        scan_timeout_computations()
        
        # Scan omissive computations
        scan_omissive_computations()
        
        # Unlock nodes
        unlock_nodes_interval()
        
        # Verify all calls were made
        assert mock_get.call_count == 4  # init, check, scan_timeout, scan_omissive
        assert mock_post.call_count == 1  # unlock

    @patch('scan_timeout_computations.requests.get')
    @patch('scan_timeout_computations.requests.post')
    @patch('scan_timeout_computations.logger')
    def test_partial_failure_resilience(self, mock_logger, mock_post, mock_get):
        """Test that one failure doesn't affect other operations"""
        # Scan timeout fails
        mock_get.side_effect = Exception("Scan error")
        
        scan_timeout_computations()
        mock_logger.error.assert_called()
        mock_logger.reset_mock()
        
        # But unlock should still work
        mock_post.return_value = Mock(status_code=200)
        unlock_nodes_interval()
        
        # Verify unlock succeeded
        mock_post.assert_called_once()

    @patch('scan_timeout_computations.requests.get')
    def test_server_health_check_retry_logic(self, mock_get):
        """Test server health check can handle retries"""
        # First two calls fail, third succeeds
        mock_get.side_effect = [
            Exception("Connection refused"),
            Exception("Connection refused"),
            Mock(status_code=200)
        ]
        
        # First two checks should fail
        assert check_server_inited() is False
        assert check_server_inited() is False
        
        # Third check should succeed
        assert check_server_inited() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

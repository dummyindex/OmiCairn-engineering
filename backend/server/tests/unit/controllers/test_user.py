"""
Unit tests for User Controller
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from controller.user import (
    UserLoginByPasswordAPI,
)
from model.user_token import UserToken


@pytest.mark.unit
@pytest.mark.controller
class TestUserController:
    """Test User Controller API endpoints"""

    # ===== UserLoginByPasswordAPI Tests =====

    @patch('controller.user.user_service')
    def test_login_by_password_success(self, mock_user_service, client):
        """Test password login - success"""
        # Arrange
        mock_token = Mock(spec=UserToken)
        mock_token.user_id = 1
        mock_token.value = "test_token_abc123"
        mock_user_service.login_by_password.return_value = mock_token

        # Act
        response = client.post('/api/user/login_by_password', data={
            'phone_number': '+1234567890',
            'password': 'password123'
        })

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data['data'] == "test_token_abc123"
        mock_user_service.login_by_password.assert_called_once_with('+1234567890', 'password123')

    @patch('controller.user.user_service')
    def test_login_by_password_invalid_credentials(self, mock_user_service, client):
        """Test password login - wrong credentials"""
        # Arrange
        from exception.authority.login_error import LoginErrorException
        mock_user_service.login_by_password.side_effect = LoginErrorException("Invalid credentials")

        # Act
        response = client.post('/api/user/login_by_password', data={
            'phone_number': '+1234567890',
            'password': 'wrong_password'
        })

        # Assert - the exception wrapper should catch the exception
        mock_user_service.login_by_password.assert_called_once()

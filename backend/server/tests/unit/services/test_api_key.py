"""
Unit tests for APIKeyService
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from service.api_key import APIKeyService, api_key_service
from model.api_key import APIKey


@pytest.mark.unit
@pytest.mark.service
class TestAPIKeyService:
    """Test APIKeyService business logic"""

    @pytest.fixture
    def service(self):
        return APIKeyService()

    @patch('service.api_key.api_key_dao')
    def test_create_api_key(self, mock_dao, service):
        """Test creating an API key"""
        # Arrange
        mock_key = Mock(spec=APIKey)
        mock_key.id = 1
        mock_key.key = "test_api_key_123"
        mock_dao.insert.return_value = mock_key

        # Act
        result = service.create_api_key(
            user_id=1,
            key="test_api_key_123",
            name="Test Key"
        )

        # Assert
        assert result is not None
        assert result.key == "test_api_key_123"
        mock_dao.insert.assert_called_once()

    @patch('service.api_key.api_key_dao')
    def test_get_api_keys(self, mock_dao, service):
        """Test getting a user's API keys"""
        # Arrange
        mock_keys = [
            Mock(id=1, key="key1", name="Key 1"),
            Mock(id=2, key="key2", name="Key 2")
        ]
        mock_dao.find_by_user_id.return_value = mock_keys

        # Act
        result = service.get_api_keys(1)

        # Assert
        assert len(result) == 2
        assert result[0].key == "key1"
        assert result[1].key == "key2"
        mock_dao.find_by_user_id.assert_called_once_with(1)

    @patch('service.api_key.api_key_dao')
    def test_delete_api_key(self, mock_dao, service):
        """Test deleting an API key"""
        # Arrange
        mock_dao.delete.return_value = None

        # Act
        service.delete_api_key(1)

        # Assert
        mock_dao.delete.assert_called_once_with(1)

    @patch('service.api_key.api_key_dao')
    def test_update_api_key(self, mock_dao, service):
        """Test updating an API key"""
        # Arrange
        mock_dao.update.return_value = None
        update_data = {'name': 'Updated Key', 'active': False}

        # Act
        service.update_api_key(1, update_data)

        # Assert
        mock_dao.update.assert_called_once_with(1, update_data)

    def test_singleton_instance(self):
        """Test the singleton pattern"""
        assert api_key_service is not None
        assert isinstance(api_key_service, APIKeyService)

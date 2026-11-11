"""
Unit tests for APIKeyDao
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from dao.api_key import APIKeyDao, api_key_dao
from model.api_key import APIKey


@pytest.mark.unit
@pytest.mark.dao
class TestAPIKeyDao:
    """Test APIKeyDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        """Create APIKeyDao instance"""
        return APIKeyDao()

    @pytest.fixture
    def sample_api_key_model(self):
        """Create sample APIKey model instance"""
        return APIKey(
            id=1,
            user_id=1,
            key="test_api_key_123abc",
            name="Test API Key",
            active=True,
            created_time=datetime.now()
        )

    # ===== Insert Tests =====

    @patch('db.alchemy_db.session')
    def test_insert_api_key(self, mock_session, dao, sample_api_key_model):
        """Test inserting an API key"""
        # Arrange
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        # Act
        result = dao.insert(sample_api_key_model)

        # Assert
        assert result is not None
        assert result.key == "test_api_key_123abc"
        mock_session.add.assert_called_once_with(sample_api_key_model)
        mock_session.flush.assert_called_once()

    # ===== Query Tests =====

    @patch('model.api_key.APIKey.query')
    def test_find_by_user_id(self, mock_query, dao, sample_api_key_model):
        """Test finding API keys by user ID"""
        # Arrange
        api_key_list = [sample_api_key_model]
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = api_key_list

        # Act
        result = dao.find_by_user_id(1)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].user_id == 1
        mock_query.filter.assert_called_once()
        mock_filter.all.assert_called_once()

    @patch('model.api_key.APIKey.query')
    def test_find_by_user_id_no_keys(self, mock_query, dao):
        """Test finding API keys by user ID - no records"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = []

        # Act
        result = dao.find_by_user_id(999)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    # ===== Update Tests =====

    @patch('db.alchemy_db.session')
    @patch('model.api_key.APIKey.query')
    def test_update_api_key(self, mock_query, mock_session, dao):
        """Test updating an API key"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = None
        mock_session.flush.return_value = None

        updated_attrs = {
            'name': 'Updated API Key',
            'active': False
        }

        # Act
        dao.update(1, updated_attrs)

        # Assert
        mock_query.filter.assert_called_once()
        mock_filter.update.assert_called_once_with(updated_attrs)
        mock_session.flush.assert_called_once()

    @patch('db.alchemy_db.session')
    @patch('model.api_key.APIKey.query')
    def test_update_api_key_empty_attrs(self, mock_query, mock_session, dao):
        """Test updating an API key - empty attributes"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = None
        mock_session.flush.return_value = None

        # Act
        dao.update(1, {})

        # Assert
        mock_filter.update.assert_called_once_with({})
        mock_session.flush.assert_called_once()

    # ===== Delete Tests =====

    @patch('db.alchemy_db.session')
    @patch('model.api_key.APIKey.query')
    def test_delete_api_key_int_id(self, mock_query, mock_session, dao):
        """Test deleting an API key - int ID"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = None
        mock_session.flush.return_value = None

        # Act
        dao.delete(1)

        # Assert
        mock_query.filter.assert_called_once()
        mock_filter.delete.assert_called_once()
        mock_session.flush.assert_called_once()

    @patch('db.alchemy_db.session')
    @patch('model.api_key.APIKey.query')
    def test_delete_api_key_str_id(self, mock_query, mock_session, dao):
        """Test deleting an API key - string ID"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = None
        mock_session.flush.return_value = None

        # Act
        dao.delete("api_key_123")

        # Assert
        mock_query.filter.assert_called_once()
        mock_filter.delete.assert_called_once()
        mock_session.flush.assert_called_once()

    # ===== Singleton Tests =====

    def test_singleton_instance(self):
        """Test singleton pattern"""
        assert api_key_dao is not None
        assert isinstance(api_key_dao, APIKeyDao)

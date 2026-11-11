"""
Unit tests for UserTokenDao
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from dao.user_token import UserTokenDao, user_token_dao
from model.user_token import UserToken


@pytest.mark.unit
@pytest.mark.dao
class TestUserTokenDao:
    """Test UserTokenDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        """Create UserTokenDao instance"""
        return UserTokenDao()

    @pytest.fixture
    def sample_token_model(self):
        """Create sample UserToken model instance"""
        return UserToken(
            id=1,
            user_id=1,
            value="test_token_abc123",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=7),
            created_time=datetime.now()
        )

    # ===== Insert Tests =====

    @patch('db.alchemy_db.session')
    def test_insert_token(self, mock_session, dao, sample_token_model):
        """Test inserting a token"""
        # Arrange
        sample_token_model.created_time = None
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        # Act
        result = dao.insert(sample_token_model)

        # Assert
        assert result is not None
        assert result.created_time is not None
        mock_session.add.assert_called_once_with(sample_token_model)
        mock_session.flush.assert_called_once()

    @patch('db.alchemy_db.session')
    def test_insert_token_with_existing_timestamp(self, mock_session, dao, sample_token_model):
        """Test inserting a token - creation time already set"""
        # Arrange
        original_time = sample_token_model.created_time
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        # Act
        result = dao.insert(sample_token_model)

        # Assert
        assert result.created_time == original_time
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    # ===== Query Tests =====

    @patch('model.user_token.UserToken.query')
    def test_find_by_value(self, mock_query, dao, sample_token_model):
        """Test finding by token value"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_token_model

        # Act
        result = dao.find_by_value("test_token_abc123")

        # Assert
        assert result is not None
        assert result.value == "test_token_abc123"
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

    @patch('model.user_token.UserToken.query')
    def test_find_by_value_not_found(self, mock_query, dao):
        """Test finding by token value - not found"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        # Act
        result = dao.find_by_value("nonexistent_token")

        # Assert
        assert result is None

    # ===== Delete Tests =====

    @patch('model.user_token.UserToken.query')
    @patch('dao.user_token.datetime')
    def test_delete_the_overdue(self, mock_datetime, mock_query, dao):
        """Test deleting expired tokens"""
        # Arrange
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = now

        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = 3

        # Act
        result = dao.delete_the_overdue(user_id=1)

        # Assert
        assert result == 3
        mock_query.filter.assert_called_once()
        mock_filter.delete.assert_called_once()

    @patch('model.user_token.UserToken.query')
    @patch('dao.user_token.datetime')
    def test_delete_the_overdue_no_tokens(self, mock_datetime, mock_query, dao):
        """Test deleting expired tokens - no expired tokens"""
        # Arrange
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = now

        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = 0

        # Act
        result = dao.delete_the_overdue(user_id=1)

        # Assert
        assert result == 0

    # ===== Singleton Tests =====

    def test_singleton_instance(self):
        """Test the singleton pattern"""
        assert user_token_dao is not None
        assert isinstance(user_token_dao, UserTokenDao)

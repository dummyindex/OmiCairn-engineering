"""
Unit tests for UserDao
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from dao.user import UserDao, user_dao
from model.user import User


@pytest.mark.unit
@pytest.mark.dao
class TestUserDao:
    """Test UserDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        """Create UserDao instance"""
        return UserDao()

    @pytest.fixture
    def sample_user_model(self):
        """Create sample User model instance"""
        return User(
            id=1,
            user_name="testuser",
            phone_number="+1234567890",
            email="test@example.com",
            password="hashed_password",
            created_time=datetime.now(),
            disabled=False
        )

    # ===== Query Tests =====

    @patch('model.user.User.query')
    def test_find_by_id_success(self, mock_query, dao, sample_user_model):
        """Test finding a user by ID - success"""
        # Arrange
        mock_query.get.return_value = sample_user_model

        # Act
        result = dao.find_by_id(1)

        # Assert
        assert result is not None
        assert result.id == 1
        assert result.user_name == "testuser"
        mock_query.get.assert_called_once_with(1)

    @patch('model.user.User.query')
    def test_find_by_id_not_found(self, mock_query, dao):
        """Test finding a user by ID - not found"""
        # Arrange
        mock_query.get.return_value = None

        # Act
        result = dao.find_by_id(999)

        # Assert
        assert result is None
        mock_query.get.assert_called_once_with(999)

    @patch('model.user.User.query')
    def test_find_by_id_none_input(self, mock_query, dao):
        """Test finding a user by ID - None input"""
        # Act
        result = dao.find_by_id(None)

        # Assert
        assert result is None
        mock_query.get.assert_not_called()

    @patch('model.user.User.query')
    def test_find_by_phone_number(self, mock_query, dao, sample_user_model):
        """Test finding a user by phone number"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_user_model

        # Act
        result = dao.find_by_phone_number("+1234567890")

        # Assert
        assert result is not None
        assert result.phone_number == "+1234567890"
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

    @patch('model.user.User.query')
    def test_find_by_id_list(self, mock_query, dao, sample_user_model):
        """Test finding users by a list of IDs"""
        # Arrange
        user_list = [sample_user_model]
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = user_list

        # Act
        result = dao.find_by_id_list([1, 2, 3])

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        mock_query.filter.assert_called_once()
        mock_filter.all.assert_called_once()

    @patch('model.user.User.query')
    def test_search_users(self, mock_query, dao, sample_user_model):
        """Test searching users"""
        # Arrange
        user_list = [sample_user_model]
        mock_filter = MagicMock()
        mock_limit = MagicMock()
        mock_offset = MagicMock()

        mock_query.filter.return_value = mock_filter
        mock_filter.limit.return_value = mock_limit
        mock_limit.offset.return_value = mock_offset
        mock_offset.all.return_value = user_list

        # Act
        result = dao.search("test", offset=0, limit=10)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        mock_query.filter.assert_called_once()
        mock_filter.limit.assert_called_once_with(10)
        mock_limit.offset.assert_called_once_with(0)

    # ===== Insert Tests =====

    @patch('db.alchemy_db.session')
    def test_insert_user(self, mock_session, dao, sample_user_model):
        """Test inserting a user"""
        # Arrange
        sample_user_model.created_time = None
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        # Act
        result = dao.insert(sample_user_model)

        # Assert
        assert result is not None
        assert result.created_time is not None
        mock_session.add.assert_called_once_with(sample_user_model)
        mock_session.flush.assert_called_once()

    @patch('db.alchemy_db.session')
    def test_insert_user_with_existing_timestamp(self, mock_session, dao, sample_user_model):
        """Test inserting a user - creation time already set"""
        # Arrange
        original_time = sample_user_model.created_time
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        # Act
        result = dao.insert(sample_user_model)

        # Assert
        assert result.created_time == original_time
        mock_session.add.assert_called_once()

    # ===== Update Tests =====

    @patch('model.user.User.query')
    def test_update_user(self, mock_query, dao):
        """Test updating a user"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = 1

        attrs = {
            'user_name': 'updated_user',
            'email': 'updated@example.com'
        }

        # Act
        result = dao.update(1, attrs)

        # Assert
        assert result == 1
        mock_query.filter.assert_called_once()
        mock_filter.update.assert_called_once_with(attrs)

    @patch('model.user.User.query')
    def test_update_user_not_found(self, mock_query, dao):
        """Test updating a user - not found"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = 0

        # Act
        result = dao.update(999, {'user_name': 'test'})

        # Assert
        assert result == 0

    # ===== Delete Tests =====

    @patch('model.user.User.query')
    def test_destroy_user(self, mock_query, dao):
        """Test deleting a user"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = 1

        # Act
        result = dao.destroy(1)

        # Assert
        assert result == 1
        mock_query.filter.assert_called_once()
        mock_filter.delete.assert_called_once()

    @patch('model.user.User.query')
    def test_destroy_user_not_found(self, mock_query, dao):
        """Test deleting a user - not found"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = 0

        # Act
        result = dao.destroy(999)

        # Assert
        assert result == 0

    # ===== Singleton Tests =====

    def test_singleton_instance(self):
        """Test the singleton pattern"""
        # user_dao should be a pre-created singleton instance
        assert user_dao is not None
        assert isinstance(user_dao, UserDao)

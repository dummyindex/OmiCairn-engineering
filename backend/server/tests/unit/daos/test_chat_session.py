"""
Unit tests for ChatSessionDao
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from dao.chat_session import ChatSessionDao
from model.chat_session import ChatSession


@pytest.mark.unit
@pytest.mark.dao
class TestChatSessionDao:
    """Test ChatSessionDao CRUD operations"""

    @pytest.fixture
    def sample_session(self):
        return ChatSession(
            id=1,
            user_id=1,
            analysis_id=1,
            title="Test Chat",
            is_active=True,
            created_time=datetime.now(),
            updated_time=datetime.now()
        )

    @patch('db.alchemy_db.session')
    def test_create(self, mock_session, sample_session):
        """Test creating a chat session"""
        # Arrange
        session_data = {
            'user_id': 1,
            'analysis_id': 1,
            'title': 'Test Chat'
        }
        mock_session.add.return_value = None
        mock_session.commit.return_value = None

        with patch('dao.chat_session.ChatSession') as mock_chat_session:
            mock_chat_session.return_value = sample_session

            # Act
            result = ChatSessionDao.create(session_data)

            # Assert
            assert result is not None
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @patch('model.chat_session.ChatSession.query')
    def test_get_by_id(self, mock_query, sample_session):
        """Test finding a session by ID"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter_by.return_value = mock_filter
        mock_filter.first.return_value = sample_session

        # Act
        result = ChatSessionDao.get_by_id(1)

        # Assert
        assert result is not None
        assert result.id == 1
        mock_query.filter_by.assert_called_once_with(id=1, is_active=True)

    @patch('model.chat_session.ChatSession.query')
    def test_get_by_analysis_id(self, mock_query, sample_session):
        """Test finding sessions by analysis ID"""
        # Arrange
        mock_filter = MagicMock()
        mock_order = MagicMock()
        mock_query.filter_by.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = [sample_session]

        # Act
        result = ChatSessionDao.get_by_analysis_id(1)

        # Assert
        assert len(result) == 1
        mock_query.filter_by.assert_called_once_with(analysis_id=1, is_active=True)

    @patch('db.alchemy_db.session')
    @patch('model.chat_session.ChatSession.query')
    def test_update(self, mock_query, mock_session, sample_session):
        """Test updating a session"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter_by.return_value = mock_filter
        mock_filter.first.return_value = sample_session
        mock_session.commit.return_value = None

        # Act
        result = ChatSessionDao.update(1, {'title': 'Updated Title'})

        # Assert
        assert result is not None
        assert result.title == 'Updated Title'
        mock_session.commit.assert_called_once()

    @patch('db.alchemy_db.session')
    @patch('model.chat_session.ChatSession.query')
    def test_delete(self, mock_query, mock_session, sample_session):
        """Test soft-deleting a session"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter_by.return_value = mock_filter
        mock_filter.first.return_value = sample_session
        mock_session.commit.return_value = None

        # Act
        result = ChatSessionDao.delete(1)

        # Assert
        assert result is True
        assert sample_session.is_active is False
        mock_session.commit.assert_called_once()

    @patch('model.chat_session.ChatSession.query')
    def test_delete_not_found(self, mock_query):
        """Test deleting a non-existent session"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter_by.return_value = mock_filter
        mock_filter.first.return_value = None

        # Act
        result = ChatSessionDao.delete(999)

        # Assert
        assert result is False

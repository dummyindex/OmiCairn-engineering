"""
Unit tests for ChatMessageDao
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from dao.chat_message import ChatMessageDao, chat_message_dao
from model.chat_message import ChatMessage


@pytest.mark.unit
@pytest.mark.dao
class TestChatMessageDao:
    """Test ChatMessageDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        return ChatMessageDao()

    @pytest.fixture
    def sample_message(self):
        return ChatMessage(
            id="msg_123",
            chat_id="chat_456",
            role="user",
            content="Test message",
            created_time=datetime.now()
        )

    @patch('db.alchemy_db.session')
    def test_insert(self, mock_session, dao, sample_message):
        """Test inserting a message"""
        # Arrange
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        # Act
        result = dao.insert(sample_message)

        # Assert
        assert result is not None
        mock_session.add.assert_called_once_with(sample_message)
        mock_session.flush.assert_called_once()

    @patch('model.chat_message.ChatMessage.query')
    def test_find_by_id(self, mock_query, dao, sample_message):
        """Test finding a message by ID"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_message

        # Act
        result = dao.find_by_id("msg_123")

        # Assert
        assert result is not None
        assert result.id == "msg_123"
        mock_query.filter.assert_called_once()

    @patch('db.alchemy_db.session')
    def test_find_by_chat_id(self, mock_session, dao, sample_message):
        """Test finding messages by chat ID"""
        # Arrange
        mock_query = MagicMock()
        mock_outerjoin = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        mock_offset = MagicMock()
        mock_limit = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_outerjoin
        mock_outerjoin.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        mock_limit.all.return_value = [sample_message]

        # Act
        result = dao.find_by_chat_id("chat_456", limit=10, offset=0)

        # Assert
        assert len(result) == 1
        mock_session.query.assert_called_once()

    @patch('db.alchemy_db.session')
    def test_update(self, mock_session, dao, sample_message):
        """Test updating a message"""
        # Arrange
        mock_session.merge.return_value = sample_message
        mock_session.flush.return_value = None

        # Act
        result = dao.update(sample_message)

        # Assert
        assert result is not None
        mock_session.merge.assert_called_once_with(sample_message)
        mock_session.flush.assert_called_once()

    @patch('db.alchemy_db.session')
    @patch('model.chat_message.ChatMessage.query')
    def test_update_content(self, mock_query, mock_session, dao):
        """Test updating message content"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = 1
        mock_session.flush.return_value = None

        # Act
        result = dao.update_content("msg_123", "Updated content")

        # Assert
        assert result is True
        mock_filter.update.assert_called_once()

    @patch('db.alchemy_db.session')
    @patch('model.chat_message.ChatMessage.query')
    def test_batch_update(self, mock_query, mock_session, dao):
        """Test batch update"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = 3
        mock_session.flush.return_value = None

        # Act
        result = dao.batch_update(["msg_1", "msg_2", "msg_3"], {'is_summary': True})

        # Assert
        assert result == 3
        mock_filter.update.assert_called_once()

    @patch('db.alchemy_db.session')
    @patch('model.chat_message.ChatMessage.query')
    def test_delete_by_chat_id(self, mock_query, mock_session, dao):
        """Test deleting messages by chat ID"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = 5
        mock_session.flush.return_value = None

        # Act
        result = dao.delete_by_chat_id("chat_456")

        # Assert
        assert result is True
        mock_filter.delete.assert_called_once()

    @patch('model.chat_message.ChatMessage.query')
    def test_count_by_chat_id(self, mock_query, dao):
        """Test counting messages"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 10

        # Act
        result = dao.count_by_chat_id("chat_456")

        # Assert
        assert result == 10

    def test_singleton_instance(self):
        """Test singleton pattern"""
        assert chat_message_dao is not None
        assert isinstance(chat_message_dao, ChatMessageDao)

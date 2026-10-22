"""
Unit tests for InformDao
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from dao.inform import InformDao, inform_dao
from model.inform import Inform


@pytest.mark.unit
@pytest.mark.dao
class TestInformDao:
    """Test InformDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        return InformDao()

    @pytest.fixture
    def sample_inform(self):
        return Inform(
            id=1,
            user_id=1,
            title="Test Notification",
            content="Test content",
            inform_type="system",
            is_read=False,
            created_time=datetime.now()
        )

    @patch('db.alchemy_db.session')
    def test_insert(self, mock_session, dao, sample_inform):
        """Test inserting a notification"""
        # Arrange
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        # Act
        result = dao.insert(sample_inform)

        # Assert
        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @patch('model.inform.Inform.query')
    def test_find_by_user_id(self, mock_query, dao, sample_inform):
        """Test finding notifications by user ID"""
        # Arrange
        mock_filter = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()
        mock_offset = MagicMock()

        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.offset.return_value = mock_offset
        mock_offset.all.return_value = [sample_inform]

        # Act
        result = dao.find_by_user_id(1, limit=10, offset=0)

        # Assert
        assert len(result) == 1

    @patch('model.inform.Inform.query')
    def test_count_unread(self, mock_query, dao):
        """Test counting unread notifications"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 5

        # Act
        result = dao.count_unread(1)

        # Assert
        assert result == 5

    @patch('model.inform.Inform.query')
    def test_mark_as_read(self, mock_query, dao):
        """Test marking as read"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = 1

        # Act
        dao.mark_as_read(1)

        # Assert
        mock_filter.update.assert_called_once()

    @patch('model.inform.Inform.query')
    def test_mark_all_as_read(self, mock_query, dao):
        """Test marking all as read"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = 3

        # Act
        dao.mark_all_as_read(1)

        # Assert
        mock_filter.update.assert_called_once()

    @patch('model.inform.Inform.query')
    def test_delete(self, mock_query, dao):
        """Test deleting a notification"""
        # Arrange
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = 1

        # Act
        dao.delete(1)

        # Assert
        mock_filter.delete.assert_called_once()

    def test_singleton_instance(self):
        """Test singleton pattern"""
        assert inform_dao is not None
        assert isinstance(inform_dao, InformDao)

"""
Unit tests for LlmDao
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from dao.llm import LlmDao, llm_dao
from model.llm_consumption import LLMConsumption


@pytest.mark.unit
@pytest.mark.dao
class TestLlmDao:
    """Test LlmDao operations"""

    @pytest.fixture
    def dao(self):
        return LlmDao()

    @pytest.fixture
    def sample_consumption(self):
        return LLMConsumption(
            id=1,
            user_id=1,
            functionality="chat",
            model="gpt-4",
            total_tokens=1000,
            prompt_tokens=800,
            completion_tokens=200,
            cost=0.03,
            created_at=datetime.now()
        )

    @patch('db.alchemy_db.session')
    def test_insert_consumption(self, mock_session, dao, sample_consumption):
        """Test inserting an LLM usage record"""
        # Arrange
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        # Act
        dao.insert_consumption(sample_consumption)

        # Assert
        mock_session.add.assert_called_once_with(sample_consumption)
        mock_session.flush.assert_called_once()

    @patch('db.alchemy_db.session')
    def test_list_consumptions(self, mock_session, dao, sample_consumption):
        """Test listing a user's LLM usage"""
        # Arrange
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [sample_consumption]

        # Act
        result = dao.list_consumptions(1)

        # Assert
        assert len(result) == 1
        mock_session.query.assert_called_once()

    @patch('db.alchemy_db.session')
    def test_get_llm_consumptions_by_month(self, mock_session, dao):
        """Test aggregating LLM usage by month"""
        # Arrange
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_group = MagicMock()
        mock_order = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.group_by.return_value = mock_group
        mock_group.order_by.return_value = mock_order

        # Mock result
        mock_result = [
            (2024, 1, 'chat', 'gpt-4', 10000, 8000, 2000, 0, 0.30)
        ]
        mock_order.all.return_value = mock_result

        # Act
        result = dao.get_llm_consumptions_by_month(1)

        # Assert
        assert len(result) == 1
        assert result[0][0] == 2024  # year
        assert result[0][1] == 1     # month
        assert result[0][2] == 'chat'  # functionality
        assert result[0][3] == 'gpt-4'  # model

    def test_singleton_instance(self):
        """Test singleton pattern"""
        assert llm_dao is not None
        assert isinstance(llm_dao, LlmDao)

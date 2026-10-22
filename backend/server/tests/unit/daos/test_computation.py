"""
Unit tests for ComputationDao
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from dao.computation import ComputationDao, computation_dao
from model.computation import Computation


@pytest.mark.unit
@pytest.mark.dao
class TestComputationDao:
    """Test ComputationDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        return ComputationDao()

    @pytest.fixture
    def sample_computation(self):
        return Computation(
            id=1,
            node_id=1,
            analysis_id=1,
            user_id=1,
            status="pending",
            progress=0,
            created_time=datetime.now()
        )

    @patch('model.computation.Computation.query')
    def test_find_by_id(self, mock_query, dao, sample_computation):
        """Test finding by ID"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_computation

        result = dao.find_by_id(1)

        assert result is not None
        assert result.id == 1

    @patch('model.computation.Computation.query')
    def test_find_by_node_id(self, mock_query, dao, sample_computation):
        """Test finding by node ID"""
        mock_filter = MagicMock()
        mock_order = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = [sample_computation]

        result = dao.find_by_node_id(1)

        assert len(result) == 1
        assert result[0].node_id == 1

    @patch('model.computation.Computation.query')
    def test_find_latest_by_node_id(self, mock_query, dao, sample_computation):
        """Test finding the latest computation for a node"""
        mock_filter = MagicMock()
        mock_order = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.first.return_value = sample_computation

        result = dao.find_latest_by_node_id(1)

        assert result is not None
        assert result.node_id == 1

    @patch('db.alchemy_db.session')
    def test_insert(self, mock_session, dao, sample_computation):
        """Test inserting a computation task"""
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        result = dao.insert(sample_computation)

        assert result is not None
        mock_session.add.assert_called_once()

    @patch('model.computation.Computation.query')
    def test_update(self, mock_query, dao):
        """Test updating a computation task"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = None

        dao.update(1, {'status': 'running', 'progress': 50})

        mock_query.filter.assert_called_once()

    def test_singleton_instance(self):
        """Test singleton pattern"""
        assert computation_dao is not None
        assert isinstance(computation_dao, ComputationDao)

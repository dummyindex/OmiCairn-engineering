"""
Unit tests for EdgeDao
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from dao.edge import EdgeDao, edge_dao
from model.edge import Edge


@pytest.mark.unit
@pytest.mark.dao
class TestEdgeDao:
    """Test EdgeDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        return EdgeDao()

    @pytest.fixture
    def sample_edge(self):
        return Edge(
            id=1,
            analysis_id=1,
            source_node_id=1,
            target_node_id=2,
            source_port="output",
            target_port="input",
            created_time=datetime.now()
        )

    @patch('db.alchemy_db.session')
    def test_insert(self, mock_session, dao, sample_edge):
        """Test inserting an edge"""
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        result = dao.insert(sample_edge)

        assert result is not None
        mock_session.add.assert_called_once()

    @patch('model.edge.Edge.query')
    def test_find_by_analysis_id(self, mock_query, dao, sample_edge):
        """Test finding all edges by analysis ID"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [sample_edge]

        result = dao.find_by_analysis_id(1)

        assert len(result) == 1

    @patch('model.edge.Edge.query')
    def test_delete(self, mock_query, dao):
        """Test deleting an edge"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = None

        dao.delete(1)

        mock_filter.delete.assert_called_once()

    def test_singleton_instance(self):
        """Test singleton pattern"""
        assert edge_dao is not None
        assert isinstance(edge_dao, EdgeDao)

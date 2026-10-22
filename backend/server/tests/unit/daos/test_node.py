"""
Unit tests for NodeDao
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from dao.node import NodeDao, node_dao
from model.node import Node


@pytest.mark.unit
@pytest.mark.dao
class TestNodeDao:
    """Test NodeDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        return NodeDao()

    @pytest.fixture
    def sample_node(self):
        return Node(
            id=1,
            analysis_id=1,
            name="Test Node",
            node_type="processing",
            parameters='{}',
            position_x=100,
            position_y=100,
            created_time=datetime.now()
        )

    @patch('db.alchemy_db.session')
    def test_insert(self, mock_session, dao, sample_node):
        """Test inserting a node"""
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        result = dao.insert(sample_node)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @patch('model.node.Node.query')
    def test_find_by_id(self, mock_query, dao, sample_node):
        """Test finding by ID"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_node

        result = dao.find_by_id(1)

        assert result is not None
        assert result.id == 1

    @patch('model.node.Node.query')
    def test_find_by_analysis_id(self, mock_query, dao, sample_node):
        """Test finding all nodes by analysis ID"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [sample_node]

        result = dao.find_by_analysis_id(1)

        assert len(result) == 1

    @patch('model.node.Node.query')
    def test_update(self, mock_query, dao):
        """Test updating a node"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = None

        dao.update(1, {'name': 'Updated Node'})

        mock_query.filter.assert_called_once()

    @patch('model.node.Node.query')
    def test_delete(self, mock_query, dao):
        """Test deleting a node"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = None

        dao.delete(1)

        mock_query.filter.assert_called_once()
        mock_filter.delete.assert_called_once()

    def test_singleton_instance(self):
        """Test singleton pattern"""
        assert node_dao is not None
        assert isinstance(node_dao, NodeDao)

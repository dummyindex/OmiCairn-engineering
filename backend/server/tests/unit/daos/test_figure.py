"""
Unit tests for FigureDao
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from dao.figure import FigureDao, figure_dao
from model.figure import Figure


@pytest.mark.unit
@pytest.mark.dao
class TestFigureDao:
    """Test FigureDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        return FigureDao()

    @pytest.fixture
    def sample_figure(self):
        return Figure(
            id=1,
            computation_id=1,
            name="Test Figure",
            figure_type="plot",
            file_path="/path/to/figure.png",
            created_time=datetime.now()
        )

    @patch('db.alchemy_db.session')
    def test_insert(self, mock_session, dao, sample_figure):
        """Test inserting a figure"""
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        result = dao.insert(sample_figure)

        assert result is not None
        mock_session.add.assert_called_once()

    @patch('model.figure.Figure.query')
    def test_find_by_computation_id(self, mock_query, dao, sample_figure):
        """Test finding by computation ID"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [sample_figure]

        result = dao.find_by_computation_id(1)

        assert len(result) == 1

    @patch('model.figure.Figure.query')
    def test_delete(self, mock_query, dao):
        """Test deleting a figure"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = None

        dao.delete(1)

        mock_filter.delete.assert_called_once()

    def test_singleton_instance(self):
        """Test singleton pattern"""
        assert figure_dao is not None
        assert isinstance(figure_dao, FigureDao)

"""
Unit tests for ParamFileDao
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from dao.param_file import ParamFileDao, param_file_dao
from model.param_file import ParamFile


@pytest.mark.unit
@pytest.mark.dao
class TestParamFileDao:
    """Test ParamFileDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        return ParamFileDao()

    @pytest.fixture
    def sample_param_file(self):
        return ParamFile(
            id=1,
            uuid="test-uuid-123",
            name="test_params.yaml",
            user_id=1,
            suffix="yaml",
            content="param1: value1",
            created_time=datetime.now()
        )

    @patch('db.alchemy_db.session')
    def test_insert(self, mock_session, dao, sample_param_file):
        """Test inserting a parameter file"""
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        dao.insert(sample_param_file)

        mock_session.add.assert_called_once_with(sample_param_file)
        mock_session.flush.assert_called_once()

    @patch('model.param_file.ParamFile.query')
    def test_find_by_uuid(self, mock_query, dao, sample_param_file):
        """Test finding by UUID"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_param_file

        result = dao.find_by_uuid("test-uuid-123")

        assert result is not None
        assert result.uuid == "test-uuid-123"

    @patch('model.param_file.ParamFile.query')
    def test_find_by_user_id(self, mock_query, dao, sample_param_file):
        """Test finding by user ID"""
        mock_filter = MagicMock()
        mock_limit = MagicMock()
        mock_offset = MagicMock()

        mock_query.filter.return_value = mock_filter
        mock_filter.limit.return_value = mock_limit
        mock_limit.offset.return_value = mock_offset
        mock_offset.all.return_value = [sample_param_file]

        result = dao.find_by_user_id(1, limit=10, offset=0, search_key="")

        assert len(result) == 1

    @patch('model.param_file.ParamFile.query')
    def test_find_by_suffixes(self, mock_query, dao, sample_param_file):
        """Test finding by suffix"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [sample_param_file]

        result = dao.find_by_suffixes(["yaml", "yml"], user_id=1)

        assert len(result) == 1

    @patch('model.param_file.ParamFile.query')
    def test_delete_by_uuid(self, mock_query, dao):
        """Test deleting by UUID"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = None

        dao.delete_by_uuid("test-uuid-123")

        mock_query.filter.assert_called_once()
        mock_filter.delete.assert_called_once()

    @patch('model.param_file.ParamFile.query')
    def test_update_by_uuid(self, mock_query, dao):
        """Test updating by UUID"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = None

        dao.update_by_uuid("test-uuid-123", {'name': 'updated.yaml'})

        mock_query.filter.assert_called_once()
        mock_filter.update.assert_called_once()

    def test_singleton_instance(self):
        """Test singleton pattern"""
        assert param_file_dao is not None
        assert isinstance(param_file_dao, ParamFileDao)

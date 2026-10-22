"""
Unit tests for TaskDao
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from dao.task import TaskDao, task_dao
from model.task import Task


@pytest.mark.unit
@pytest.mark.dao
class TestTaskDao:
    """Test TaskDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        return TaskDao()

    @pytest.fixture
    def sample_task(self):
        return Task(
            id=1,
            computation_id=1,
            name="Test Task",
            status="pending",
            created_time=datetime.now()
        )

    @patch('db.alchemy_db.session')
    def test_insert(self, mock_session, dao, sample_task):
        """Test inserting a task"""
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        result = dao.insert(sample_task)

        assert result is not None
        mock_session.add.assert_called_once()

    @patch('model.task.Task.query')
    def test_find_by_computation_id(self, mock_query, dao, sample_task):
        """Test finding by computation ID"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [sample_task]

        result = dao.find_by_computation_id(1)

        assert len(result) == 1

    @patch('model.task.Task.query')
    def test_update(self, mock_query, dao):
        """Test updating a task"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = None

        dao.update(1, {'status': 'running'})

        mock_query.filter.assert_called_once()

    def test_singleton_instance(self):
        """Test the singleton pattern"""
        assert task_dao is not None
        assert isinstance(task_dao, TaskDao)

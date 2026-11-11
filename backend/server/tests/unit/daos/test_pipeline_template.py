"""
Unit tests for PipelineTemplateDao
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from dao.pipeline_template import PipelineTemplateDao, pipeline_template_dao
from model.pipeline_template import PipelineTemplate


@pytest.mark.unit
@pytest.mark.dao
class TestPipelineTemplateDao:
    """Test PipelineTemplateDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        return PipelineTemplateDao()

    @pytest.fixture
    def sample_template(self):
        return PipelineTemplate(
            id=1,
            name="Test Template",
            description="Test description",
            user_id=1,
            public=False,
            created_time=datetime.now()
        )

    @patch('db.alchemy_db.session')
    def test_insert(self, mock_session, dao, sample_template):
        """Test inserting a template"""
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        result = dao.insert(sample_template)

        assert result is not None
        mock_session.add.assert_called_once_with(sample_template)
        mock_session.flush.assert_called_once()

    @patch('db.alchemy_db.session')
    @patch('model.pipeline_template.PipelineTemplate.query')
    def test_update(self, mock_query, mock_session, dao):
        """Test updating a template"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = None
        mock_session.flush.return_value = None

        dao.update(1, {'name': 'Updated Template'})

        mock_query.filter.assert_called_once()
        mock_session.flush.assert_called_once()

    @patch('db.alchemy_db.session')
    @patch('model.pipeline_template.PipelineTemplate.query')
    def test_delete(self, mock_query, mock_session, dao):
        """Test deleting a template"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = None
        mock_session.flush.return_value = None

        dao.delete(1)

        assert mock_query.filter.call_count >= 1
        mock_session.flush.assert_called_once()

    @patch('model.pipeline_template.PipelineTemplate.query')
    def test_find_by_id(self, mock_query, dao, sample_template):
        """Test finding by ID"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_template

        result = pipeline_template_dao.find_by_id(1)

        assert result.id == 1

    def test_singleton_instance(self):
        """Test singleton pattern"""
        assert pipeline_template_dao is not None
        assert isinstance(pipeline_template_dao, PipelineTemplateDao)

"""
Unit tests for WorkflowReportDao
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from dao.workflow_report import WorkflowReportDao, workflow_report_dao
from model.workflow_report import WorkflowReport


@pytest.mark.unit
@pytest.mark.dao
class TestWorkflowReportDao:
    """Test WorkflowReportDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        return WorkflowReportDao()

    @pytest.fixture
    def sample_workflow_report(self):
        return WorkflowReport(
            id=1,
            analysis_id=1,
            title="Test Workflow Report",
            content="Report content",
            status="completed",
            created_time=datetime.now()
        )

    @patch('db.alchemy_db.session')
    def test_insert(self, mock_session, dao, sample_workflow_report):
        """Test inserting a workflow report"""
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        result = dao.insert(sample_workflow_report)

        assert result is not None
        mock_session.add.assert_called_once()

    @patch('model.workflow_report.WorkflowReport.query')
    def test_find_by_analysis_id(self, mock_query, dao, sample_workflow_report):
        """Test finding by analysis ID"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_workflow_report

        result = dao.find_by_analysis_id(1)

        assert result is not None
        assert result.analysis_id == 1

    @patch('model.workflow_report.WorkflowReport.query')
    def test_update(self, mock_query, dao):
        """Test updating a workflow report"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = None

        dao.update(1, {'status': 'published'})

        mock_query.filter.assert_called_once()

    @patch('model.workflow_report.WorkflowReport.query')
    def test_delete(self, mock_query, dao):
        """Test deleting a workflow report"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = None

        dao.delete(1)

        mock_filter.delete.assert_called_once()

    def test_singleton_instance(self):
        """Test the singleton pattern"""
        assert workflow_report_dao is not None
        assert isinstance(workflow_report_dao, WorkflowReportDao)

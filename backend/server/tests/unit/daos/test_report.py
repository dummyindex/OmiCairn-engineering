"""
Unit tests for ReportDao
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from dao.report import ReportDao, report_dao
from model.report import Report


@pytest.mark.unit
@pytest.mark.dao
class TestReportDao:
    """Test ReportDao CRUD operations"""

    @pytest.fixture
    def dao(self):
        return ReportDao()

    @pytest.fixture
    def sample_report(self):
        return Report(
            id=1,
            analysis_id=1,
            name="Test Report",
            content="Report content",
            report_type="html",
            created_time=datetime.now()
        )

    @patch('db.alchemy_db.session')
    def test_insert(self, mock_session, dao, sample_report):
        """Test inserting a report"""
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        result = dao.insert(sample_report)

        assert result is not None
        mock_session.add.assert_called_once()

    @patch('model.report.Report.query')
    def test_find_by_analysis_id(self, mock_query, dao, sample_report):
        """Test finding by analysis ID"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [sample_report]

        result = dao.find_by_analysis_id(1)

        assert len(result) == 1

    @patch('model.report.Report.query')
    def test_delete(self, mock_query, dao):
        """Test deleting a report"""
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = None

        dao.delete(1)

        mock_filter.delete.assert_called_once()

    def test_singleton_instance(self):
        """Test the singleton pattern"""
        assert report_dao is not None
        assert isinstance(report_dao, ReportDao)

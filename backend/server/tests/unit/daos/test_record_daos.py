"""
Unit tests for simple record DAOs
Includes tests for simple record tables such as open_ap_record
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


@pytest.mark.unit
@pytest.mark.dao
class TestOpenAPRecordDao:
    """Test the analysis-open record DAO"""

    @patch('db.alchemy_db.session')
    def test_insert_open_ap_record(self, mock_session):
        """Test inserting an analysis-open record"""
        from dao.open_ap_record import OpenApRecordDao
        from model.open_ap_record import OpenApRecord

        # Arrange
        dao = OpenApRecordDao()
        record = OpenApRecord(
            user_id=1,
            analysis_id=1,
            open_time=datetime.now()
        )
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        # Act
        result = dao.insert(record)

        # Assert
        assert result is not None
        mock_session.add.assert_called_once()


# Simplified test: test the singleton instance
def test_record_dao_singletons():
    """Test the singleton instance of the record DAO"""
    from dao.open_ap_record import open_ap_record_dao

    assert open_ap_record_dao is not None

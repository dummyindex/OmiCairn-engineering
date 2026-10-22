import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
from unittest.mock import patch, Mock
from datetime import datetime
import pytest

from service.analysis import AnalysisService
from model.analysis import Analysis
from model.analysis_user_relation import AnalysisUserRelation
from constants.authority import Permission, Relation


@pytest.mark.service
@pytest.mark.unit
class TestAnalysisService(unittest.TestCase):

    def setUp(self):
        self.service = AnalysisService()
        self.sample_analysis = Analysis(
            id=1,
            name="test_analysis",
            created_time=datetime.now(),
            disabled=False,
            description="Test description",
            password=None
        )

    @patch('dao.analysis.analysis_dao.find_by_user_id')
    def test_get_info_list_without_visit_time(self, mock_find):
        mock_find.return_value = [self.sample_analysis]

        result = self.service.get_info_list(1, add_latest_visit_time=False)

        self.assertEqual(len(result), 1)
        mock_find.assert_called_once_with(1)

    @patch('dao.open_ap_record.open_ap_record_dao.find_ones_latest_record_by_user_id')
    @patch('dao.analysis.analysis_dao.find_by_user_id')
    def test_get_info_list_with_visit_time(self, mock_find, mock_find_visit):
        mock_find.return_value = [self.sample_analysis]
        mock_visit_record = Mock()
        mock_visit_record.analysis_id = 1
        mock_visit_record.open_time = datetime.now()
        mock_find_visit.return_value = [mock_visit_record]

        result = self.service.get_info_list(1, add_latest_visit_time=True)

        self.assertEqual(len(result), 1)
        self.assertIn('latestVisitTime', result[0])

    @patch('dao.analysis.analysis_dao.find_by_id')
    def test_get_info_exists(self, mock_find):
        mock_find.return_value = self.sample_analysis

        result = self.service.get_info(1)

        self.assertEqual(result, self.sample_analysis)
        mock_find.assert_called_once_with(1)

    @patch('dao.analysis.analysis_dao.find_by_id')
    def test_get_info_not_exists(self, mock_find):
        mock_find.return_value = None

        result = self.service.get_info(999)

        self.assertIsNone(result)
        mock_find.assert_called_once_with(999)

    @patch('dao.analysis.analysis_dao.insert_user_relation')
    @patch('dao.analysis.analysis_dao.insert')
    def test_create_analysis(self, mock_insert, mock_insert_relation):
        new_analysis = Analysis(id=2, name="new_analysis")
        mock_insert.return_value = new_analysis
        mock_insert_relation.return_value = None

        result = self.service.create(
            user_id=1,
            name="new_analysis",
            description="New description",
            password=None
        )

        self.assertEqual(result, new_analysis)
        mock_insert.assert_called_once()
        mock_insert_relation.assert_called_once()

    @patch('dao.analysis.analysis_dao.find_by_id')
    def test_validate_password_correct(self, mock_find):
        self.sample_analysis.password = "test123"
        mock_find.return_value = self.sample_analysis

        result = self.service.validate_password(1, "test123")

        self.assertTrue(result)

    @patch('dao.analysis.analysis_dao.find_by_id')
    def test_validate_password_incorrect(self, mock_find):
        self.sample_analysis.password = "test123"
        mock_find.return_value = self.sample_analysis

        result = self.service.validate_password(1, "wrong_password")

        self.assertFalse(result)

    @patch('dao.analysis.analysis_dao.find_by_id')
    def test_validate_password_no_analysis(self, mock_find):
        mock_find.return_value = None

        result = self.service.validate_password(999, "any_password")

        # A missing analysis never validates
        self.assertFalse(result)

    @patch('dao.analysis_data_relation.analysis_data_relation_dao.insert')
    @patch('dao.data.data_dao.find_by_id')
    def test_import_data_success(self, mock_find_data, mock_insert):
        from model.data import Data

        mock_data = Data(id=1, name="test_data")
        mock_find_data.return_value = mock_data
        mock_insert.return_value = Mock()

        result = self.service.import_data(1, 1)

        self.assertIsNotNone(result)
        mock_find_data.assert_called_once_with(1)
        mock_insert.assert_called_once()

    @patch('dao.data.data_dao.find_by_id')
    def test_import_data_invalid_data_id(self, mock_find_data):
        from exception.request.parameter_invalid import ParameterInvalidException

        mock_find_data.return_value = None

        with self.assertRaises(ParameterInvalidException):
            self.service.import_data(1, 999)

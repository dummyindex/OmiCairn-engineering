import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime
import pytest

from main import create_app
from service.data import DataService
from model.data import Data
from model.analysis_data_relation import AnalysisDataRelation
from constants.data import CreatedFrom, DataState
from constants.authority import SpecialUserId, Relation, Permission


@pytest.mark.service
@pytest.mark.unit
@pytest.mark.data
class TestDataService(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()
        self.data_service = DataService()
        
        self.sample_data = Data(
            id=1,
            upload_type="csv",
            created_from=CreatedFrom.UPLOAD.value,
            created_time=datetime.now(),
            collected=False,
            name="test_data",
            species="human",
            description="Test data description",
            state=DataState.UPLOADED.value,
            error_message=None
        )

    def tearDown(self):
        self.ctx.pop()

    @patch('dao.data.data_dao.create')
    def test_create_frame_record(self, mock_create):
        mock_create.return_value = self.sample_data
        
        result = self.data_service.create_frame_record(
            user_id=1,
            upload_type="csv",
            name="test_data",
            species="human",
            description="Test data description"
        )
        
        self.assertEqual(result, self.sample_data)
        mock_create.assert_called_once()

    @patch('dao.data.data_dao.find_by_id')
    def test_get_data_by_id_exists(self, mock_find_by_id):
        mock_find_by_id.return_value = self.sample_data
        
        result = self.data_service.get_data_by_id(1)
        
        self.assertEqual(result, self.sample_data)
        mock_find_by_id.assert_called_once_with(1)

    @patch('dao.data.data_dao.find_by_id')
    def test_get_data_by_id_not_exists(self, mock_find_by_id):
        mock_find_by_id.return_value = None
        
        result = self.data_service.get_data_by_id(999)
        
        self.assertIsNone(result)
        mock_find_by_id.assert_called_once_with(999)

    @patch('dao.data.data_dao.find_by_user_id')
    def test_get_data_list_by_user(self, mock_find_by_user):
        mock_find_by_user.return_value = [self.sample_data]
        
        result = self.data_service.get_data_list_by_user(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_find_by_user.assert_called_once_with(1)

    @patch('dao.data.data_dao.update')
    def test_update_data_state(self, mock_update):
        mock_update.return_value = 1
        
        result = self.data_service.update_data_state(1, DataState.UPLOADED.value)
        
        self.assertTrue(result)
        mock_update.assert_called_once()

    @patch('dao.data.data_dao.update')
    def test_update_data_error_message(self, mock_update):
        mock_update.return_value = 1
        
        result = self.data_service.update_data_error_message(1, "Error occurred")
        
        self.assertTrue(result)
        mock_update.assert_called_once()

    @patch('dao.data.data_dao.delete_by_id')
    def test_delete_data(self, mock_delete):
        mock_delete.return_value = 1
        
        result = self.data_service.delete_data(1)
        
        self.assertTrue(result)
        mock_delete.assert_called_once_with(1)

    @patch('dao.analysis_data_relation.analysis_data_relation_dao.create')
    def test_attach_data_to_analysis(self, mock_create):
        mock_relation = AnalysisDataRelation(
            analysis_id=1,
            data_id=1,
            created_time=datetime.now()
        )
        mock_create.return_value = mock_relation
        
        result = self.data_service.attach_data_to_analysis(1, 1)
        
        self.assertEqual(result, mock_relation)
        mock_create.assert_called_once()

    @patch('dao.analysis_data_relation.analysis_data_relation_dao.delete_by_analysis_and_data')
    def test_detach_data_from_analysis(self, mock_delete):
        mock_delete.return_value = 1
        
        result = self.data_service.detach_data_from_analysis(1, 1)
        
        self.assertTrue(result)
        mock_delete.assert_called_once_with(1, 1)



    @patch('dao.data.data_dao.find_by_state')
    def test_get_data_by_state(self, mock_find_by_state):
        mock_find_by_state.return_value = [self.sample_data]
        
        result = self.data_service.get_data_by_state(DataState.UPLOADED.value)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_find_by_state.assert_called_once_with(DataState.UPLOADED.value)


    @patch('dao.data.data_dao.update')
    def test_confirm_data_upload(self, mock_update):
        mock_update.return_value = 1
        
        result = self.data_service.confirm_data_upload(1)
        
        self.assertTrue(result)
        mock_update.assert_called_once()

    @patch('dao.data.data_dao.find_by_user_and_name')
    def test_check_data_name_exists(self, mock_find):
        mock_find.return_value = [self.sample_data]
        
        result = self.data_service.check_data_name_exists(1, "test_data")
        
        self.assertTrue(result)
        mock_find.assert_called_once_with(1, "test_data")

    @patch('dao.data.data_dao.find_by_user_and_name')
    def test_check_data_name_not_exists(self, mock_find):
        mock_find.return_value = []
        
        result = self.data_service.check_data_name_exists(1, "non_existing_data")
        
        self.assertFalse(result)
        mock_find.assert_called_once_with(1, "non_existing_data")

    def test_validate_data_name_valid(self):
        result = self.data_service._validate_data_name("valid_name")
        self.assertTrue(result)

    def test_validate_data_name_empty(self):
        with self.assertRaises(Exception):
            self.data_service._validate_data_name("")

    def test_validate_data_name_none(self):
        with self.assertRaises(Exception):
            self.data_service._validate_data_name(None)

    def test_validate_species_valid(self):
        result = self.data_service._validate_species("human")
        self.assertTrue(result)

    def test_validate_upload_type_valid(self):
        result = self.data_service._validate_upload_type("csv")
        self.assertTrue(result)
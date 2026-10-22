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
from dao.data import DataDao
from model.data import Data
from model.data_user_relation import DataUserRelation
from model.computation import Computation
from constants.data import CreatedFrom, DataState
from constants.authority import Relation


@pytest.mark.dao
@pytest.mark.unit
@pytest.mark.data
class TestDataDao(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.data_dao = DataDao()
        
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
            error_message=None,
            buried=False
        )
        
        self.sample_user_relation = DataUserRelation(
            data_id=1,
            user_id=1,
            relation="owner",
            permission="read_write",
            created_time=datetime.now()
        )

    def tearDown(self):
        self.ctx.pop()

    @patch('db.alchemy_db.session')
    def test_insert_data(self, mock_session):
        mock_session.add = Mock()
        mock_session.flush = Mock()
        
        result = self.data_dao.insert(self.sample_data)
        
        self.assertEqual(result, self.sample_data)
        mock_session.add.assert_called_once_with(self.sample_data)
        mock_session.flush.assert_called_once()

    @patch('db.alchemy_db.session')
    def test_insert_user_relation(self, mock_session):
        mock_session.add = Mock()
        mock_session.flush = Mock()
        
        result = self.data_dao.insert_user_relation(self.sample_user_relation)
        
        self.assertEqual(result, self.sample_user_relation)
        mock_session.add.assert_called_once_with(self.sample_user_relation)
        mock_session.flush.assert_called_once()

    @patch('model.data.Data.query')
    def test_find_by_id_exists(self, mock_query):
        mock_query.filter.return_value.first.return_value = self.sample_data
        
        result = self.data_dao.find_by_id(1)
        
        self.assertEqual(result, self.sample_data)
        mock_query.filter.assert_called_once()

    @patch('model.data.Data.query')
    def test_find_by_id_not_exists(self, mock_query):
        mock_query.filter.return_value.first.return_value = None
        
        result = self.data_dao.find_by_id(999)
        
        self.assertIsNone(result)
        mock_query.filter.assert_called_once()

    @patch('db.alchemy_db.session')
    def test_find_isolated_and_not_buried_by_created_from_with_page(self, mock_session):
        mock_result = Mock()
        mock_result.data_id = 1
        mock_result.computation_id = None
        mock_session.query.return_value.outerjoin.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [mock_result]
        
        result = self.data_dao.find_isolated_and_not_buried_by_created_from_with_page(
            CreatedFrom.UPLOAD.value, 0, 10
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

    @patch('dao.data.DataDao.find_user_relation_by_user_id')
    @patch('model.data.Data.query')
    def test_find_by_user_id_and_upload_type_with_type(self, mock_query, mock_find_relations):
        mock_find_relations.return_value = [self.sample_user_relation]
        mock_query.filter.return_value.all.return_value = [self.sample_data]
        
        result = self.data_dao.find_by_user_id_and_upload_type(1, ["csv"], "test")
        
        self.assertIsNotNone(result)
        mock_find_relations.assert_called_once_with(1)

    @patch('dao.data.DataDao.find_by_user_id')
    def test_find_by_user_id_and_upload_type_no_type(self, mock_find_by_user):
        mock_find_by_user.return_value = [self.sample_data]
        
        result = self.data_dao.find_by_user_id_and_upload_type(1, None, "test")
        
        self.assertIsNotNone(result)
        mock_find_by_user.assert_called_once_with(1)

    @patch('model.data_user_relation.DataUserRelation.query')
    def test_find_user_relation_by_user_id(self, mock_query):
        mock_query.filter.return_value.all.return_value = [self.sample_user_relation]
        
        result = self.data_dao.find_user_relation_by_user_id(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_query.filter.assert_called_once()

    @patch('model.data_user_relation.DataUserRelation.query')
    def test_find_user_relation_by_data_id(self, mock_query):
        mock_query.filter.return_value.all.return_value = [self.sample_user_relation]
        
        result = self.data_dao.find_user_relation_by_data_id(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_query.filter.assert_called_once()

    @patch('model.data.Data.query')
    def test_find_by_user_id(self, mock_query):
        mock_query.join.return_value.filter.return_value.all.return_value = [self.sample_data]
        
        result = self.data_dao.find_by_user_id(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

    @patch('model.data.Data.query')
    def test_find_by_state(self, mock_query):
        mock_query.filter.return_value.all.return_value = [self.sample_data]
        
        result = self.data_dao.find_by_state(DataState.UPLOADED.value)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_query.filter.assert_called_once()

    @patch('model.data.Data.query')
    def test_find_by_user_and_name(self, mock_query):
        mock_query.join.return_value.filter.return_value.all.return_value = [self.sample_data]
        
        result = self.data_dao.find_by_user_and_name(1, "test_data")
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

    @patch('db.alchemy_db.session')
    @patch('model.data.Data.query')
    def test_update_data(self, mock_query, mock_session):
        mock_query.filter.return_value.first.return_value = self.sample_data
        mock_session.commit = Mock()
        
        result = self.data_dao.update(1, {"state": DataState.PROCESSED.value})
        
        mock_session.commit.assert_called_once()

    @patch('db.alchemy_db.session')
    @patch('model.data.Data.query')
    def test_delete_by_id(self, mock_query, mock_session):
        mock_query.filter.return_value.first.return_value = self.sample_data
        mock_session.delete = Mock()
        mock_session.commit = Mock()
        
        result = self.data_dao.delete_by_id(1)
        
        mock_session.delete.assert_called_once_with(self.sample_data)
        mock_session.commit.assert_called_once()

    @patch('db.alchemy_db.session')
    def test_create_data(self, mock_session):
        mock_session.add = Mock()
        mock_session.commit = Mock()
        
        data = Data(
            upload_type="csv",
            created_from=CreatedFrom.UPLOAD.value,
            created_time=datetime.now(),
            name="new_data",
            species="mouse"
        )
        
        result = self.data_dao.create(data)
        
        mock_session.add.assert_called_once_with(data)
        mock_session.commit.assert_called_once()

    @patch('model.data.Data.query')
    def test_search_by_keyword(self, mock_query):
        mock_query.filter.return_value.all.return_value = [self.sample_data]
        
        result = self.data_dao.search_by_keyword("test", 1)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_query.filter.assert_called_once()

    @patch('model.data.Data.query')
    def test_count_by_user_and_state(self, mock_query):
        mock_query.join.return_value.filter.return_value.count.return_value = 5
        
        result = self.data_dao.count_by_user_and_state(1, DataState.UPLOADED.value)
        
        self.assertEqual(result, 5)

    @patch('model.data.Data.query')
    def test_find_by_created_date_range(self, mock_query):
        mock_query.filter.return_value.all.return_value = [self.sample_data]
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        result = self.data_dao.find_by_created_date_range(start_date, end_date)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_query.filter.assert_called_once()

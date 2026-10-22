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
from dao.analysis import AnalysisDao
from model.analysis import Analysis
from model.analysis_user_relation import AnalysisUserRelation
from model.analysis_updated_record import AnalysisUpdatedRecord
from model.analysis_data_relation import AnalysisDataRelation


@pytest.mark.dao
@pytest.mark.unit
class TestAnalysisDao(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.analysis_dao = AnalysisDao()
        
        self.sample_analysis = Analysis(
            id=1,
            name="test_analysis",
            user_id=1,
            created_time=datetime.now(),
            description="Test analysis description",
            disabled=False
        )
        
        self.sample_user_relation = AnalysisUserRelation(
            analysis_id=1,
            user_id=1,
            relation="owner",
            permission="read_write",
            created_time=datetime.now()
        )

    def tearDown(self):
        self.ctx.pop()

    @patch('db.alchemy_db.session')
    def test_insert_analysis(self, mock_session):
        mock_session.add = Mock()
        mock_session.flush = Mock()
        
        result = self.analysis_dao.insert(self.sample_analysis)
        
        self.assertEqual(result, self.sample_analysis)
        mock_session.add.assert_called_once_with(self.sample_analysis)
        mock_session.flush.assert_called_once()

    @patch('db.alchemy_db.session')
    def test_insert_user_relation(self, mock_session):
        mock_session.add = Mock()
        mock_session.flush = Mock()
        
        result = self.analysis_dao.insert_user_relation(self.sample_user_relation)
        
        self.assertEqual(result, self.sample_user_relation)
        mock_session.add.assert_called_once_with(self.sample_user_relation)
        mock_session.flush.assert_called_once()

    @patch('model.analysis.Analysis.query')
    def test_find_by_id_exists(self, mock_query):
        mock_query.filter.return_value.first.return_value = self.sample_analysis
        
        result = self.analysis_dao.find_by_id(1)
        
        self.assertEqual(result, self.sample_analysis)
        mock_query.filter.assert_called_once()

    @patch('model.analysis.Analysis.query')
    def test_find_by_id_not_exists(self, mock_query):
        mock_query.filter.return_value.first.return_value = None
        
        result = self.analysis_dao.find_by_id(999)
        
        self.assertIsNone(result)
        mock_query.filter.assert_called_once()

    @patch('model.analysis_user_relation.AnalysisUserRelation.query')
    def test_find_count_by_user_id(self, mock_query):
        mock_query.filter.return_value.count.return_value = 5
        
        result = self.analysis_dao.find_count_by_user_id(1)
        
        self.assertEqual(result, 5)
        mock_query.filter.assert_called_once()

    @patch('model.analysis_user_relation.AnalysisUserRelation.query')
    def test_find_user_relation_by_user_id(self, mock_query):
        mock_query.filter.return_value.all.return_value = [self.sample_user_relation]
        
        result = self.analysis_dao.find_user_relation_by_user_id(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_query.filter.assert_called_once()

    @patch('model.analysis_user_relation.AnalysisUserRelation.query')
    def test_find_user_relation_by_analysis_id(self, mock_query):
        mock_query.filter.return_value.all.return_value = [self.sample_user_relation]
        
        result = self.analysis_dao.find_user_relation_by_analysis_id(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_query.filter.assert_called_once()

    @patch('model.analysis_user_relation.AnalysisUserRelation.query')
    def test_find_user_relation_by_analysis_and_user_ids(self, mock_query):
        mock_query.filter.return_value.all.return_value = [self.sample_user_relation]
        
        result = self.analysis_dao.find_user_relation_by_analysis_id_and_user_ids(1, [1, 2])
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_query.filter.assert_called_once()

    @patch('db.alchemy_db.session')
    @patch('model.analysis.Analysis.query')
    def test_update_analysis(self, mock_query, mock_session):
        mock_query.filter.return_value.first.return_value = self.sample_analysis
        mock_session.commit = Mock()
        
        result = self.analysis_dao.update(1, {"name": "updated_name"})
        
        mock_session.commit.assert_called_once()

    @patch('db.alchemy_db.session')
    @patch('model.analysis.Analysis.query')
    def test_delete_by_id(self, mock_query, mock_session):
        mock_query.filter.return_value.first.return_value = self.sample_analysis
        mock_session.delete = Mock()
        mock_session.commit = Mock()
        
        result = self.analysis_dao.delete_by_id(1)
        
        mock_session.delete.assert_called_once_with(self.sample_analysis)
        mock_session.commit.assert_called_once()

    @patch('model.analysis.Analysis.query')
    def test_find_by_name_and_user(self, mock_query):
        mock_query.filter.return_value.all.return_value = [self.sample_analysis]
        
        result = self.analysis_dao.find_by_name_and_user("test_analysis", 1)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_query.filter.assert_called_once()

    @patch('model.analysis.Analysis.query')
    def test_find_by_user_id(self, mock_query):
        mock_query.join.return_value.filter.return_value.all.return_value = [self.sample_analysis]
        
        result = self.analysis_dao.find_by_user_id(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

    @patch('db.alchemy_db.session')
    def test_create_analysis(self, mock_session):
        mock_session.add = Mock()
        mock_session.commit = Mock()
        
        analysis = Analysis(
            name="new_analysis",
            user_id=1,
            created_time=datetime.now(),
            description="New analysis"
        )
        
        result = self.analysis_dao.create(analysis)
        
        mock_session.add.assert_called_once_with(analysis)
        mock_session.commit.assert_called_once()

    @patch('db.alchemy_db.session')
    def test_delete_user_relation(self, mock_session):
        mock_session.delete = Mock()
        mock_session.commit = Mock()
        
        result = self.analysis_dao.delete_user_relation(1, 1)
        
        mock_session.commit.assert_called_once()

    @patch('model.analysis.Analysis.query')
    def test_search_by_keyword(self, mock_query):
        mock_query.filter.return_value.all.return_value = [self.sample_analysis]
        
        result = self.analysis_dao.search_by_keyword("test", 1)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_query.filter.assert_called_once()

    @patch('model.analysis.Analysis.query')
    def test_count_analyses_by_date_range(self, mock_query):
        mock_query.filter.return_value.count.return_value = 10
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        result = self.analysis_dao.count_by_date_range(start_date, end_date)
        
        self.assertEqual(result, 10)
        mock_query.filter.assert_called_once()

    @patch('model.analysis.Analysis.query')
    def test_find_recent_analyses(self, mock_query):
        mock_query.order_by.return_value.limit.return_value.all.return_value = [self.sample_analysis]
        
        result = self.analysis_dao.find_recent_analyses(10)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        mock_query.order_by.assert_called_once()
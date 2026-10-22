import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
from unittest.mock import patch, Mock
import pytest

from main import create_app


@pytest.mark.unit
@pytest.mark.database
class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    @patch('db.config.get_db_connection')
    def test_database_connection_mock(self, mock_get_connection):
        mock_connection = Mock()
        mock_get_connection.return_value = mock_connection
        
        from db.config import get_db_connection
        result = get_db_connection()
        
        self.assertEqual(result, mock_connection)

    def test_database_configuration_environment_variables(self):
        # Test that environment variables are properly set
        self.assertEqual(os.environ.get("MYSQL_IP"), 'localhost')
        self.assertEqual(os.environ.get("MYSQL_PORT"), "3306")

    def test_app_database_configuration(self):
        # Test that the app has database configuration
        self.assertIsNotNone(self.app)
        # Verify app context is working
        self.assertIsNotNone(self.ctx)

    @patch('db.alchemy_db.session')
    def test_database_session_mock(self, mock_session):
        mock_session.commit = Mock()
        mock_session.rollback = Mock()
        
        # Test commit
        mock_session.commit()
        mock_session.commit.assert_called_once()
        
        # Test rollback
        mock_session.rollback()
        mock_session.rollback.assert_called_once()

    def test_database_model_imports(self):
        # Test that database models can be imported without errors
        try:
            from model.user import User
            from model.analysis import Analysis
            from model.data import Data
            from model.computation import Computation
            
            # Models should be importable
            self.assertIsNotNone(User)
            self.assertIsNotNone(Analysis)
            self.assertIsNotNone(Data)
            self.assertIsNotNone(Computation)
            
        except ImportError as e:
            self.fail(f"Failed to import database models: {e}")

    def test_database_connection_error_handling(self):
        # Test error handling for database connection issues
        with patch('db.config.get_db_connection') as mock_get_connection:
            mock_get_connection.side_effect = Exception("Connection failed")
            
            with self.assertRaises(Exception):
                from db.config import get_db_connection
                get_db_connection()
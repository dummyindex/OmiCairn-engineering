import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta
import pytest

from main import create_app
from authority.guardian import AuthorityGrardian
from authority.guardian_factory import AuthorityGuardianFactory
from exception.authority.token_invalid import TokenInvalidException


@pytest.mark.unit
@pytest.mark.auth
class TestAuthority(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    @patch('flask.request')
    @patch('dao.user_token.user_token_dao.find_by_value')
    def test_authority_guardian_init_valid_token(self, mock_find_token, mock_request):
        mock_request.headers.get.return_value = "valid_token"
        
        mock_token = Mock()
        mock_token.is_overdue.return_value = False
        mock_token.user_id = 123
        mock_find_token.return_value = mock_token
        
        # Create a concrete implementation for testing
        class TestGuardian(AuthorityGrardian):
            def get_user_relations(self, object_id):
                return []
            
            def check_authority(self, object_id, check_writable=False):
                return True
            
            def check_ownership(self, object_id):
                return True
            
            def share_to_all(self, object_id):
                pass
            
            def cancel_share_to_all(self, object_id):
                pass
        
        guardian = TestGuardian()
        
        self.assertEqual(guardian.get_user_id(), 123)

    @patch('flask.request')
    @patch('dao.user_token.user_token_dao.find_by_value')
    def test_authority_guardian_init_invalid_token(self, mock_find_token, mock_request):
        mock_request.headers.get.return_value = "invalid_token"
        mock_find_token.return_value = None
        
        class TestGuardian(AuthorityGrardian):
            def get_user_relations(self, object_id):
                return []
            
            def check_authority(self, object_id, check_writable=False):
                return True
            
            def check_ownership(self, object_id):
                return True
            
            def share_to_all(self, object_id):
                pass
            
            def cancel_share_to_all(self, object_id):
                pass
        
        guardian = TestGuardian()
        
        self.assertIsNone(guardian.get_user_id())

    @patch('flask.request')
    @patch('dao.user_token.user_token_dao.find_by_value')
    def test_authority_guardian_init_overdue_token(self, mock_find_token, mock_request):
        mock_request.headers.get.return_value = "overdue_token"
        
        mock_token = Mock()
        mock_token.is_overdue.return_value = True
        mock_find_token.return_value = mock_token
        
        class TestGuardian(AuthorityGrardian):
            def get_user_relations(self, object_id):
                return []
            
            def check_authority(self, object_id, check_writable=False):
                return True
            
            def check_ownership(self, object_id):
                return True
            
            def share_to_all(self, object_id):
                pass
            
            def cancel_share_to_all(self, object_id):
                pass
        
        guardian = TestGuardian()
        
        self.assertIsNone(guardian.get_user_id())

    @patch('flask.request')
    def test_authority_guardian_no_token_header(self, mock_request):
        mock_request.headers.get.return_value = None
        
        class TestGuardian(AuthorityGrardian):
            def get_user_relations(self, object_id):
                return []
            
            def check_authority(self, object_id, check_writable=False):
                return True
            
            def check_ownership(self, object_id):
                return True
            
            def share_to_all(self, object_id):
                pass
            
            def cancel_share_to_all(self, object_id):
                pass
        
        guardian = TestGuardian()
        
        self.assertIsNone(guardian.get_user_id())

    def test_authority_guardian_abstract_methods(self):
        # Test that AuthorityGrardian cannot be instantiated directly
        with self.assertRaises(TypeError):
            AuthorityGrardian()

    @patch('authority.impl.analysis.AnalysisAuthorityGuardian')
    def test_authority_guardian_factory_create(self, mock_guardian_class):
        mock_guardian_instance = Mock()
        mock_guardian_class.return_value = mock_guardian_instance
        
        result = AuthorityGuardianFactory.create("analysis")
        
        self.assertEqual(result, mock_guardian_instance)
        mock_guardian_class.assert_called_once()


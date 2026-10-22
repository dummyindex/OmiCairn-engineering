import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT","3306")
from main import create_app
import unittest
from unittest.mock import patch
from datetime import datetime

from model.user_token import UserToken
from model.user import User
from dao.user import user_dao
from service.user import UserService
from unittest.mock import MagicMock


class TestUserService(unittest.TestCase):
    # Set up
    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()
        self.user_service = UserService()
        self.user = User(
            id=-2,
            user_name="testuser",
            phone_number='+10000000000',
            password="password123",
            created_time=datetime.now(),
            disabled=False,
            email="test@example.com",
            extend1=None
        )
        
    # Tear down
    def tearDown(self):
        self.ctx.pop()

    def test_encrypt_password(self):
        password = self.user.password
        encrypted = self.user_service.encrypt_password(password)
        self.assertIsNotNone(encrypted)
        self.assertNotEqual(encrypted, password)

    def test_verify_password(self):
        password = self.user.password
        encrypted = self.user_service.encrypt_password(password)
        self.assertNotEqual(password, encrypted)
        self.assertTrue(self.user_service.verify_password(password, encrypted))
        self.assertFalse(self.user_service.verify_password("wrong-password", encrypted))
    
    @patch('tool.user_token.UserTokenTool.generate_new_token_value', return_value='2095f52426e7411f8aa24b8f1c49d9c1')
    def test_instantiate_user_token(self, mock_generate_new_token_value: MagicMock):
        # expected token value
        user_id = -2  # Example user ID
        user_token = self.user_service.instantiate_user_token(user_id)
        mock_generate_new_token_value.assert_called_once()
        # Assertions to check if the user token is instantiated correctly
        self.assertIsInstance(user_token, UserToken)
        self.assertEqual(user_token.value, '2095f52426e7411f8aa24b8f1c49d9c1')
        self.assertFalse(user_token.disabled)
        self.assertIsNotNone(user_token.created_time)
        self.assertEqual(user_token.user_id, user_id)

    @patch('service.user.user_token_dao')
    @patch('service.user.inform_dao')
    @patch('service.user.user_dao')
    def test_register_and_login_by_password(self, mock_user_dao: MagicMock, mock_inform_dao: MagicMock, mock_token_dao: MagicMock):
        mock_user_dao.find_by_phone_number.return_value = None
        user = self.user_service.register(self.user.user_name, self.user.phone_number, self.user.password, self.user.email)
        mock_user_dao.insert.assert_called_once()
        self.assertNotEqual(user.password, self.user.password)
        self.assertTrue(self.user_service.verify_password(self.user.password, user.password))

        user.id = -2
        mock_user_dao.find_by_phone_number.return_value = user
        mock_inform_dao.find_unread_informs_by_receiver_id_and_type.return_value = []
        mock_token_dao.insert.side_effect = lambda token: token
        user_token = self.user_service.login_by_password(self.user.phone_number, self.user.password)
        self.assertIsNotNone(user_token)
        self.assertEqual(user_token.user_id, user.id)


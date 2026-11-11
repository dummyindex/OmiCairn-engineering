"""
Unit tests for UserService
"""
import pytest
from werkzeug.security import generate_password_hash, check_password_hash
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from service.user import UserService
from model.user import User
from model.user_token import UserToken
from exception.authority.login_error import LoginErrorException
from exception.authority.register_error import RegisterErrorException


@pytest.mark.unit
@pytest.mark.service
class TestUserService:
    """Test UserService business logic"""

    @pytest.fixture
    def service(self):
        return UserService()

    @pytest.fixture
    def sample_user(self):
        return User(
            id=1,
            user_name="testuser",
            phone_number="+1234567890",
            email="test@example.com",
            password=generate_password_hash("password"),
            created_time=datetime.now()
        )

    # ===== Password Tests =====

    def test_encrypt_password(self, service):
        """Test password hashing"""
        password = "password"
        encrypted = service.encrypt_password(password)

        assert encrypted is not None
        assert encrypted != password
        assert check_password_hash(encrypted, password)

    def test_verify_password_correct(self, service):
        """Test password verification - correct password"""
        password = "password"
        saved_hash = generate_password_hash("password")

        result = service.verify_password(password, saved_hash)

        assert result is True

    def test_verify_password_incorrect(self, service):
        """Test password verification - wrong password"""
        password = "wrongpassword"
        saved_hash = generate_password_hash("password")

        result = service.verify_password(password, saved_hash)

        assert result is False

    # ===== User Token Tests =====

    @patch('service.user.UserTokenTool.generate_new_token_value')
    def test_instantiate_user_token(self, mock_generate, service):
        """Test creating a user token"""
        mock_generate.return_value = "test_token_abc123"

        token = service.instantiate_user_token(user_id=1)

        assert token is not None
        assert token.user_id == 1
        assert token.value == "test_token_abc123"
        assert token.disabled is False
        assert token.end_time > datetime.now()

    @patch('service.user.UserTokenTool.generate_new_token_value')
    def test_instantiate_user_token_custom_expiry(self, mock_generate, service):
        """Test creating a user token - custom expiry time"""
        mock_generate.return_value = "test_token_abc123"
        custom_end_time = datetime.now() + timedelta(days=7)

        token = service.instantiate_user_token(user_id=1, end_time=custom_end_time)

        assert token.end_time == custom_end_time

    # ===== User Info Tests =====

    def test_list_lack_of_info_complete(self, service, sample_user):
        """Test missing-info check - info complete"""
        result = service.list_lack_of_info(sample_user)

        assert result == []

    def test_list_lack_of_info_missing_email(self, service, sample_user):
        """Test missing-info check - email missing"""
        sample_user.email = None

        result = service.list_lack_of_info(sample_user)

        assert "email" in result
        assert "user_name" not in result

    def test_list_lack_of_info_missing_multiple(self, service, sample_user):
        """Test missing-info check - multiple fields missing"""
        sample_user.email = None
        sample_user.user_name = None

        result = service.list_lack_of_info(sample_user)

        assert "email" in result
        assert "user_name" in result
        assert len(result) == 2

# singleton test
user_service = UserService()

def test_user_service_singleton():
    """Test that UserService can be instantiated"""
    assert user_service is not None
    assert isinstance(user_service, UserService)

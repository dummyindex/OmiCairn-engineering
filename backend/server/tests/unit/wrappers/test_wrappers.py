import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
from unittest.mock import patch, Mock, MagicMock
import pytest
from http import HTTPStatus

from main import create_app
from wrapper.exception import exception_wrapper
from wrapper.db_session import transaction_wrapper
from exception.authority.token_invalid import TokenInvalidException
from exception.authority.no_authority import NoAuthorityException
from exception.request.parameter_invalid import ParameterInvalidException
from exception.data.confirm import DataConfirmException
from exception.sss.upload_file import SSSUploadFileException
from exception.request.dynamic_status_code import DynamicStatusCode
from tool.response_manager import ResponseManager


@pytest.mark.unit
@pytest.mark.wrapper
class TestWrappers(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_exception_wrapper_success(self):
        @exception_wrapper
        def successful_function(self):
            return {"status": "success"}
        
        # Create a mock self object
        mock_self = Mock()
        
        result = successful_function(mock_self)
        
        self.assertEqual(result, {"status": "success"})

    def test_exception_wrapper_token_invalid(self):
        @exception_wrapper
        def token_invalid_function(self):
            raise TokenInvalidException("Invalid token")
        
        mock_self = Mock()
        
        with self.app.test_request_context():
            result = token_invalid_function(mock_self)
        
        self.assertEqual(result.status_code, HTTPStatus.UNAUTHORIZED)

    def test_exception_wrapper_no_authority(self):
        @exception_wrapper
        def no_authority_function(self):
            raise NoAuthorityException("No authority")
        
        mock_self = Mock()
        
        with self.app.test_request_context():
            result = no_authority_function(mock_self)
        
        self.assertEqual(result.status_code, HTTPStatus.UNAUTHORIZED)

    def test_exception_wrapper_parameter_invalid(self):
        @exception_wrapper
        def parameter_invalid_function(self):
            raise ParameterInvalidException("Invalid parameters")
        
        mock_self = Mock()
        
        with self.app.test_request_context():
            result = parameter_invalid_function(mock_self)
        
        self.assertEqual(result.status_code, HTTPStatus.BAD_REQUEST)

    def test_exception_wrapper_data_confirm_error(self):
        @exception_wrapper
        def data_confirm_function(self):
            raise DataConfirmException("Data confirm error")
        
        mock_self = Mock()
        
        with self.app.test_request_context():
            result = data_confirm_function(mock_self)
        
        self.assertEqual(result.status_code, HTTPStatus.BAD_REQUEST)

    def test_exception_wrapper_sss_upload_error(self):
        @exception_wrapper
        def sss_upload_function(self):
            raise SSSUploadFileException("Upload failed")
        
        mock_self = Mock()
        
        with self.app.test_request_context():
            result = sss_upload_function(mock_self)
        
        self.assertEqual(result.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_exception_wrapper_not_implemented_error(self):
        @exception_wrapper
        def not_implemented_function(self):
            raise NotImplementedError("Not implemented")
        
        mock_self = Mock()
        
        with self.app.test_request_context():
            result = not_implemented_function(mock_self)
        
        self.assertEqual(result.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_exception_wrapper_dynamic_status_code(self):
        @exception_wrapper
        def dynamic_status_function(self):
            raise DynamicStatusCode(418, "I'm a teapot")  # Custom status code
        
        mock_self = Mock()
        
        with self.app.test_request_context():
            result = dynamic_status_function(mock_self)
        
        self.assertEqual(result.status_code, 418)

    def test_exception_wrapper_generic_exception(self):
        @exception_wrapper
        def generic_exception_function(self):
            raise Exception("Generic error")
        
        mock_self = Mock()
        
        with self.app.test_request_context():
            with patch('traceback.print_exc') as mock_print_exc:
                result = generic_exception_function(mock_self)
        
        self.assertEqual(result.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        mock_print_exc.assert_called_once()

    def test_exception_wrapper_preserves_function_metadata(self):
        @exception_wrapper
        def test_function(self):
            """Test function docstring"""
            return "test"
        
        self.assertEqual(test_function.__name__, "test_function")
        self.assertEqual(test_function.__doc__, "Test function docstring")

    @patch('db.alchemy_db.session')
    def test_transaction_wrapper_success(self, mock_session):
        mock_session.commit = Mock()
        
        @transaction_wrapper
        def successful_transaction(self):
            return {"status": "success"}
        
        mock_self = Mock()
        
        result = successful_transaction(mock_self)
        
        self.assertEqual(result, {"status": "success"})
        mock_session.commit.assert_called_once()

    @patch('db.alchemy_db.session')
    def test_transaction_wrapper_exception(self, mock_session):
        mock_session.rollback = Mock()
        
        @transaction_wrapper
        def failing_transaction(self):
            raise Exception("Transaction failed")
        
        mock_self = Mock()
        
        with self.assertRaises(Exception) as context:
            failing_transaction(mock_self)
        
        self.assertEqual(str(context.exception), "Transaction failed")
        mock_session.rollback.assert_called_once()

    @patch('db.alchemy_db.session')
    def test_transaction_wrapper_preserves_exception(self, mock_session):
        mock_session.rollback = Mock()
        
        @transaction_wrapper
        def custom_exception_transaction(self):
            raise ParameterInvalidException("Custom error")
        
        mock_self = Mock()
        
        with self.assertRaises(ParameterInvalidException) as context:
            custom_exception_transaction(mock_self)
        
        self.assertEqual(str(context.exception), "Custom error")
        mock_session.rollback.assert_called_once()

    def test_transaction_wrapper_preserves_function_metadata(self):
        @transaction_wrapper
        def test_transaction(self):
            """Test transaction function"""
            return "test"
        
        self.assertEqual(test_transaction.__name__, "test_transaction")
        self.assertEqual(test_transaction.__doc__, "Test transaction function")

    @patch('db.alchemy_db.session')
    def test_combined_wrappers_success(self, mock_session):
        mock_session.commit = Mock()
        
        @exception_wrapper
        @transaction_wrapper
        def combined_function(self):
            return {"status": "success"}
        
        mock_self = Mock()
        
        result = combined_function(mock_self)
        
        self.assertEqual(result, {"status": "success"})
        mock_session.commit.assert_called_once()

    @patch('db.alchemy_db.session')
    def test_combined_wrappers_exception_handling(self, mock_session):
        mock_session.rollback = Mock()
        
        @exception_wrapper
        @transaction_wrapper
        def combined_failing_function(self):
            raise ParameterInvalidException("Combined error")
        
        mock_self = Mock()
        
        with self.app.test_request_context():
            result = combined_failing_function(mock_self)
        
        # Should handle exception with exception_wrapper and return bad request
        self.assertEqual(result.status_code, HTTPStatus.BAD_REQUEST)
        # Should also rollback transaction
        mock_session.rollback.assert_called_once()

    def test_exception_wrapper_all_exception_types(self):
        # Test all exception categories handled by the wrapper
        
        # Authority exceptions -> UNAUTHORIZED
        authority_exceptions = [TokenInvalidException, NoAuthorityException]
        for exc_class in authority_exceptions:
            @exception_wrapper
            def authority_function(self):
                raise exc_class("Authority error")
            
            with self.app.test_request_context():
                result = authority_function(Mock())
                self.assertEqual(result.status_code, HTTPStatus.UNAUTHORIZED)

        # Bad request exceptions -> BAD_REQUEST
        bad_request_exceptions = [
            ParameterInvalidException, DataConfirmException
        ]
        for exc_class in bad_request_exceptions:
            @exception_wrapper
            def bad_request_function(self):
                raise exc_class("Bad request error")
            
            with self.app.test_request_context():
                result = bad_request_function(Mock())
                self.assertEqual(result.status_code, HTTPStatus.BAD_REQUEST)

        # Server error exceptions -> INTERNAL_SERVER_ERROR
        server_error_exceptions = [
            NotImplementedError, SSSUploadFileException
        ]
        for exc_class in server_error_exceptions:
            @exception_wrapper
            def server_error_function(self):
                raise exc_class("Server error")
            
            with self.app.test_request_context():
                result = server_error_function(Mock())
                self.assertEqual(result.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_wrapper_function_signature(self):
        # Test that wrappers handle functions with correct signature
        
        @exception_wrapper
        def correct_signature_function(self):
            return "correct"
        
        @transaction_wrapper
        def correct_transaction_function(self):
            return "correct"
        
        mock_self = Mock()
        
        result1 = correct_signature_function(mock_self)
        self.assertEqual(result1, "correct")
        
        with patch('db.alchemy_db.session'):
            result2 = correct_transaction_function(mock_self)
            self.assertEqual(result2, "correct")

    @patch('db.alchemy_db.session')
    def test_transaction_wrapper_commit_failure(self, mock_session):
        # Test scenario where commit itself fails
        mock_session.commit.side_effect = Exception("Commit failed")
        mock_session.rollback = Mock()
        
        @transaction_wrapper
        def commit_failing_function(self):
            return "success"
        
        mock_self = Mock()
        
        with self.assertRaises(Exception) as context:
            commit_failing_function(mock_self)
        
        self.assertEqual(str(context.exception), "Commit failed")
        mock_session.rollback.assert_called_once()

    def test_exception_wrapper_message_preservation(self):
        # Test that exception messages are preserved in responses
        test_message = "Custom error message"
        
        @exception_wrapper
        def custom_message_function(self):
            raise ParameterInvalidException(test_message)
        
        mock_self = Mock()
        
        with self.app.test_request_context():
            result = custom_message_function(mock_self)
            response_data = result.get_json()
            self.assertIn(test_message, response_data["message"])

    def test_nested_wrapper_execution_order(self):
        # Test execution order when multiple wrappers are applied
        execution_order = []
        
        def outer_wrapper(func):
            def wrapper(self):
                execution_order.append("outer_start")
                try:
                    result = func(self)
                    execution_order.append("outer_end")
                    return result
                except Exception as e:
                    execution_order.append("outer_exception")
                    raise
            return wrapper
        
        @outer_wrapper
        @exception_wrapper
        def nested_function(self):
            execution_order.append("function_body")
            raise ParameterInvalidException("Test error")
        
        mock_self = Mock()
        
        with self.app.test_request_context():
            result = nested_function(mock_self)
        
        # Verify execution order
        expected_order = ["outer_start", "function_body", "outer_end"]
        self.assertEqual(execution_order, expected_order)
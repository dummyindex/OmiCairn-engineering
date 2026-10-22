import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
import pytest

from main import create_app
from exception.request.parameter_invalid import ParameterInvalidException
from exception.data.delete import DataDeleteException
from exception.data.collect import DataCollectException
from exception.computation.enqueue import ComputationEnqueueException
from exception.computation.state import ComputationStateException
from exception.common.not_operatable import NotOperatableException


@pytest.mark.unit
@pytest.mark.exception
class TestExceptions(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_parameter_invalid_exception_default_message(self):
        exception = ParameterInvalidException()
        
        self.assertEqual(str(exception), "parameters are invalid.")
        self.assertIsInstance(exception, Exception)

    def test_parameter_invalid_exception_custom_message(self):
        custom_message = "Custom parameter validation error"
        exception = ParameterInvalidException(custom_message)
        
        self.assertEqual(str(exception), custom_message)

    def test_parameter_invalid_exception_none_message(self):
        exception = ParameterInvalidException(None)
        
        self.assertEqual(str(exception), "parameters are invalid.")

    def test_parameter_invalid_exception_empty_message(self):
        exception = ParameterInvalidException("")
        
        self.assertEqual(str(exception), "parameters are invalid.")

    def test_data_delete_exception_default_message(self):
        exception = DataDeleteException()
        
        self.assertEqual(str(exception), "data deleted failed.")
        self.assertIsInstance(exception, Exception)

    def test_data_delete_exception_custom_message(self):
        custom_message = "Failed to delete data: file not found"
        exception = DataDeleteException(custom_message)
        
        self.assertEqual(str(exception), custom_message)

    def test_data_delete_exception_none_message(self):
        exception = DataDeleteException(None)
        
        self.assertEqual(str(exception), "data deleted failed.")

    def test_data_collect_exception_default_message(self):
        exception = DataCollectException()
        
        self.assertIsInstance(exception, Exception)
        # Test that it has a default message (assuming similar pattern)
        exception_str = str(exception)
        self.assertIsNotNone(exception_str)
        self.assertGreater(len(exception_str), 0)

    def test_data_collect_exception_custom_message(self):
        custom_message = "Failed to collect data from source"
        exception = DataCollectException(custom_message)
        
        self.assertEqual(str(exception), custom_message)

    def test_computation_enqueue_exception_default_message(self):
        exception = ComputationEnqueueException()
        
        self.assertIsInstance(exception, Exception)
        exception_str = str(exception)
        self.assertIsNotNone(exception_str)

    def test_computation_enqueue_exception_custom_message(self):
        custom_message = "Failed to enqueue computation task"
        exception = ComputationEnqueueException(custom_message)
        
        self.assertEqual(str(exception), custom_message)

    def test_computation_state_exception_default_message(self):
        exception = ComputationStateException()
        
        self.assertIsInstance(exception, Exception)
        exception_str = str(exception)
        self.assertIsNotNone(exception_str)

    def test_computation_state_exception_custom_message(self):
        custom_message = "Invalid computation state transition"
        exception = ComputationStateException(custom_message)
        
        self.assertEqual(str(exception), custom_message)

    def test_not_operatable_exception_default_message(self):
        exception = NotOperatableException()
        
        self.assertIsInstance(exception, Exception)
        exception_str = str(exception)
        self.assertIsNotNone(exception_str)

    def test_not_operatable_exception_custom_message(self):
        custom_message = "Resource is not in an operable state"
        exception = NotOperatableException(custom_message)
        
        self.assertEqual(str(exception), custom_message)

    def test_exception_inheritance(self):
        # Test that all custom exceptions inherit from Exception
        exceptions = [
            ParameterInvalidException(),
            DataDeleteException(),
            DataCollectException(),
            ComputationEnqueueException(),
            ComputationStateException(),
            NotOperatableException()
        ]
        
        for exception in exceptions:
            self.assertIsInstance(exception, Exception)

    def test_exception_raising_and_catching(self):
        # Test that exceptions can be raised and caught properly
        with self.assertRaises(ParameterInvalidException):
            raise ParameterInvalidException("Test parameter error")
        
        with self.assertRaises(DataDeleteException):
            raise DataDeleteException("Test data delete error")

    def test_exception_chaining(self):
        # Test exception chaining/wrapping
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise ParameterInvalidException("Parameter validation failed") from e
        except ParameterInvalidException as pe:
            self.assertIsInstance(pe.__cause__, ValueError)
            self.assertEqual(str(pe.__cause__), "Original error")

    def test_exception_args_property(self):
        message = "Test exception message"
        exception = ParameterInvalidException(message)
        
        self.assertEqual(exception.args[0], message)
        self.assertEqual(len(exception.args), 1)

    def test_exception_repr(self):
        message = "Test message"
        exception = ParameterInvalidException(message)
        
        repr_str = repr(exception)
        self.assertIn("ParameterInvalidException", repr_str)
        self.assertIn(message, repr_str)

    def test_multiple_exception_types_in_try_except(self):
        # Test handling multiple exception types
        def raise_different_exceptions(exception_type):
            if exception_type == "parameter":
                raise ParameterInvalidException("Parameter error")
            elif exception_type == "data":
                raise DataDeleteException("Data error")
            else:
                raise Exception("Generic error")
        
        # Test catching specific exception
        with self.assertRaises(ParameterInvalidException):
            raise_different_exceptions("parameter")
        
        # Test catching different specific exception
        with self.assertRaises(DataDeleteException):
            raise_different_exceptions("data")
        
        # Test catching with multiple exception types
        try:
            raise_different_exceptions("parameter")
        except (ParameterInvalidException, DataDeleteException) as e:
            self.assertIsInstance(e, ParameterInvalidException)

    def test_exception_message_formatting(self):
        # Test that exception messages can contain formatting
        user_id = 123
        resource_id = 456
        message = f"User {user_id} cannot access resource {resource_id}"
        exception = NotOperatableException(message)
        
        self.assertEqual(str(exception), message)
        self.assertIn(str(user_id), str(exception))
        self.assertIn(str(resource_id), str(exception))
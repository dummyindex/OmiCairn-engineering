import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
from unittest.mock import patch, Mock
import pytest
import json
from http import HTTPStatus

from main import create_app
from tool.response_manager import ResponseManager


@pytest.mark.unit
@pytest.mark.utility
class TestResponseManager(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_response_manager_init(self):
        code = 200
        message = "Success"
        data = {"key": "value"}
        
        response_manager = ResponseManager(code, message, data)
        
        self.assertEqual(response_manager.code, code)
        self.assertEqual(response_manager.message, message)
        self.assertEqual(response_manager.data, data)

    def test_response_manager_init_minimal(self):
        code = 200
        
        response_manager = ResponseManager(code)
        
        self.assertEqual(response_manager.code, code)
        self.assertIsNone(response_manager.message)
        self.assertIsNone(response_manager.data)

    def test_set_code(self):
        response_manager = ResponseManager(200)
        
        response_manager.set_code(400)
        
        self.assertEqual(response_manager.code, 400)

    def test_set_message(self):
        response_manager = ResponseManager(200)
        
        response_manager.set_message("Test message")
        
        self.assertEqual(response_manager.message, "Test message")

    def test_set_data_valid_dict(self):
        response_manager = ResponseManager(200)
        data = {"test": "value"}
        
        response_manager.set_data(data)
        
        self.assertEqual(response_manager.data, data)

    def test_set_data_invalid_type(self):
        response_manager = ResponseManager(200)
        
        with self.assertRaises(Exception) as context:
            response_manager.set_data("not a dict")
        
        self.assertIn("response data should be a dict", str(context.exception))

    def test_to_dict(self):
        code = 200
        message = "Success"
        data = {"key": "value"}
        response_manager = ResponseManager(code, message, data)
        
        result = response_manager.to_dict()
        
        expected = {
            "code": code,
            "message": message,
            "data": data
        }
        self.assertEqual(result, expected)

    def test_to_string(self):
        code = 200
        message = "Success"
        data = {"key": "value"}
        response_manager = ResponseManager(code, message, data)
        
        result = response_manager.to_string()
        
        expected_dict = {
            "code": code,
            "message": message,
            "data": data
        }
        expected_string = json.dumps(expected_dict)
        self.assertEqual(result, expected_string)

    def test_new_success_response_with_data(self):
        data = {"result": "success"}
        
        with self.app.test_request_context():
            response = ResponseManager.new_success_response(data=data)
        
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data["code"], HTTPStatus.OK)
        self.assertEqual(response_data["data"], data)

    def test_new_success_response_with_message(self):
        message = "Operation completed successfully"
        
        with self.app.test_request_context():
            response = ResponseManager.new_success_response(message=message)
        
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data["code"], HTTPStatus.OK)
        self.assertEqual(response_data["message"], message)

    def test_new_success_response_empty(self):
        with self.app.test_request_context():
            response = ResponseManager.new_success_response()
        
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data["code"], HTTPStatus.OK)
        self.assertIsNone(response_data["data"])
        self.assertIsNone(response_data["message"])

    def test_new_bad_request_response(self):
        message = "Invalid request parameters"
        
        with self.app.test_request_context():
            response = ResponseManager.new_bad_request_response(message)
        
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data["code"], HTTPStatus.BAD_REQUEST)
        self.assertEqual(response_data["message"], message)

    def test_new_not_acceptable_response(self):
        message = "Request not acceptable"
        
        with self.app.test_request_context():
            response = ResponseManager.new_not_acceptable_response(message)
        
        self.assertEqual(response.status_code, HTTPStatus.NOT_ACCEPTABLE)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data["code"], HTTPStatus.NOT_ACCEPTABLE)
        self.assertEqual(response_data["message"], message)

    def test_new_server_error_response(self):
        message = "Internal server error occurred"
        
        with self.app.test_request_context():
            response = ResponseManager.new_server_error_response(message)
        
        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data["code"], HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(response_data["message"], message)

    def test_new_unauthorized_response_with_message(self):
        message = "Access denied"
        
        with self.app.test_request_context():
            response = ResponseManager.new_unauthorized_response(message)
        
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data["code"], HTTPStatus.UNAUTHORIZED)
        self.assertEqual(response_data["message"], message)

    def test_new_unauthorized_response_default_message(self):
        with self.app.test_request_context():
            response = ResponseManager.new_unauthorized_response()
        
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data["code"], HTTPStatus.UNAUTHORIZED)
        self.assertEqual(response_data["message"], "token is invalid")

    def test_new_health_response(self):
        with self.app.test_request_context():
            response = ResponseManager.new_health_response()
        
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data["code"], HTTPStatus.OK)

    def test_new_dynamic_status_code_response(self):
        status_code = 418  # I'm a teapot
        message = "Custom status code"
        
        with self.app.test_request_context():
            response = ResponseManager.new_dynamic_status_code_response(status_code, message)
        
        self.assertEqual(response.status_code, status_code)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data["code"], status_code)
        self.assertEqual(response_data["message"], message)

    def test_new_raw_response(self):
        status_code = 200
        raw_response = "Plain text response"
        
        with self.app.test_request_context():
            response = ResponseManager.new_raw_response(status_code, raw_response)
        
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response.get_data(as_text=True), raw_response)

    def test_response_manager_chain_operations(self):
        response_manager = ResponseManager(200)
        
        response_manager.set_code(201)
        response_manager.set_message("Created")
        response_manager.set_data({"id": 123})
        
        result = response_manager.to_dict()
        
        expected = {
            "code": 201,
            "message": "Created",
            "data": {"id": 123}
        }
        self.assertEqual(result, expected)

    def test_response_manager_with_complex_data(self):
        complex_data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
            "pagination": {
                "page": 1,
                "total": 2,
                "has_more": False
            }
        }
        
        response_manager = ResponseManager(200, "Success", complex_data)
        result = response_manager.to_dict()
        
        self.assertEqual(result["data"], complex_data)

    def test_set_data_with_none(self):
        response_manager = ResponseManager(200)
        
        with self.assertRaises(Exception):
            response_manager.set_data(None)

    def test_set_data_with_list(self):
        response_manager = ResponseManager(200)
        
        with self.assertRaises(Exception):
            response_manager.set_data([1, 2, 3])

    def test_set_data_with_string(self):
        response_manager = ResponseManager(200)
        
        with self.assertRaises(Exception):
            response_manager.set_data("string data")
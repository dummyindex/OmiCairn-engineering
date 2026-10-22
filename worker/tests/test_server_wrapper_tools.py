"""
Unit tests for the server response manager.
"""

from http import HTTPStatus

import pytest
from flask import Flask

from server.tool.response_manager import ResponseManager


@pytest.fixture
def app_context():
    app = Flask(__name__)
    with app.app_context():
        yield


class TestResponseManager:
    """Test response manager utility."""

    def test_to_dict(self):
        response = ResponseManager(HTTPStatus.OK, message="ok", data={"id": 1})
        assert response.to_dict() == {
            "code": HTTPStatus.OK,
            "message": "ok",
            "data": {"id": 1},
        }

    def test_new_success_response(self, app_context):
        response = ResponseManager.new_success_response({"value": "test"})
        assert response.status_code == HTTPStatus.OK
        body = response.get_json()
        assert body["code"] == HTTPStatus.OK
        assert body["data"] == {"value": "test"}

    def test_new_bad_request_response(self, app_context):
        response = ResponseManager.new_bad_request_response("Error message")
        assert response.status_code == HTTPStatus.BAD_REQUEST
        body = response.get_json()
        assert body["code"] == HTTPStatus.BAD_REQUEST
        assert body["message"] == "Error message"

    def test_new_unauthorized_response(self, app_context):
        response = ResponseManager.new_unauthorized_response()
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.get_json()["message"] == "token is invalid"

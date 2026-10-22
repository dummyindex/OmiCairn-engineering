from http import HTTPStatus
from flask import (
    make_response,
    jsonify
)


class ResponseManager():
    def __init__(self, code, message=None, data=None) -> None:
        self.code = code
        self.message = message
        self.data = data

    def set_code(self, code):
        self.code = code

    def set_message(self, message):
        self.message = message

    def set_data(self, data: dict):
        if not isinstance(data, dict):
            raise Exception(f"response data should be a dict but {type(data)}")
        self.data = data

    def to_dict(self):
        package_dict = dict()
        package_dict["code"] = self.code
        package_dict["message"] = self.message
        package_dict["data"] = self.data
        return package_dict

    def to_string(self):
        import json
        package_dict = self.to_dict()
        return json.dumps(package_dict)

    @staticmethod
    def new_bad_request_response(message):
        response_object = ResponseManager(HTTPStatus.BAD_REQUEST, message=message)
        return make_response(jsonify(response_object.to_dict()), HTTPStatus.BAD_REQUEST)

    @staticmethod
    def new_success_response(data=None, message=None):
        response_object = ResponseManager(HTTPStatus.OK, data=data, message=message)
        return make_response(jsonify(response_object.to_dict()), HTTPStatus.OK)

    @staticmethod
    def new_not_acceptable_response(message):
        response_object = ResponseManager(HTTPStatus.NOT_ACCEPTABLE, message=message)
        return make_response(jsonify(response_object.to_dict()), HTTPStatus.NOT_ACCEPTABLE)

    @staticmethod
    def new_server_error_response(message):
        response_object = ResponseManager(HTTPStatus.INTERNAL_SERVER_ERROR, message=message)
        return make_response(jsonify(response_object.to_dict()), HTTPStatus.INTERNAL_SERVER_ERROR)

    @staticmethod
    def new_unauthorized_response(message=None):
        response_object = ResponseManager(HTTPStatus.UNAUTHORIZED, message=message or "token is invalid")
        return make_response(jsonify(response_object.to_dict()), HTTPStatus.UNAUTHORIZED)

    @staticmethod
    def new_health_response():
        response_object = ResponseManager(HTTPStatus.OK)
        return make_response(jsonify(response_object.to_dict()), HTTPStatus.OK)

    @staticmethod
    def new_dynamic_status_code_response(status_code, message):
        response_object = ResponseManager(status_code, message)
        return make_response(jsonify(response_object.to_dict()), status_code)

    @staticmethod
    def new_raw_response(status_code, raw_response):
        return make_response(raw_response, status_code)

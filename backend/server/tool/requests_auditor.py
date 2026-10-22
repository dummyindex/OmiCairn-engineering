from flask import Request

from exception.request.parameter_invalid import ParameterInvalidException


class RequestAuditor:

    def request_args_check(self, request: Request, checked_list):
        absence_list = [
            param_name
            for param_name in checked_list
            if request.args.get(
                param_name, default=None
            ) is None
        ]
        if len(absence_list) > 0:
            raise ParameterInvalidException(
                f"parameters {','.join(absence_list)} are absence")

    def request_form_check(self, request: Request, checked_list):
        absence_list = [
            param_name
            for param_name in checked_list
            if request.form.get(
                param_name, default=None
            )
            is None
        ]
        if len(absence_list) > 0:
            raise ParameterInvalidException(
                f"parameters {','.join(absence_list)} are absence")

    def request_json_check(self, request: Request, checked_list):
        request_json = request.get_json()
        absence_list = [
            param_name
            for param_name in checked_list
            if request_json.get(
                param_name, None
            )
            is None
        ]
        if len(absence_list) > 0:
            raise ParameterInvalidException(
                f"parameters {','.join(absence_list)} are absence")


# single instance
request_auditor = RequestAuditor()

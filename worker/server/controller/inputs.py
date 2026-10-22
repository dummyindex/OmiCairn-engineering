from flask import Blueprint, request
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from service.inputs import inputs_service
from log.logger_factory import LoggerFactory
from constants.authority import AuthorityCarrier

logger = LoggerFactory.get_logger("InputsController")


class InputsStructureGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """Get inputs directory structure for a node"""
        request_auditor.request_args_check(request, ["node_id"])
        node_id = request.args.get("node_id")

        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id)

        result = inputs_service.get_inputs_structure(node_id)
        return ResponseManager.new_success_response(data=result)


class FileContentGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """Get file content from inputs directory"""
        request_auditor.request_args_check(request, ["node_id", "relative_path"])
        node_id = request.args.get("node_id")
        relative_path = request.args.get("relative_path")

        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id)

        result = inputs_service.get_file_content(node_id, relative_path)
        return ResponseManager.new_success_response(data=result)


inputs_bp = Blueprint("inputs", __name__)
inputs_api = Api(inputs_bp, "/inputs")
inputs_api.add_resource(InputsStructureGetAPI, "/get-structure")
inputs_api.add_resource(FileContentGetAPI, "/get-file-content")

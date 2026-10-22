from flask_restful import Resource, Api
from flask import (
    request,
    Blueprint
)
from tool.response_manager import ResponseManager
from service.param_file import param_file_service
from wrapper.exception import exception_wrapper
from wrapper.db_session import transaction_wrapper
from tool.requests_auditor import request_auditor
from authority.guardian_factory import AuthorityGuardianFactory


class ParamFileCreateAPI(Resource):
    @transaction_wrapper
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(request, ["name", "size"])
        file_name = request.args.get("name")
        file_size = int(request.args.get("size"))
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        result = param_file_service.create_param_file(file_name, file_size, user_id)
        return ResponseManager.new_success_response(result)
    
class ParamFileRemoveAPI(Resource):
    @transaction_wrapper
    @exception_wrapper
    def delete(self):
        request_auditor.request_args_check(request, ["uuid"])
        file_uuid = request.args.get("uuid")
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        param_file = param_file_service.get_param_file_info(file_uuid)
        if param_file["userId"] != user_id:
            return ResponseManager.new_not_acceptable_response("You have no authority to delete this file")
        param_file_service.delete_param_file(file_uuid)
        return ResponseManager.new_success_response()
    
class ParamFileListAPI(Resource):
    @transaction_wrapper
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["offset", "limit", "search_key"])
        offset = int(request.args.get("offset"))
        limit = int(request.args.get("limit"))
        search_key = request.args.get("searchKey")
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        result = param_file_service.list_param_files_by_user(user_id, offset, limit, search_key)
        return ResponseManager.new_success_response(result)
    
class ParamFileInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["uuid"])
        file_uuid = request.args.get("uuid")
        result = param_file_service.get_param_file_info(file_uuid)
        return ResponseManager.new_success_response(result)

class ParamFileListInfoGetAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_json_check(request, ["uuids"])
        file_uuids = request.json["uuids"]
        result = [
            param_file_service.get_param_file_info(file_uuid)
            for file_uuid in file_uuids
        ]
        return ResponseManager.new_success_response(result)
    
class ParamFileListBySuffixesAPI(Resource):
    @transaction_wrapper
    @exception_wrapper
    def post(self):
        request_auditor.request_json_check(request, ["suffixes"])
        suffixes = request.json["suffixes"]
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        result = param_file_service.list_param_files_by_suffixes(suffixes, user_id)
        return ResponseManager.new_success_response(result)
    
class ParamFilePresignedUrlGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["uuid"])
        file_uuid = request.args.get("uuid")
        result = param_file_service.get_param_file_presigned_url(file_uuid)
        return ResponseManager.new_success_response(result)
    
class ParamFileUpdateAPI(Resource):
    @transaction_wrapper
    @exception_wrapper
    def put(self):
        request_auditor.request_args_check(request, ["uuid"])
        file_uuid = request.args.get("uuid")
        updated_attrs = request.json
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        param_file = param_file_service.get_param_file_info(file_uuid)
        if param_file["userId"] != user_id:
            return ResponseManager.new_not_acceptable_response("You have no authority to update this file")
        param_file_service.update_param_file(file_uuid, updated_attrs)
        return ResponseManager.new_success_response()

param_file_bp = Blueprint("param_file", __name__)
param_file_api = Api(param_file_bp, prefix="/param-file")
param_file_api.add_resource(ParamFileCreateAPI, "/create-file")
param_file_api.add_resource(ParamFileRemoveAPI, "/remove-file")
param_file_api.add_resource(ParamFileListAPI, "/list")
param_file_api.add_resource(ParamFileInfoGetAPI, "/get-info")
param_file_api.add_resource(ParamFileListInfoGetAPI, "/get-list-info")
param_file_api.add_resource(ParamFileListBySuffixesAPI, "/list-by-suffixes")
param_file_api.add_resource(ParamFilePresignedUrlGetAPI, "/get-presigned-url")
param_file_api.add_resource(ParamFileUpdateAPI, "/update-info")
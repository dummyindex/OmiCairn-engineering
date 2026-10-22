from flask import Blueprint, request
from flask_restful import Api, Resource

from authority.guardian_factory import AuthorityGuardianFactory
from tool.response_manager import ResponseManager
from wrapper.exception import exception_wrapper
from tool.requests_auditor import request_auditor
from service.sss import sss_service

class MultipartUploadCompleteAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "upload_id", "object_key", "parts"
        ])
        post_data = request.get_json()
        upload_id = post_data.get("upload_id")
        object_key = post_data.get("object_key")
        parts = post_data.get("parts")
        AuthorityGuardianFactory.get_authority_guardian().require_user_id()
        sss_service.complete_multipart_upload(object_key, upload_id, parts)
        return ResponseManager.new_success_response()
    
class MultipartUploadAbortAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "upload_id", "object_key"
        ])
        post_data = request.get_json()
        upload_id = post_data.get("upload_id")
        object_key = post_data.get("object_key")
        AuthorityGuardianFactory.get_authority_guardian().require_user_id()
        sss_service.abort_multipart_upload(object_key, upload_id)
        return ResponseManager.new_success_response()

class TempUploadInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        AuthorityGuardianFactory.get_authority_guardian().require_user_id()
        request_auditor.request_args_check(request, [
            "file_name", "file_size"
        ])
        file_name = request.args.get("file_name")
        file_size = request.args.get("file_size", 100)
        file_size = int(file_size)
        result = sss_service.generate_temp_upload_info(file_name, file_size)
        return ResponseManager.new_success_response(data=result)

sss_bp = Blueprint("sss", __name__)
sss_api = Api(sss_bp, prefix="/sss")
sss_api.add_resource(MultipartUploadCompleteAPI, "/multipart-upload/complete")
sss_api.add_resource(MultipartUploadAbortAPI, "/multipart-upload/abort")
sss_api.add_resource(TempUploadInfoGetAPI, "/get-temp-upload-info")
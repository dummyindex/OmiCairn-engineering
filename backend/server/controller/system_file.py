from flask import Blueprint, request, send_file
from flask_restful import Api, Resource
from service.system_file import system_file_service
from tool.response_manager import ResponseManager
from authority.guardian_factory import AuthorityGuardianFactory
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper

class DataFilesViewAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            [
                "prefix",
                "start_after_file_name"
            ]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        prefix = request.args.get("prefix")
        start_after_file_name = request.args.get("start_after_file_name")
        user_id = guardian.get_user_id()
        data_files = system_file_service.get_data_files_view(
            user_id,
            prefix,
            start_after_file_name
        )
        return ResponseManager.new_success_response(data_files)

class DataSpaceFilesViewAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            [
                "prefix",
                "start_after_file_name"
            ]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        prefix = request.args.get("prefix")
        start_after_file_name = request.args.get("start_after_file_name")
        user_id = guardian.get_user_id()
        data_space_files = system_file_service.get_data_space_files_view(
            user_id,
            prefix,
            start_after_file_name
        )
        return ResponseManager.new_success_response(data_space_files)

class ComputationOutputFilesViewAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            [
                "prefix",
                "start_after_file_name"
            ]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        prefix = request.args.get("prefix")
        start_after_file_name = request.args.get("start_after_file_name")
        user_id = guardian.get_user_id()
        computation_output_files = system_file_service.get_computation_output_files_view(
            user_id,
            prefix,
            start_after_file_name
        )
        return ResponseManager.new_success_response(computation_output_files)

class ObjectDownloadAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            [
                "object_key"
            ]
        )
        AuthorityGuardianFactory.get_authority_guardian().require_user_id()
        object_key = request.args.get("object_key")
        temp_file_path = system_file_service.get_presigned_url(object_key)
        return send_file(temp_file_path, as_attachment=True)

class ObjectCollectAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(
            request,
            [
                "object_key"
            ]
        )
        AuthorityGuardianFactory.get_authority_guardian().require_user_id()
        object_key = request.args.get("object_key")
        system_file_service.collect(object_key)
        return ResponseManager.new_success_response()

class GptSpaceFilesViewAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            [
                "prefix",
            ]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        prefix = request.args.get("prefix")
        search_key = request.args.get("search_key")
        user_id = guardian.get_user_id()
        gpt_space_files = system_file_service.get_gpt_space_files_view(
            user_id,
            prefix,
            search_key
        )
        return ResponseManager.new_success_response(gpt_space_files)

class GptSpaceFileUploadAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_form_check(
            request,
            [
                "prefix",
                "file_name"
            ]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        prefix = request.form.get("prefix")
        file_name = request.form.get("file_name")
        file = request.files["file"]
        user_id = guardian.get_user_id()
        system_file_service.upload_gpt_space_file(
            user_id,
            prefix,
            file_name,
            file
        )
        return ResponseManager.new_success_response()

class GptSpaceFileDownloadAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            [
                "prefix",
                "file_name"
            ]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        prefix = request.args.get("prefix")
        file_name = request.args.get("file_name")
        user_id = guardian.get_user_id()
        temp_file_path = system_file_service.download_gpt_space_file(
            user_id,
            prefix,
            file_name
        )
        return send_file(temp_file_path, as_attachment=True)

class GptSpaceFileDeleteAPI(Resource):
    @exception_wrapper
    def delete(self):
        request_auditor.request_args_check(
            request,
            [
                "prefix",
                "file_name"
            ]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        prefix = request.args.get("prefix")
        file_name = request.args.get("file_name")
        user_id = guardian.get_user_id()
        system_file_service.delete_gpt_space_file(
            user_id,
            prefix,
            file_name
        )
        return ResponseManager.new_success_response()

class GptSpaceFileCloneFromOtherAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(
            request,
            [
                "prefix",
                "source_object_key"
            ]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        prefix = request.args.get("prefix")
        source_object_key = request.args.get("source_object_key")
        user_id = guardian.get_user_id()
        system_file_service.copy_to_gpt_space(
            user_id,
            prefix,
            source_object_key
        )
        return ResponseManager.new_success_response()

system_file_bp = Blueprint("system_file_api", __name__)
system_file_api = Api(system_file_bp, prefix="/system-file")
system_file_api.add_resource(DataFilesViewAPI, "/browse-data-files")
system_file_api.add_resource(DataSpaceFilesViewAPI, "/browse-data-space-files")
system_file_api.add_resource(ComputationOutputFilesViewAPI, "/browse-computation-output-files")
system_file_api.add_resource(ObjectDownloadAPI, "/download-object")
system_file_api.add_resource(ObjectCollectAPI, "/collect-object")
system_file_api.add_resource(GptSpaceFilesViewAPI, "/browse-gpt-space-files")
system_file_api.add_resource(GptSpaceFileUploadAPI, "/upload-gpt-space-file")
system_file_api.add_resource(GptSpaceFileDownloadAPI, "/download-gpt-space-file")
system_file_api.add_resource(GptSpaceFileDeleteAPI, "/delete-gpt-space-file")
system_file_api.add_resource(GptSpaceFileCloneFromOtherAPI, "/clone-gpt-space-file-from-other")

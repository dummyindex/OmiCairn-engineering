from flask import Blueprint, request
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from service.user_space import user_space_service

class UserSpaceS3UploadInfoAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "prefix", "file_name", "file_size"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        prefix = request.args.get("prefix")
        file_name = request.args.get("file_name")
        file_size = int(request.args.get("file_size"))
        s3_info = user_space_service.get_upload_info(
            user_id, prefix, file_name, file_size
        )
        return ResponseManager.new_success_response(s3_info)

class UserSpaceS3DownloadInfoAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "prefix", "file_name"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        prefix = request.args.get("prefix")
        file_name = request.args.get("file_name")
        s3_info = user_space_service.get_download_info(
            user_id, prefix, file_name
        )
        return ResponseManager.new_success_response(s3_info)


class UserSpaceListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "prefix"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        prefix = request.args.get("prefix")
        list_file_info = user_space_service.list_folder(user_id, prefix)
        return ResponseManager.new_success_response(list_file_info)


class UserSpaceDeleteAPI(Resource):
    @exception_wrapper
    def delete(self):
        request_auditor.request_args_check(request, [
            "prefix", "file_name"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        prefix = request.args.get("prefix")
        file_name = request.args.get("file_name")
        user_space_service.delete_file(user_id, prefix, file_name)
        return ResponseManager.new_success_response()

class UserSpaceFolderDeleteAPI(Resource):
    @exception_wrapper
    def delete(self):
        request_auditor.request_args_check(request, [
            "prefix", "folder_name"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        prefix = request.args.get("prefix")
        folder_name = request.args.get("folder_name")
        user_space_service.delete_folder(user_id, prefix, folder_name)
        return ResponseManager.new_success_response()

class UserSpaceCollectAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "prefix", "file_name"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        prefix = request.args.get("prefix")
        file_name = request.args.get("file_name")
        user_space_service.collect_file(user_id, prefix, file_name)
        return ResponseManager.new_success_response()

class UserSpaceFileInformationGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "prefix", "file_name"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        prefix = request.args.get("prefix")
        file_name = request.args.get("file_name")
        file_info = user_space_service.get_file_information(
            user_id, prefix, file_name
        )
        return ResponseManager.new_success_response(file_info)


userspace_bp = Blueprint("user-space", __name__)
userspace_api = Api(userspace_bp, prefix="/user-space")
userspace_api.add_resource(UserSpaceS3UploadInfoAPI, "/get-s3-upload-info")
userspace_api.add_resource(UserSpaceS3DownloadInfoAPI, "/get-s3-download-info")
userspace_api.add_resource(UserSpaceListGetAPI, "/list")
userspace_api.add_resource(UserSpaceDeleteAPI, "/delete")
userspace_api.add_resource(UserSpaceFolderDeleteAPI, "/delete-folder")
userspace_api.add_resource(UserSpaceCollectAPI, "/collect")
userspace_api.add_resource(UserSpaceFileInformationGetAPI, "/get-file-info")

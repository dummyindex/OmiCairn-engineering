from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from constants.authority import AuthorityCarrier
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from wrapper.db_session import transaction_wrapper
from service.file_management import file_management_service
import io
import os
import re

WORKSPACE_KEY_PATTERN = re.compile(r"^v3-chat-workspace/(\d+)/")


def _check_analysis(analysis_id, check_writable=False):
    guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
    guardian.require_user_id()
    guardian.check_authority(analysis_id, check_writable=check_writable)


def _check_key(key, check_writable=False):
    """Require a logged-in user; if the key lies in an analysis workspace, require access to that analysis."""
    guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
    guardian.require_user_id()
    match = WORKSPACE_KEY_PATTERN.match(key or "")
    if match:
        guardian.check_authority(match.group(1), check_writable=check_writable)

class FileListGetAPI(Resource):
    @exception_wrapper
    def get(self):        
        analysis_id = request.args.get('analysis_id')
        s3_prefix = request.args.get('s3_prefix', '')
        
        if not analysis_id:
            return ResponseManager.new_bad_request_response("analysis_id is required")
        _check_analysis(analysis_id)

        files = file_management_service.list_files(analysis_id, s3_prefix=s3_prefix)
        return ResponseManager.new_success_response(files)


class FileDeleteAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def delete(self): 
        file_id = request.args.get('file_id')
        if not file_id:
            return ResponseManager.new_bad_request_response("file_id is required")
        _check_key(file_id, check_writable=True)

        file_management_service.delete_file_by_id(file_id)
        return ResponseManager.new_success_response({"message": "File deleted successfully"})


class FileUploadAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        analysis_id = request.form.get('analysis_id')
        if not analysis_id:
            return ResponseManager.new_bad_request_response("analysis_id is required")
        _check_analysis(analysis_id, check_writable=True)

        if 'file' not in request.files:
            return ResponseManager.new_bad_request_response("No file provided")

        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return ResponseManager.new_bad_request_response("No file selected")

        try:
            file_stream = io.BytesIO(uploaded_file.read())

            result = file_management_service.upload_file(
                analysis_id=analysis_id,
                file_stream=file_stream,
                file_name=uploaded_file.filename
            )

            return ResponseManager.new_success_response(result)

        except Exception as e:
            return ResponseManager.new_server_error_response(f"Upload failed: {str(e)}")


class FileContentGetAPI(Resource):
    @exception_wrapper
    def get(self):
        file_key = request.args.get('file_key')
        if not file_key:
            return ResponseManager.new_bad_request_response("file_key is required")
        
        analysis_id = request.args.get('analysis_id')
        if analysis_id:
            _check_analysis(analysis_id)
        else:
            _check_key(file_key)

        try:
            file_content = file_management_service.read_file_content(file_key, analysis_id)
            
            return Response(
                file_content,
                headers={
                    'Content-Type': 'application/octet-stream',
                    'Content-Disposition': f'attachment; filename="{os.path.basename(file_key).replace(chr(34), "")}"'
                }
            )

        except Exception as e:
            return ResponseManager.new_server_error_response(f"Read failed: {str(e)}")

class FileCopyAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        data = request.get_json() or {}

        file_name = data.get('file_name') if data else None
        source_key = data.get('source_key') if data else None
        destination_key = data.get('destination_key') if data else None

        if not source_key:
            return ResponseManager.new_bad_request_response("source_key is required")
        if not destination_key:
            return ResponseManager.new_bad_request_response("destination_key is required")
        _check_key(source_key)
        _check_key(destination_key, check_writable=True)

        try:
            result_destination_key = file_management_service.copy_file(file_name, source_key, destination_key)
            return ResponseManager.new_success_response({
                "message": "File copied successfully", 
                "destination_key": result_destination_key
            })
        except Exception as e:
            return ResponseManager.new_server_error_response(f"Copy failed: {str(e)}")
         
class FileRenameAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        data = request.get_json() or {}

        source_key = data.get('source_key') if data else None
        new_name = data.get('new_name') if data else None

        if not source_key:
            return ResponseManager.new_bad_request_response("source_key is required")
        if not new_name:
            return ResponseManager.new_bad_request_response("new_name is required")
        _check_key(source_key, check_writable=True)

        try:
            file_management_service.rename_file(source_key, new_name)
            return ResponseManager.new_success_response({"message": "File renamed successfully"})
        except Exception as e:
            return ResponseManager.new_server_error_response(f"Rename failed: {str(e)}")

class CheckFolderExistAPI(Resource):
    @exception_wrapper
    def get(self):
        folder_key = request.args.get('folder_key')
        if not folder_key:
            return ResponseManager.new_bad_request_response("folder_key is required")
        _check_key(folder_key)
        try:
            exists = file_management_service.check_folder_exist(folder_key)
            return ResponseManager.new_success_response({"exists": exists})
        except Exception as e:
            return ResponseManager.new_server_error_response(f"Check folder existence failed: {str(e)}")

file_bp = Blueprint("file", __name__)
file_api = Api(file_bp, prefix="/file")
file_api.add_resource(FileListGetAPI, "/list/get")
file_api.add_resource(FileDeleteAPI, "/remove")
file_api.add_resource(FileUploadAPI, "/upload")
file_api.add_resource(FileContentGetAPI, "/content/get")
file_api.add_resource(FileCopyAPI, "/copy")
file_api.add_resource(FileRenameAPI, "/rename")
file_api.add_resource(CheckFolderExistAPI, "/check-folder-exist")
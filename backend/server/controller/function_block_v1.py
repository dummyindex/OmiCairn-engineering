from typing import List
from flask import Blueprint, request, send_file
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from constants.function_block import MINI_TOOL_GROUP_ID, FBOccasion
from model.function_block_v1 import FunctionBlockV1
from tool.requests_auditor import request_auditor
from tool.response_manager import ResponseManager
from service.function_block_v1 import function_block_v1_service
from wrapper.exception import exception_wrapper
from wrapper.db_session import transaction_wrapper
from dto.function_block_group_dto import FunctionBlockGroupDto
from constants.authority import SpecialUserId, AuthorityCarrier
from model.function_block_group import FunctionBlockGroup
from datetime import datetime

from authority.admin import require_administrator

class PublicFunctionBlockGroupListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        function_block_groups: List[FunctionBlockGroup] = function_block_v1_service.get_group_list_by_owner_id(
            SpecialUserId.PUBLIC.value
        )
        function_block_groups = [
            FunctionBlockGroupDto(
                group,
                function_block_v1_service.get_by_group_id(group.id)
            )
            for group in function_block_groups
        ]
        return ResponseManager.new_success_response(
            function_block_groups
        )

class FunctionBlockGroupListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK.value)
        owner_id = guardian.get_user_id()
        show_function_block_list = request.args.get("show_function_block_list", "1")
        if show_function_block_list == "1":
            function_block_groups: List[FunctionBlockGroup] = function_block_v1_service.get_group_list_by_owner_id(
                owner_id
            )
            function_block_groups = [
                FunctionBlockGroupDto(
                    group,
                    function_block_v1_service.get_by_group_id(group.id)
                )
                for group in function_block_groups
            ]
            return ResponseManager.new_success_response(
                function_block_groups
            )
        else:
            function_block_groups: List[FunctionBlockGroup] = function_block_v1_service.get_group_list_by_owner_id(
                owner_id
            )
            return ResponseManager.new_success_response(
                function_block_groups
            )

class FunctionBlockInformationGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["function_block_id"]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK.value)
        function_block_id = request.args.get("function_block_id")
        guardian.check_authority(
            function_block_id
        )
        information = function_block_v1_service.get_information(
            function_block_id,
        )
        return ResponseManager.new_success_response(
            information
        )
    
class FunctionBlockVersionInformationGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["function_block_version_id"]
        )
        function_block_version_id = request.args.get("function_block_version_id")
        information = function_block_v1_service.get_version_information(
            function_block_version_id,
        )
        return ResponseManager.new_success_response(
            information
        )

class FunctionBlockGroupCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["name"]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK_GROUP.value)
        owner_id = guardian.get_user_id()
        name = request.args.get("name")
        alt_name = request.args.get("alt_name", None)
        function_block_group = function_block_v1_service.create_group(
            owner_id=owner_id,
            name=name,
            alt_name=alt_name
        )
        return ResponseManager.new_success_response(
            function_block_group
        )

class FunctionBlockCreateFormValidateAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_form_check(
            request=request,
            checked_list=["fb_name", "fb_type", "group_id", "version_name"]
        )
        fb_type = request.form.get("fb_type")
        version = request.form.get("version_name")
        function_block_v1_service.validate_creation_form(
            fb_type=fb_type,
            first_version_name=version
        )
        return ResponseManager.new_success_response()

class FunctionBlockCreateRequestAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_form_check(
            request=request,
            checked_list=["fb_name", "fb_type", "version_name", "file_size"]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK.value)
        user_id = guardian.get_user_id()
        fb_name = request.form.get("fb_name")
        fb_alt_name = request.form.get("fb_alt_name", None)
        fb_type = request.form.get("fb_type")
        group_id = request.form.get("group_id")
        version = request.form.get("version_name")
        occasion = FBOccasion.MINI_TOOL.value if MINI_TOOL_GROUP_ID == int(group_id) else FBOccasion.FLOW.value
        file_size = int(request.form.get("file_size"))
        first_version = function_block_v1_service.create_function_block(
            user_id=user_id,
            group_id=group_id,
            name=fb_name,
            alt_name=fb_alt_name,
            fb_type=fb_type,
            first_version_name=version,
            occasion=occasion
        )
        raw_fb_zip_sss_info = function_block_v1_service.get_raw_fb_zip_upload_info(first_version.id, file_size)
        result = {
            "version": first_version,
            "s3Info": raw_fb_zip_sss_info
        }
        return ResponseManager.new_success_response(
            result
        )

class PublicFunctionBlockCreateRequestAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        require_administrator()
        request_auditor.request_form_check(
            request=request,
            checked_list=["fb_name", "fb_type", "version_name", "group_id", "file_size"]
        )
        fb_name = request.form.get("fb_name")
        fb_type = request.form.get("fb_type")
        group_id = request.form.get("group_id")
        version = request.form.get("version_name")
        occasion = FBOccasion.MINI_TOOL.value if MINI_TOOL_GROUP_ID == int(group_id) else FBOccasion.FLOW.value
        file_size = int(request.form.get("file_size"))
        first_version = function_block_v1_service.create_public_function_block(
            group_id=group_id,
            name=fb_name,
            fb_type=fb_type,
            first_version_name=version,
            occasion=occasion
        )
        raw_fb_zip_sss_info = function_block_v1_service.get_raw_fb_zip_upload_info(first_version.id, file_size)
        result = {
            "version": first_version,
            "s3Info": raw_fb_zip_sss_info
        }
        return ResponseManager.new_success_response(
            result
        )

class FunctionBlockUpdateFormValidateAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_form_check(
            request=request,
            checked_list=["version_name", "function_block_id"]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK.value)
        version = request.form.get("version_name")
        function_block_id = request.form.get("function_block_id")
        owner_id = guardian.get_user_id()
        error_list = function_block_v1_service.validate_update_form(
            version_name=version,
            function_block_id=function_block_id,
            user_id=owner_id
        )
        return ResponseManager.new_success_response(data=error_list)

class FunctionBlockUpdateRequestAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_form_check(
            request=request,
            checked_list=["version_name", "function_block_id", "file_size"]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK.value)
        function_block_id = request.form.get("function_block_id")
        version = request.form.get("version_name")
        file_size = int(request.form.get("file_size"))
        owner_id = guardian.get_user_id()
        error_list = function_block_v1_service.validate_update_form(
            version_name=version,
            function_block_id=function_block_id,
            user_id=owner_id
        )
        if len(error_list) > 0:
            raise Exception(error_list)
        first_version = function_block_v1_service.create_function_block_version(
            function_block_id=function_block_id,
            first_version_name=version
        )
        raw_fb_zip_sss_info = function_block_v1_service.get_raw_fb_zip_upload_info(first_version.id, file_size)
        result = {
            "version": first_version,
            "s3Info": raw_fb_zip_sss_info
        }
        return ResponseManager.new_success_response(
            result
        )
    
class FunctionBlockVersionRewriteRequestAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_form_check(
            request=request,
            checked_list=["version_name", "function_block_id", "file_size"]
        )
        AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK.value)
        function_block_id = request.form.get("function_block_id")
        version = request.form.get("version_name")
        file_size = int(request.form.get("file_size"))
        first_version = function_block_v1_service.get_fb_version_by_name(
            function_block_id=function_block_id,
            version_name=version
        )
        if first_version is None:
            raise Exception("No such version")
        raw_fb_zip_sss_info = function_block_v1_service.get_raw_fb_zip_upload_info(first_version.id, file_size)
        result = {
            "version": first_version,
            "s3Info": raw_fb_zip_sss_info
        }
        return ResponseManager.new_success_response(
            result
        )

class FunctionBlockSearchAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["search_key"]
        )

        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK.value)
        # Search is restricted to the current user's function blocks
        owner_id = guardian.get_user_id()
        # search_key sent from the frontend
        search_key = request.args.get("search_key")

        # search_result is a list of DTOs; see server/dto/function_block_search_dto.py for details
        search_result = function_block_v1_service.get_search(search_key, owner_id)

        if len(search_result) == 0:
            return ResponseManager.new_success_response(
                search_result,
                message="No result found"
            )
        else:
            return ResponseManager.new_success_response(search_result)
        
class FunctionBlockUpdatedRecordListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            checked_list=["start_time"]
        )
        start_time = request.args.get("start_time")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK.value)
        user_id = guardian.get_user_id()
        # Convert start_time to datetime
        start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        updated_records = function_block_v1_service.get_updated_records(start_time, user_id)
        return ResponseManager.new_success_response(updated_records)

class FunctionBlockVersionListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            checked_list=["function_block_id"]
        )
        function_block_id = request.args.get("function_block_id")
        fb_v_list = function_block_v1_service.get_version_list(function_block_id)
        return ResponseManager.new_success_response(fb_v_list)

class FunctionBlockVersionSwitchAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(
            request,
            checked_list=["function_block_id", "version_id"]
        )
        function_block_id = request.args.get("function_block_id")
        version_id = request.args.get("version_id")
        new_version = function_block_v1_service.switch_version(function_block_id, version_id)
        return ResponseManager.new_success_response(new_version)

class FunctionBlockVersionPreprocessLogsGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            checked_list=["function_block_version_id"]
        )
        function_block_version_id = request.args.get("function_block_version_id")
        preprocess_logs = function_block_v1_service.get_preprocess_logs(function_block_version_id)
        return ResponseManager.new_success_response(preprocess_logs)

class FunctionBlockVersionPreviewImagesListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        function_block_version_id = request.args.get("function_block_version_id", None)
        function_block_id = request.args.get("function_block_id", None)
        preview_images_list = function_block_v1_service.get_preview_images_list(
            function_block_version_id,
            function_block_id
        )
        return ResponseManager.new_success_response(preview_images_list)
    
class MiniToolFunctionBlockListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["offset", "limit"]
        )
        AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK.value)
        offset = int(request.args.get("offset"))
        limit = int(request.args.get("limit"))
        search_key = request.args.get("search_key", None)
        fbs: List[FunctionBlockV1] = function_block_v1_service.get_mini_tool_function_blocks(
            offset=offset,
            limit=limit,
            search_key=search_key
        )
        return ResponseManager.new_success_response(
            fbs
        )
    
class MiniToolCollectedListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["offset", "limit"]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK.value)
        user_id = guardian.get_user_id()
        offset = int(request.args.get("offset"))
        limit = int(request.args.get("limit"))
        search_key = request.args.get("search_key", '')
        collected_fbs = function_block_v1_service.get_collected_minitools_by_user_id(
            user_id=user_id,
            offset=offset,
            limit=limit,
            search_key=search_key
        )
        return ResponseManager.new_success_response(
            collected_fbs
        )
    
class FunctionBlockCheckCollectedAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_json_check(
            request=request,
            checked_list=["function_block_ids"]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK.value)
        user_id = guardian.get_user_id()
        function_block_ids = request.json.get("function_block_ids")
        collected_result = function_block_v1_service.check_collected_function_blocks(
            user_id=user_id,
            function_block_id_list=function_block_ids
        )
        return ResponseManager.new_success_response(
            collected_result    
        )

class FunctionBlockCollectAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["function_block_id"]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK.value)
        user_id = guardian.get_user_id()
        function_block_id = request.args.get("function_block_id")
        collected_result = function_block_v1_service.collect_function_block(user_id, function_block_id)
        return ResponseManager.new_success_response(
            collected_result
        )
    
class FunctionBlockCancelCollectAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["function_block_id"]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK.value)
        user_id = guardian.get_user_id()
        function_block_id = request.args.get("function_block_id")
        function_block_v1_service.uncollect_function_block(user_id, function_block_id)
        return ResponseManager.new_success_response()
    
class FunctionBlockVersionPreprocessAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["function_block_version_id"]
        )
        function_block_version_id = request.args.get("function_block_version_id")
        function_block_v1_service.preprocess_function_block_version_directly(function_block_version_id)
        return ResponseManager.new_success_response()
    
class FunctionBlockVersionContentGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["function_block_version_id", "file"]
        )
        function_block_version_id = request.args.get("function_block_version_id")
        file = request.args.get("file")
        code = function_block_v1_service.get_function_block_version_code(function_block_version_id, file)
        return ResponseManager.new_success_response(
            code
        )

class FunctionBlockVersionStructureGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["function_block_version_id"]
        )
        function_block_version_id = request.args.get("function_block_version_id")
        structure = function_block_v1_service.get_function_block_version_structure(function_block_version_id)
        return ResponseManager.new_success_response(
            structure
        )
    
class FunctionBlockVersionDownloadAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["function_block_version_id"]
        )
        function_block_version_id = request.args.get("function_block_version_id")
        
        # Get version information for filename
        version_info = function_block_v1_service.get_version_information(function_block_version_id)
        if version_info is None:
            raise Exception("Function block version not found")
        
        # Get the function block name for filename
        fb = function_block_v1_service.get_information(version_info.get('function_block_id'))
        fb_name = fb.get('name', 'function_block')
        version_name = version_info.get('name', 'version')
        
        # Download the zip buffer
        zip_buffer = function_block_v1_service.download_function_block_version(function_block_version_id)
        
        # Send the file as attachment
        filename = f"{fb_name}_{version_name}.zip"
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )


class FunctionBlockVersionUpdateIsV2API(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "function_block_version_id", "is_v2"
        ])
        post_data = request.get_json()
        function_block_version_id = post_data.get("function_block_version_id")
        is_v2 = post_data.get("is_v2")
        
        # Get the function block version to find the parent function block
        version_info = function_block_v1_service.get_version_information(function_block_version_id)
        if not version_info:
            return ResponseManager.new_bad_request_response("Function block version not found")
        
        function_block_id = version_info.get('function_block_id')
        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.FUNCTION_BLOCK.value)
        guardian.check_authority(function_block_id, check_writable=True)
        
        function_block_v1_service.update_version_is_v2(function_block_version_id, is_v2)
        return ResponseManager.new_success_response()

class PublicFunctionBlockVersionV2ListAPI(Resource):
    @exception_wrapper
    def get(self):
        public_v2_fbvs = function_block_v1_service.get_existing_public_fbvs_v2()
        return ResponseManager.new_success_response(public_v2_fbvs)


function_block_v1_bp = Blueprint("function-block-v1", __name__)
function_block_v1_api = Api(function_block_v1_bp, prefix="/function-block-v1")
function_block_v1_api.add_resource(
    PublicFunctionBlockGroupListGetAPI, "/get-public-group-list"
)
function_block_v1_api.add_resource(
    FunctionBlockGroupListGetAPI, "/get-group-list"
)
function_block_v1_api.add_resource(
    FunctionBlockInformationGetAPI, "/get-information"
)
function_block_v1_api.add_resource(
    FunctionBlockVersionInformationGetAPI, "/get-version-information" 
)
function_block_v1_api.add_resource(
    FunctionBlockGroupCreateAPI, "/create-group"
)
function_block_v1_api.add_resource(
    FunctionBlockCreateFormValidateAPI, "/validate-creation-form"
)
function_block_v1_api.add_resource(
    FunctionBlockCreateRequestAPI, "/create"
)
function_block_v1_api.add_resource(
    PublicFunctionBlockCreateRequestAPI, "/create-public"
)
function_block_v1_api.add_resource(
    FunctionBlockUpdateFormValidateAPI, "/validate-update-form"
)
function_block_v1_api.add_resource(
    FunctionBlockUpdateRequestAPI, "/create-version"
)
function_block_v1_api.add_resource(
    FunctionBlockVersionRewriteRequestAPI, "/rewrite-version-by-name"
)
function_block_v1_api.add_resource(
    FunctionBlockSearchAPI, "/search"
)
function_block_v1_api.add_resource(
    FunctionBlockUpdatedRecordListGetAPI, "/get-updated-records"
)
function_block_v1_api.add_resource(
    FunctionBlockVersionListGetAPI, "/get-version-list"
)
function_block_v1_api.add_resource(
    FunctionBlockVersionSwitchAPI, "/switch-version"
)
function_block_v1_api.add_resource(
    FunctionBlockVersionPreprocessLogsGetAPI, "/get-preprocess-logs"
)
function_block_v1_api.add_resource(
    FunctionBlockVersionPreviewImagesListGetAPI, "/get-preview-images-list"
)
function_block_v1_api.add_resource(
    MiniToolFunctionBlockListGetAPI, "/get-mini-tool-list"
)
function_block_v1_api.add_resource(
    MiniToolCollectedListGetAPI, "/get-collected-mini-tool-list"
)
function_block_v1_api.add_resource(
    FunctionBlockCheckCollectedAPI, "/check-collected"
)
function_block_v1_api.add_resource(
    FunctionBlockCollectAPI, "/collect"
)
function_block_v1_api.add_resource(
    FunctionBlockCancelCollectAPI, "/cancel-collect"
)
function_block_v1_api.add_resource(
    FunctionBlockVersionPreprocessAPI, "/preprocess-version"
)
function_block_v1_api.add_resource(
    FunctionBlockVersionContentGetAPI, "/get-version-content"
)
function_block_v1_api.add_resource(
    FunctionBlockVersionStructureGetAPI, "/get-version-structure"
)
function_block_v1_api.add_resource(
    FunctionBlockVersionDownloadAPI, "/download-version"
)
function_block_v1_api.add_resource(
    FunctionBlockVersionUpdateIsV2API, "/update-version-is-v2"
)
function_block_v1_api.add_resource(
    PublicFunctionBlockVersionV2ListAPI, "/get-public-v2-fbvs"
)
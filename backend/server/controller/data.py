import os
from flask import Blueprint, request
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from constants.data import DataListFetchMode, Species, UploadType
from tool.data import DataTool
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from service.data import data_service
from constants.authority import AuthorityCarrier

class DataFrameworkFormValidateAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_form_check(request, [
            "species",
            "description"
        ])
        error_list = []
        species = request.form.get("species")
        description = request.form.get("description")
        if description is None or len(description) == 0:
            error_list.append({
                "field": "description",
                "message": "Description is required"
            })
        return ResponseManager.new_success_response(data=error_list)

class DataFrameworkCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_form_check(request, [
            "upload_type"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        owner_id = guardian.get_user_id()
        name = request.form.get("name", None)
        upload_type = request.form.get("upload_type")
        species = request.form.get("species", None)
        description = request.form.get("description", None)
        data = data_service.create_frame_record(
            owner_id, upload_type, name, species, description
        )
        return ResponseManager.new_success_response(data)


class DataUploadInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "data_id",
            "file_size"
        ])
        data_id = request.args.get("data_id")
        file_size = int(request.args.get("file_size"))
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        guardian.check_authority(data_id)
        upload_info = data_service.prepare_h5ad_upload_info(data_id, file_size)
        return ResponseManager.new_success_response(upload_info)


class DataComponentUploadInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "data_id", "component_type", "file_suffix", "file_size"
        ])
        data_id = request.args.get("data_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        guardian.check_authority(data_id)
        component_type = request.args.get("component_type")
        file_suffix = request.args.get("file_suffix")
        file_size = int(request.args.get("file_size"))
        upload_info = data_service.prepare_data_component_upload_info(
            data_id, component_type, file_suffix, file_size
        )
        return ResponseManager.new_success_response(upload_info)

class DataComponentDeleteAPI(Resource):
    @exception_wrapper
    def delete(self):
        request_auditor.request_args_check(request, [
            "data_id",
            "component_type"
        ])
        data_id = request.args.get("data_id")
        component_type = request.args.get("component_type")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        guardian.check_authority(data_id)
        data_service.remove_data_component(data_id, component_type)
        return ResponseManager.new_success_response()

class DataComponentTypeEditAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "data_id",
            "old_component_type",
            "new_component_type",
        ])
        post_data = request.get_json()
        data_id = post_data.get("data_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        guardian.check_authority(data_id)
        old_component_type = post_data.get("old_component_type")
        new_component_type = post_data.get("new_component_type")
        data_service.edit_data_component_type(
            data_id, old_component_type, new_component_type
        )
        return ResponseManager.new_success_response()


class DataComponentListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "data_id",
            "upload_type"
        ])
        data_id = request.args.get("data_id")
        upload_type = request.args.get("upload_type")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        guardian.check_authority(data_id)
        data_component_list = data_service.get_data_component_list_in_data(data_id, upload_type)
        return ResponseManager.new_success_response(data_component_list)


class DataListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "mode"
        ])
        mode = request.args.get("mode")
        search_key = request.args.get("search_key", None)
        DataTool.check_data_list_fetch_mode(mode)
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        user_id = guardian.get_user_id()
        if mode == DataListFetchMode.ALL.value:
            data_list = data_service.get_data_source_list(user_id, search_key)
        elif mode == DataListFetchMode.UPLOADED.value:
            data_list = data_service.get_uploaded_list(user_id, search_key)
        elif mode == DataListFetchMode.COLLECTED.value:
            data_list = data_service.get_collected_list(user_id, search_key)
        elif mode == DataListFetchMode.IMPORTED.value:
            request_auditor.request_args_check(
                request, ["analysis_id"]
            )
            analysis_id = request.args.get("analysis_id")
            data_list = data_service.get_imported_list_by_analysis_id(
                analysis_id
            )
        elif mode == DataListFetchMode.STATE.value:
            request_auditor.request_args_check(
                request, ["state"]
            )
            state = request.args.get("state")
            data_list = data_service.get_data_list_by_state(user_id, state, search_key)
        elif mode == DataListFetchMode.PUBLIC.value:
            data_list = data_service.get_public_list(search_key)
        elif mode == DataListFetchMode.PAGE_OF_ALL.value:
            request_auditor.request_args_check(
                request, ["page", "page_size", "only_ok"]
            )
            page = int(request.args.get("page"))
            page_size = int(request.args.get("page_size"))
            only_ok = request.args.get("only_ok", "0") == "1"
            data_list = data_service.get_data_source_page(user_id, page, page_size, search_key, only_ok)
        return ResponseManager.new_success_response(data_list)
    
class DataIndexGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "data_id",
            "search_key",
            "only_ok"
        ])
        data_id = request.args.get("data_id")
        search_key = request.args.get("search_key")
        only_ok = request.args.get("only_ok") == "1"
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        guardian.check_authority(data_id)
        user_id = guardian.get_user_id()
        index = data_service.get_data_source_index(data_id, user_id, search_key, only_ok)
        return ResponseManager.new_success_response(index)

class DataDownloadInfoGetAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "data_id"
        ])
        data_id = request.args.get("data_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        guardian.check_authority(data_id)
        user_id = guardian.get_user_id()
        download_info = data_service.prepare_h5ad_download_info(data_id, user_id)
        return ResponseManager.new_success_response(download_info)

class DataDeleteAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def delete(self):
        request_auditor.request_args_check(request, [
            "data_id"
        ])
        data_id = request.args.get("data_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        guardian.check_authority(data_id)
        user_id = guardian.get_user_id()
        data_service.remove(data_id, user_id)
        return ResponseManager.new_success_response()

class ExampleDataDownloadInfoGetAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        user_id = guardian.get_user_id()
        example_data_id = int(os.environ.get("EXAMPLE_DATA_ID", "1"))
        download_info = data_service.prepare_h5ad_download_info(example_data_id, user_id)
        return ResponseManager.new_success_response(download_info)


class ExampleDataComponentDownloadInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "component_type"
        ])
        component_type = request.args.get("component_type")
        AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        download_info = data_service.prepare_data_component_download_info(
            "example-anndata", component_type)
        return ResponseManager.new_success_response(download_info)

class DataSpeciesListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        return ResponseManager.new_success_response([
            Species.FISH.value,
            Species.MOUSE.value,
            Species.HUMAN.value
        ])


class RecentValidDataGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "node_id"
        ])
        node_id = request.args.get("node_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id)
        data = data_service.get_recent_valid_data(node_id)
        return ResponseManager.new_success_response(data)


class CollectAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "node_id",
            "data_name"
        ])
        node_id = request.args.get("node_id")
        data_name = request.args.get("data_name")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id)
        data_service.collect(node_id, data_name)
        return ResponseManager.new_success_response()

class EditAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "data_id"
        ])
        post_data = request.get_json()
        data_id = post_data.get("data_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        guardian.check_authority(data_id)
        name = post_data.get("name", None)
        description = post_data.get("description", None)
        data_service.edit(data_id, name, description)
        return ResponseManager.new_success_response()
    
class DataInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "data_id"
        ])
        data_id = request.args.get("data_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        guardian.check_authority(data_id)
        data_info = data_service.get_data_info(data_id)
        return ResponseManager.new_success_response(data_info)
    
class DataSourceGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "data_id"
        ])
        data_id = request.args.get("data_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        guardian.check_authority(data_id)
        data = data_service.get_source_data_info(data_id)
        return ResponseManager.new_success_response(data)
    
class ThirtyPartDataSourcePageGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "page",
            "page_size"
        ])
        page = int(request.args.get("page"))
        page_size = int(request.args.get("page_size"))
        search = request.args.get("search", None)
        sort = request.args.get("sort", None)
        order = request.args.get("order", None)
        page_result = data_service.get_thirty_part_data_source_list(
            page, page_size, search, sort, order
        )
        return ResponseManager.new_success_response(page_result)
    
class ReferencedStateGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "data_id"
        ])
        data_id = request.args.get("data_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value)
        guardian.check_authority(data_id)
        state = data_service.get_referenced_state(data_id)
        return ResponseManager.new_success_response(state)

class GeneralInputsListAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "data_id"
        ])
        AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value).require_user_id()
        data_id = request.args.get("data_id")
        prefix = request.args.get("prefix", None)
        start_after_file_name = request.args.get("start_after_file_name", "")
        max_keys = request.args.get("max_keys", 50, type=int)
        search_query = request.args.get("search_query", None)
        file_type_filter = request.args.get("file_type_filter", None)

        result = data_service.list_general_inputs(
            data_id, prefix, start_after_file_name,
            max_keys, search_query, file_type_filter)
        return ResponseManager.new_success_response(data=result)
    
class GeneralInputsItemDownloadInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            [
                "object_key",
                "data_id"
            ]
        )
        AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.DATA.value).require_user_id()
        data_id = request.args.get("data_id")
        object_key = request.args.get("object_key")
        # Only presign objects inside this data's general store (as listed by /list-general-inputs).
        if not object_key.startswith(f"adata/{data_id}-general-s3-store/") or ".." in object_key:
            return ResponseManager.new_bad_request_response("object_key is not part of this data")
        result = data_service.get_general_inputs_item_download_info(object_key)
        return ResponseManager.new_success_response(data=result)

data_bp = Blueprint("data", __name__)
data_api = Api(data_bp, prefix="/data")
data_api.add_resource(DataFrameworkFormValidateAPI, "/validate-creation-form")
data_api.add_resource(DataFrameworkCreateAPI, "/framework/create")
data_api.add_resource(DataUploadInfoGetAPI, "/upload/info/get")
data_api.add_resource(DataComponentTypeEditAPI, "/edit-component-type")
data_api.add_resource(DataComponentUploadInfoGetAPI,
                      "/component/upload/info/get")
data_api.add_resource(DataComponentListGetAPI, "/component/list/get")
data_api.add_resource(DataListGetAPI, "/list/get")
data_api.add_resource(DataIndexGetAPI, "/get-data-index")
data_api.add_resource(DataDownloadInfoGetAPI, "/download/info/get")
data_api.add_resource(ExampleDataDownloadInfoGetAPI,
                      "/download/example-info/get")
data_api.add_resource(DataDeleteAPI, "/remove")
data_api.add_resource(DataComponentDeleteAPI, "/remove-component")
data_api.add_resource(ExampleDataComponentDownloadInfoGetAPI,
                      "/component/download/example_info/get")
data_api.add_resource(DataSpeciesListGetAPI, "/species/list/get")
data_api.add_resource(RecentValidDataGetAPI, "/recent-valid/get")
data_api.add_resource(CollectAPI, "/collect")
data_api.add_resource(EditAPI, "/edit")
data_api.add_resource(DataInfoGetAPI, "/get-data-info")
data_api.add_resource(DataSourceGetAPI, "/get-source-data")
data_api.add_resource(ThirtyPartDataSourcePageGetAPI, "/page-3-part-data-source")
data_api.add_resource(ReferencedStateGetAPI, "/get-referenced-state")
data_api.add_resource(GeneralInputsListAPI, "/list-general-inputs")
data_api.add_resource(GeneralInputsItemDownloadInfoGetAPI, "/get-general-input-item-download-info")
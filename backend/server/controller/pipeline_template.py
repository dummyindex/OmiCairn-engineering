from flask import Blueprint, request
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from constants.authority import SpecialUserId
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from service.pipeline_template import (
    pipeline_template_service as pt_service
)
from constants.authority import AuthorityCarrier
from model.pipeline_template import PipelineTemplate


class PipelineTemplateCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(
            request, ['name', 'node_id_list', 'edge_id_list', 'group_name'])
        post_data = request.get_json()
        name = post_data.get('name')
        node_id_list = post_data.get('node_id_list')
        edge_id_list = post_data.get('edge_id_list')
        group_name = post_data.get('group_name')
        description = post_data.get('description', None)
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        for node_id in node_id_list:
            guardian.check_authority(node_id)
        owner_id = guardian.get_user_id()
        pt: PipelineTemplate = pt_service.create(
            name,
            node_id_list,
            edge_id_list,
            owner_id,
            group_name,
            description
        )
        return ResponseManager.new_success_response(pt)

class PipelineTemplateListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request, ['group_name'])
        group_name = request.args.get('group_name')
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        owner_id = guardian.get_user_id()
        pt_list = pt_service.get_list_by_owner_id_and_group_name(
            owner_id,
            group_name
        )
        return ResponseManager.new_success_response(pt_list)

class PipelineTemplateGroupNameListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        group_name_list = pt_service.get_group_name_list_by_user_id(
            user_id
        )
        return ResponseManager.new_success_response(group_name_list)


class FunctionBlockListGetByPipelineTemplateAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request, ['pipeline_template_id'])
        pipeline_template_id = request.args.get('pipeline_template_id')
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.PIPELINE_TEMPLATE.value)
        guardian.check_authority(pipeline_template_id)
        fb_list = pt_service.get_function_block_list_by_pipeline_template_id(
            pipeline_template_id
        )
        return ResponseManager.new_success_response(fb_list)

class GroupNameEditAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(
            request, ['old_name', 'new_name'])
        post_data = request.get_json()
        old_name = post_data.get('old_name')
        new_name = post_data.get('new_name')
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        pt_service.edit_group_name_by_user_id_and_old_name(
            user_id,
            old_name,
            new_name
        )
        return ResponseManager.new_success_response()

class GroupRemoveAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def delete(self):
        request_auditor.request_args_check(
            request, ['group_name'])
        group_name = request.args.get('group_name')
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        pt_service.remove_group_by_user_id_and_group_name(
            user_id,
            group_name
        )
        return ResponseManager.new_success_response()

class PipelineTemplateMetadataEditAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(
            request, ['pipeline_template_id'])
        post_data = request.get_json()
        pipeline_template_id = post_data.get('pipeline_template_id')
        name = post_data.get('name', None)
        group_name = post_data.get('group_name' ,None)
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.PIPELINE_TEMPLATE.value)
        guardian.check_authority(pipeline_template_id)
        pt_service.edit_metadata(
            pipeline_template_id,
            name,
            group_name
        )
        return ResponseManager.new_success_response()

class PipelineTemplateRemoveAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def delete(self):
        request_auditor.request_args_check(
            request, ['pipeline_template_id'])
        pipeline_template_id = request.args.get('pipeline_template_id')
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.PIPELINE_TEMPLATE.value)
        guardian.check_authority(pipeline_template_id)
        pt_service.remove(pipeline_template_id)
        return ResponseManager.new_success_response()

class ImportIntoAnalysisAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(
            request, ['pipeline_template_id', 'analysis_id'])
        post_data = request.get_json()
        pipeline_template_id = post_data.get('pipeline_template_id')
        analysis_id = post_data.get('analysis_id')
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.PIPELINE_TEMPLATE.value)
        user_id = guardian.get_user_id()
        guardian.check_authority(pipeline_template_id)
        import_result = pt_service.import_into_analysis(
            pipeline_template_id,
            analysis_id,
            user_id
        )
        return ResponseManager.new_success_response(data=import_result)

class PublicPipelineTemplateListGet(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request, ['group_name'])
        group_name = request.args.get('group_name')
        pt_list = pt_service.get_list_by_owner_id_and_group_name(
            SpecialUserId.PUBLIC.value,
            group_name
        )
        return ResponseManager.new_success_response(pt_list)

class PublicPipelineTemplateGroupNameListGet(Resource):
    @exception_wrapper
    def get(self):
        group_name_list = pt_service.get_group_name_list_by_user_id(
            SpecialUserId.PUBLIC.value
        )
        return ResponseManager.new_success_response(group_name_list)

class PipelineTemplateTurnOverToPublicAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(
            request, ['pipeline_template_id'])
        post_data = request.get_json()
        pipeline_template_id = post_data.get('pipeline_template_id')
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.PIPELINE_TEMPLATE.value)
        guardian.check_authority(pipeline_template_id)
        pt_service.turn_over_to_public(pipeline_template_id)
        return ResponseManager.new_success_response()


pipeline_template_bp = Blueprint('pipeline_template', __name__)
pipeline_template_api = Api(pipeline_template_bp, prefix='/pipeline-template')

pipeline_template_api.add_resource(
    PipelineTemplateCreateAPI,
    '/create'
)

pipeline_template_api.add_resource(
    PipelineTemplateListGetAPI,
    '/list/get'
)

pipeline_template_api.add_resource(
    FunctionBlockListGetByPipelineTemplateAPI,
    '/function-block/list/get'
)

pipeline_template_api.add_resource(
    GroupNameEditAPI,
    '/group-name/edit'
)

pipeline_template_api.add_resource(
    GroupRemoveAPI,
    '/group/remove'
)

pipeline_template_api.add_resource(
    PipelineTemplateMetadataEditAPI,
    '/metadata/edit'
)

pipeline_template_api.add_resource(
    PipelineTemplateRemoveAPI,
    '/remove'
)

pipeline_template_api.add_resource(
    PipelineTemplateGroupNameListGetAPI,
    '/group-name/list/get'
)

pipeline_template_api.add_resource(
    ImportIntoAnalysisAPI,
    '/import-into-analysis'
)

pipeline_template_api.add_resource(
    PublicPipelineTemplateListGet,
    '/public/list/get'
)

pipeline_template_api.add_resource(
    PublicPipelineTemplateGroupNameListGet,
    '/public/group-name/list/get'
)

pipeline_template_api.add_resource(
    PipelineTemplateTurnOverToPublicAPI,
    '/turn-over-to-public'
)

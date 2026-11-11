from flask import Blueprint, request
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from exception.request.parameter_invalid import ParameterInvalidException
from exception.common.not_operatable import NotOperatableException
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from service.flow import flow_service
from wrapper.exception import exception_wrapper
from constants.authority import AuthorityCarrier

class GeneratePipelineByGptAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        user_id = guardian.get_user_id()
        request_auditor.request_json_check(
            request,
            [
                "recommend_structure",
                "analysis_id"
            ]
        )
        post_data = request.get_json()
        recommend_structure = post_data["recommend_structure"]
        analysis_id = post_data["analysis_id"]
        nodes_and_edges = flow_service.generate_pipeline_by_gpt(recommend_structure, analysis_id, user_id)
        return ResponseManager.new_success_response(nodes_and_edges)

flow_bp = Blueprint('flow', __name__)
flow_api = Api(flow_bp, prefix="/flow")
flow_api.add_resource(GeneratePipelineByGptAPI, "/generate-pipeline-by-gpt")

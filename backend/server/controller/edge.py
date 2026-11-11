from flask import Blueprint, request
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from service.flow import flow_service
from wrapper.exception import exception_wrapper
from typing import List
from model.edge import Edge
from constants.authority import AuthorityCarrier
from dao.edge import edge_dao
from exception.request.parameter_invalid import ParameterInvalidException


class EdgeCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        request_auditor.request_form_check(
            request=request,
            checked_list=["analysis_id", "source_node_id", "target_node_id"]
        )
        analysis_id = int(request.form.get("analysis_id"))
        source_node_id = int(request.form.get("source_node_id"))
        target_node_id = int(request.form.get("target_node_id"))
        guardian.check_authority(analysis_id)

        edge = flow_service.create_edge(
            source_node_id,
            target_node_id,
            analysis_id
        )
        return ResponseManager.new_success_response(edge)


class EdgeListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        request_auditor.request_args_check(
            request=request,
            checked_list=["analysis_id"]
        )
        analysis_id = request.args.get("analysis_id")
        guardian.check_authority(analysis_id)
        edge_list: List[Edge] = flow_service.get_edge_list_by_analysis_id(
            analysis_id)
        return ResponseManager.new_success_response(data=edge_list)


class EdgeDeleteAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def delete(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        request_auditor.request_args_check(
            request=request,
            checked_list=["edge_id"]
        )
        edge_id = request.args.get("edge_id")
        edge = edge_dao.find_by_id(edge_id)
        if edge is None:
            raise ParameterInvalidException("edge_id is invalid.")
        guardian.check_authority(edge.analysis_id, check_writable=True)
        flow_service.remove_edge(edge_id)
        return ResponseManager.new_success_response()


edge_bp = Blueprint("edge", __name__)
edge_api = Api(edge_bp, prefix="/edge")
edge_api.add_resource(EdgeCreateAPI, "/create")
edge_api.add_resource(EdgeListGetAPI, "/list/get")
edge_api.add_resource(EdgeDeleteAPI, "/delete")

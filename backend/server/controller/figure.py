from flask import Blueprint, request
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from constants.authority import AuthorityCarrier
from service.figure import figure_service

class FigureCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(
            request,
            [
                "computation_id",
                "node_id",
                "figure_name",
                "suffix"
            ]
        )
        computation_id = request.args.get("computation_id")
        node_id = request.args.get("node_id")
        figure_name = request.args.get("figure_name")
        suffix = request.args.get("suffix")
        upload_info = figure_service.create_figure(computation_id, figure_name, suffix, node_id)
        return ResponseManager.new_success_response(upload_info)
    
class FigureListByComputationIdAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            [
                "computation_id"
            ]
        )
        computation_id = request.args.get("computation_id")
        figures = figure_service.list_figures_by_computation_id(computation_id)
        return ResponseManager.new_success_response(figures)

class FigureListByNodeIdAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            [
                "node_id"
            ]
        )
        node_id = request.args.get("node_id")
        figures = figure_service.list_figures_by_node_id(node_id)
        return ResponseManager.new_success_response(figures)

figure_bp = Blueprint('figure', __name__)
figure_api = Api(figure_bp, prefix="/figure")
figure_api.add_resource(FigureCreateAPI, "/create")
figure_api.add_resource(FigureListByComputationIdAPI, "/list")
figure_api.add_resource(FigureListByNodeIdAPI, "/list-by-node-id")
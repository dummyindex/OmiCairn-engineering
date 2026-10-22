from flask import Blueprint, request
from flask_restful import Api, Resource
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from service.computation import computation_service
from service.visualizer import visualizer_service
from service.task import task_service
from log.logger_factory import LoggerFactory
from constants.authority import AuthorityCarrier
from constants.common import GenerationMode
from tool.computation_launcher import ComputationLauncher
from authority.guardian_factory import AuthorityGuardianFactory
from db import alchemy_db as db

logger = LoggerFactory.get_logger("VisualizerController")


class VisualizerCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "original_node_id",
            "max_count",
            "user_request",
            "computation_resource_configure"
        ])
        post_data = request.get_json()
        original_node_id = post_data.get("original_node_id")
        max_count = post_data.get("max_count")
        user_request = post_data.get("user_request")
        computation_resource_configure = post_data.get(
            "computation_resource_configure")
        llm_model = post_data.get("llm_model", None)
        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.NODE.value)
        guardian.check_authority(original_node_id, check_writable=True)
        user_id = guardian.get_user_id()
        visualizer = visualizer_service.create(
            original_node_id,
            max_count,
            user_request,
            computation_resource_configure,
            GenerationMode.ONLY_NEW.value,
            user_id,
            llm_model
        )
        return ResponseManager.new_success_response(data=visualizer.to_dict())


class VisualizerLaunchAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "visualizer_id"
        ])
        visualizer_id = request.args.get("visualizer_id")
        visualizer = visualizer_service.get(
            visualizer_id)
        if visualizer is None:
            return ResponseManager.new_bad_request_response(
                "visualizer not found")
        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.NODE.value)
        guardian.check_authority(visualizer.original_node_id, check_writable=True)
        user_id = guardian.get_user_id()
        ComputationLauncher.launch_visualizer(
            visualizer,
            user_id
        )
        return ResponseManager.new_success_response(data=True)


class VisualizerListByAnalysisAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "analysis_id"
        ])
        analysis_id = request.args.get("analysis_id")
        result = visualizer_service.list_by_analysis_id(analysis_id)
        return ResponseManager.new_success_response(data=result)


class VisualizerStepDoneReportAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "visualizer_id",
            "node_id",
            "satisfied",
        ])
        visualizer_id = request.args.get("visualizer_id")
        node_id = request.args.get("node_id")
        satisfied = request.args.get("satisfied", "0") == "1"
        visualizer_service.report_step_done(
            visualizer_id, node_id, satisfied)
        return ResponseManager.new_success_response()


class VisualizerEditAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "visualizer_id"
        ])
        visualizer_id = request.args.get("visualizer_id")
        attrs = request.get_json()
        visualizer_service.edit(visualizer_id, attrs)
        return ResponseManager.new_success_response()
    
class VisualizerAgentLaunchAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "node_id",
            "model",
            "demand",
            "figure_counts"
        ])
        node_id = request.json.get("node_id")
        model = request.json.get("model")
        demand = request.json.get("demand")
        figure_counts = request.json.get("figure_counts")
        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id, check_writable=True)
        user_id = guardian.get_user_id()
        task_service.invoke_visualizer_agent(
            node_id=node_id,
            model=model,
            optional_figure_counts=figure_counts,
            visualizer_demand=demand,
            user_id=user_id
        )
        return ResponseManager.new_success_response()


visualizer_bp = Blueprint("visualizer", __name__)
visualizer_api = Api(visualizer_bp, "/visualizer")
visualizer_api.add_resource(VisualizerCreateAPI, "/create")
visualizer_api.add_resource(VisualizerLaunchAPI, "/launch")
visualizer_api.add_resource(
    VisualizerListByAnalysisAPI, "/list-by-analysis")
visualizer_api.add_resource(
    VisualizerStepDoneReportAPI, "/report-step-done")
visualizer_api.add_resource(VisualizerEditAPI, "/edit")

# New Visualizer Implementation
visualizer_api.add_resource(VisualizerAgentLaunchAPI, "/launch-agent")
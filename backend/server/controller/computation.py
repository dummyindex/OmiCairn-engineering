from flask import Blueprint, request
from flask_restful import Api, Resource
from exception.request.parameter_invalid import ParameterInvalidException
from service.computation import computation_service
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from authority.guardian_factory import AuthorityGuardianFactory
from constants.authority import AuthorityCarrier

class LatestByNodeGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        request_auditor.request_args_check(request, ["node_id"])
        node_id = request.args.get("node_id", None)
        guardian.check_authority(node_id)
        result = computation_service.get_latest_by_node(node_id)
        return ResponseManager.new_success_response(data=result)
    
class ListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["mode"])
        mode = request.args.get("mode", None)
        if mode == "node":
            guardian = AuthorityGuardianFactory.get_authority_guardian(
                AuthorityCarrier.NODE.value)
            request_auditor.request_args_check(request, ["node_id"])
            node_id = request.args.get("node_id", None)
            guardian.check_authority(node_id)
            result = computation_service.get_list_by_node(node_id)
            return ResponseManager.new_success_response(data=result)
        elif mode == "task":
            request_auditor.request_args_check(request, ["task_id"])
            task_id = request.args.get("task_id", None)
            result = computation_service.get_list_by_task(task_id)
            return ResponseManager.new_success_response(data=result)
        elif mode == "analysis":
            request_auditor.request_args_check(request, ["analysis_id", "limit", "offset"])
            analysis_id = request.args.get("analysis_id", None)
            show_node = request.args.get("show_node", None)
            show_node = True if show_node == "1" else False
            show_user = request.args.get("show_user", None)
            show_user = True if show_user == "1" else False
            show_data = request.args.get("show_data", None)
            show_data = True if show_data == "1" else False
            limit = request.args.get("limit", 10)
            offset = request.args.get("offset", 0)
            result = computation_service.get_list_by_analysis_id(analysis_id, show_node, show_user, show_data, limit, offset)
            return ResponseManager.new_success_response(data=result)
        return ResponseManager.new_bad_request_response("mode is invalid")

class OptimizedErrorDescriptionRefreshAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        request_auditor.request_args_check(request, ["computation_id"])
        computation_id = request.args.get("computation_id", None)
        result = computation_service.refresh_optimized_error_description(computation_id, user_id)
        return ResponseManager.new_success_response(data=result)
    
class FigureListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["computation_id"])
        computation_id = request.args.get("computation_id", None)
        result = computation_service.get_figure_list_by_computation(computation_id)
        return ResponseManager.new_success_response(data=result)

class ComputationStepsGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["node_id"])
        node_id = request.args.get("node_id")
        node_id = int(node_id)
        result = computation_service.get_former_computation_steps(node_id)
        return ResponseManager.new_success_response(data=result)

class ComputationHistoryGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["node_id"])
        node_id = request.args.get("node_id")
        node_id = int(node_id)
        result = computation_service.get_former_computation_history(node_id)
        return ResponseManager.new_success_response(data=result)
    
class ComputationDetailsGetAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_json_check(request, ["node_ids"])
        post_data = request.get_json()
        node_id_list = post_data["node_ids"]
        node_id_list = [int(node_id) for node_id in node_id_list]
        result = computation_service.get_computation_details_by_node_id_list(node_id_list)
        return ResponseManager.new_success_response(data=result)
    
class ComputationReportGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["computation_id"]
        )
        computation_id = request.args.get("computation_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.COMPUTATUION.value)
        guardian.check_authority(computation_id)
        report = computation_service.get_computation_report_presigned_url(computation_id)
        return ResponseManager.new_success_response(data=report)
    
class ComputationRetryProcessListAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["analysis_id"])
        analysis_id = request.args.get("analysis_id")
        result = computation_service.get_retry_process_list_by_analysis_id(analysis_id)
        return ResponseManager.new_success_response(data=result)
    
class ComputationRetryProcessDetailsGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["retry_process_id"])
        retry_process_id = request.args.get("retry_process_id")
        result = computation_service.get_retry_process_details(retry_process_id)
        return ResponseManager.new_success_response(data=result)

computation_bp = Blueprint("computation", __name__)
computation_api = Api(computation_bp, prefix="/computation")
computation_api.add_resource(LatestByNodeGetAPI, "/latest-by-node/get")
computation_api.add_resource(ListGetAPI, "/list")
computation_api.add_resource(OptimizedErrorDescriptionRefreshAPI, "/optimized-error-description/refresh")
computation_api.add_resource(FigureListGetAPI, "/figure-list/get")
computation_api.add_resource(ComputationStepsGetAPI, "/get-former-steps")
computation_api.add_resource(ComputationHistoryGetAPI, "/get-former-history")
computation_api.add_resource(ComputationDetailsGetAPI, "/get-details-by-nodes")
computation_api.add_resource(ComputationReportGetAPI, "/get-report")
computation_api.add_resource(ComputationRetryProcessListAPI, "/list-retry-process")
computation_api.add_resource(ComputationRetryProcessDetailsGetAPI, "/get-retry-process-details")

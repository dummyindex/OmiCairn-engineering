from flask import Blueprint, request
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from constants.analysis import SpecialAnalysis
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from service.task import task_service
from log.logger_factory import LoggerFactory
from constants.authority import AuthorityCarrier
from service.dynamic_generation import dynamic_generation_service
logger = LoggerFactory.get_logger("TaskController")


class TaskPreviousCheckAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_json_check(request, ["node_id_list"])
        post_data = request.get_json()
        node_id_list = post_data.get("node_id_list")
        result = task_service.check_params(node_id_list)
        return ResponseManager.new_success_response(result)


class TaskDispatchAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(
            request, ['analysis_id', 'node_id_list', 'edge_id_list'])
        post_data = request.get_json()
        analysis_id = post_data.get('analysis_id')
        node_id_list = post_data.get('node_id_list')
        edge_id_list = post_data.get('edge_id_list')
        node_id_list = [int(node_id) for node_id in node_id_list]
        edge_id_list = [int(edge_id) for edge_id in edge_id_list]
        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.ANALYSIS.value)
        if int(analysis_id) != SpecialAnalysis.MINI_TOOL.value:
            guardian.check_authority(analysis_id, True)
        user_id = guardian.get_user_id()
        task = task_service.create(
            analysis_id,
            node_id_list,
            edge_id_list,
            user_id
        )
        return ResponseManager.new_success_response(task)


class TaskExtendAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(
            request, ['node_id_list', 'edge_id_list'])
        post_data = request.get_json()
        node_id_list = post_data.get('node_id_list')
        edge_id_list = post_data.get('edge_id_list')
        node_id_list = [int(node_id) for node_id in node_id_list]
        edge_id_list = [int(edge_id) for edge_id in edge_id_list]
        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.ANALYSIS.value)
        user_id = guardian.get_user_id()
        if user_id is None:
            raise Exception("User id is None")
        task = task_service.extend(
            node_id_list,
            edge_id_list,
        )
        return ResponseManager.new_success_response(task)


class TaskCancelAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["task_id"])
        task_id = request.args.get("task_id")
        
        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.TASK.value)
        guardian.check_authority(task_id, check_writable=True)
        task_service.cancel(task_id)
        return ResponseManager.new_success_response()


class CancelTaskByAnalysis(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["analysis_id"])
        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.ANALYSIS.value)
        analysis_id = request.args.get("analysis_id")
        guardian.check_authority(analysis_id, True)
        task_service.cancel_by_analysis(analysis_id)
        running_branches = dynamic_generation_service.list_running_branches_by_analysis_id(
            analysis_id)
        for branch in running_branches:
            dynamic_generation_service.handle_branch_done(branch.id)
        task_service.force_unlock_nodes_by_analysis_id(analysis_id)
        return ResponseManager.new_success_response()


class ReportRunningState(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["computation_id"])
        computation_id = request.args.get("computation_id")
        task_service.handle_running_report(computation_id)
        return ResponseManager.new_success_response()


class ReportFinishedState(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(request, ["computation_id"])
        computation_id = request.args.get("computation_id")
        post_data = request.get_json()
        job_review_passed = post_data.get("job_review_passed", True)
        review_error = post_data.get("review_error", None)
        logs = post_data.get("logs")
        logger.info(f"Finished report received for computation {computation_id}")
        task_service.handle_finished_report(computation_id, logs, job_review_passed, review_error)
        return ResponseManager.new_success_response()


class ReportFailedState(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        post_data = request.get_json()
        computation_id = request.args.get("computation_id")
        request_auditor.request_json_check(
            request, ["error_description", "logs"])
        post_data = request.get_json()
        error_description = post_data.get("error_description")
        logs = post_data.get("logs")
        task_service.handle_failed_report(
            computation_id, error_description, logs)
        return ResponseManager.new_success_response()


class TaskBranchCancelAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        request_auditor.request_args_check(request, ["terminated_node_id"])
        terminated_node_id = request.args.get("terminated_node_id")
        task_service.cancel_branch(terminated_node_id)
        dynamic_generation_branch_list = dynamic_generation_service.get_generation_branch_by_end_node_id(
            terminated_node_id)
        for dynamic_generation_branch in dynamic_generation_branch_list:
            if dynamic_generation_branch.state == "running":
                dynamic_generation_service.handle_branch_done(
                    dynamic_generation_branch.id)
        return ResponseManager.new_success_response()


task_bp = Blueprint('task', __name__)
task_api = Api(task_bp, prefix='/task')
task_api.add_resource(TaskPreviousCheckAPI, '/previous-check')
task_api.add_resource(TaskDispatchAPI, '/dispatch')
task_api.add_resource(TaskExtendAPI, '/extend')
task_api.add_resource(TaskCancelAPI, '/cancel')
task_api.add_resource(CancelTaskByAnalysis, "/cancel-by-analysis")
task_api.add_resource(ReportRunningState, "/be-runned-report")
task_api.add_resource(ReportFinishedState, "/finished-report")
task_api.add_resource(ReportFailedState, "/failed-report")
task_api.add_resource(TaskBranchCancelAPI, "/cancel-branch")

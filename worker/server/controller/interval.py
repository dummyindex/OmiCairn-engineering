from flask import Blueprint, request
from flask_restful import Api, Resource
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from service.computation import computation_service
from service.task import task_service
from service.dynamic_generation import dynamic_generation_service
from log.logger_factory import LoggerFactory
from constants.authority import AuthorityCarrier

logger = LoggerFactory.get_logger("IntervalController")


class InitAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        # Cancel all running tasks
        task_service.cancel_all_running()
        # Cancel all running dynamic generations
        dynamic_generation_service.stop_all()
        # Cancel all running retry processes
        computation_service.stop_all_retry_process()
        # Force-unlock all nodes to resolve lock anomalies after a restart
        task_service.force_unlock_all_nodes()
        logger.info("Server initialization completed - all tasks stopped and nodes unlocked")
        return ResponseManager.new_success_response()


class ScanTimeoutComputationAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        computation_service.scan_timeout_computations()
        return ResponseManager.new_success_response()


class ScanOmissiveComputationAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        computation_service.scan_omissive_computations()
        return ResponseManager.new_success_response()


class TaskUnlockAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        task_service.unlock_nodes_interval()
        return ResponseManager.new_success_response()

class RefreshFunctionBlockAverageDurationAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        computation_service.refresh_function_block_average_duration()
        return ResponseManager.new_success_response()

class ForceUnlockAllNodesAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """
        Emergency endpoint: force-unlock all nodes
        Used to resolve lock anomalies
        """
        logger.warning("Force unlock all nodes API called - this is an emergency operation")
        task_service.force_unlock_all_nodes()
        return ResponseManager.new_success_response({"message": "All nodes have been forcibly unlocked"})

interval_bp = Blueprint("interval", __name__)
interval_api = Api(interval_bp, "/interval")
interval_api.add_resource(InitAPI, "/init")
interval_api.add_resource(ScanTimeoutComputationAPI, "/scan-timeout")
interval_api.add_resource(ScanOmissiveComputationAPI, "/scan-omissive")
interval_api.add_resource(TaskUnlockAPI, "/unlock-nodes-interval")
interval_api.add_resource(RefreshFunctionBlockAverageDurationAPI, "/refresh-fb-avg-duration")
interval_api.add_resource(ForceUnlockAllNodesAPI, "/force-unlock-all-nodes")

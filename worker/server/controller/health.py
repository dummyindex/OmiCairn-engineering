from flask import Blueprint, request
from flask_restful import Api, Resource
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from service.computation import computation_service
from service.task import task_service
from log.logger_factory import LoggerFactory
from constants.authority import AuthorityCarrier

logger = LoggerFactory.get_logger("HealthController")


class AvailabilityCheckAPI(Resource):
    @exception_wrapper
    def get(self):
        return ResponseManager.new_success_response()


health_bp = Blueprint("health", __name__)
health_api = Api(health_bp, "/health")
health_api.add_resource(AvailabilityCheckAPI, "/check")

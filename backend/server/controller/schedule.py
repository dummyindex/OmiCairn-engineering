from flask_restful import Resource, Api
from flask import (
    request,
    Blueprint
)
from service.schedule import schedule_service
from tool.response_manager import ResponseManager
from wrapper.exception import exception_wrapper
from wrapper.db_session import transaction_wrapper
from tool.requests_auditor import request_auditor

class BuriedDataClearByComputationAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        handled_count = schedule_service.clear_buried_data_by_computation()
        return ResponseManager.new_success_response(data={
            "handledCount": handled_count
        })
    
class BurriedDataClearAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        handled_count = schedule_service.clear_buried_data()
        return ResponseManager.new_success_response(data={
            "handledCount": handled_count
        })

class UploadingTimeoutScanAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        handled_count = schedule_service.scan_uploading_timeout()
        return ResponseManager.new_success_response(data={
            "handledCount": handled_count
        })

schedule_bp = Blueprint("schedule", __name__)
schedule_api = Api(schedule_bp, prefix="/schedule")
schedule_api.add_resource(BuriedDataClearByComputationAPI, "/clear-buried-data-by-computation")
schedule_api.add_resource(BurriedDataClearAPI, "/clear-buried-data")
schedule_api.add_resource(UploadingTimeoutScanAPI, "/scan-uploading-timeout")
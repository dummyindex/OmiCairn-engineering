from flask import Blueprint, request
from flask_restful import Api, Resource
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from service.burial_point import burial_point_service
from authority.guardian_factory import AuthorityGuardianFactory
from constants.authority import AuthorityCarrier
from datetime import datetime

class RecordOpenApAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["analysis_id"]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        analysis_id = request.args.get("analysis_id")
        open_time = datetime.now()
        open_ap_record = burial_point_service.record_open_ap(user_id, analysis_id, open_time)
        return ResponseManager.new_success_response(data=open_ap_record)
    
burial_point_bp = Blueprint("burial-point", __name__)
burial_point_api = Api(burial_point_bp, prefix="/burial-point")
burial_point_api.add_resource(RecordOpenApAPI, "/record-open-ap")
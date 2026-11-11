from flask import Blueprint, request
from flask_restful import Api, Resource
from exception.request.parameter_invalid import ParameterInvalidException
from service.computation import computation_service
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from authority.guardian_factory import AuthorityGuardianFactory
from constants.authority import AuthorityCarrier
from service.consumption import consumption_service
from datetime import datetime

class FileSizeTotalGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        s3_file_size_details = consumption_service.get_s3_file_size_total_by_user(user_id)
        return ResponseManager.new_success_response(s3_file_size_details)

class TotalLLMConsumptionGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        llm_consumptions = consumption_service.get_llm_consumptions_total_by_user(user_id)
        return ResponseManager.new_success_response(llm_consumptions)

class TotalComputationConsumptionGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        computation_consumptions = consumption_service.get_computation_consumptions_total_by_user(user_id)
        return ResponseManager.new_success_response(computation_consumptions)

class FileSizeDetailsGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        month = request.args.get("month", None)
        if month is None:
            month = datetime.now().strftime("%Y-%m")
        s3_file_size_details = consumption_service.get_s3_file_size_details_by_user(user_id, month)
        return ResponseManager.new_success_response(s3_file_size_details)

class DetailsLLMConsumptionGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        month = request.args.get("month")
        if month is None:
            month = datetime.now().strftime("%Y-%m")
        llm_consumptions = consumption_service.get_llm_consumptions_details_by_user(user_id, month)
        return ResponseManager.new_success_response(llm_consumptions)
    
class TotalComputationConsumptionsGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        computation_consumptions = consumption_service.get_computation_consumptions_total_by_user(user_id)
        return ResponseManager.new_success_response(computation_consumptions)

class DetailsComputationConsumptionsGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        month = request.args.get("month")
        if month is None:
            month = datetime.now().strftime("%Y-%m")
        computation_consumptions = consumption_service.get_computation_consumptions_details_by_user(user_id, month)
        return ResponseManager.new_success_response(computation_consumptions)

consumption_bp = Blueprint("consumption", __name__)
consumption_api = Api(consumption_bp, prefix="/consumption")
consumption_api.add_resource(FileSizeTotalGetAPI, "/get-s3-file-size-total")
consumption_api.add_resource(TotalLLMConsumptionGetAPI, "/get-llm-consumptions-total")
consumption_api.add_resource(FileSizeDetailsGetAPI, "/get-s3-file-size-details")
consumption_api.add_resource(DetailsLLMConsumptionGetAPI, "/get-llm-consumptions-details")
consumption_api.add_resource(TotalComputationConsumptionGetAPI, "/get-computation-consumptions-total")
consumption_api.add_resource(DetailsComputationConsumptionsGetAPI, "/get-computation-consumptions-details")
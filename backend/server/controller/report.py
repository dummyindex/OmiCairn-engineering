from flask import Blueprint, request
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from service.report import report_service
from wrapper.db_session import transaction_wrapper
from wrapper.exception import exception_wrapper

# Only the create API is currently used
class ReportCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        AuthorityGuardianFactory.get_authority_guardian()
        post_data = request.get_json()
        node_id = post_data.get("node_id")
        summary = post_data.get("summary")
        detail = post_data.get("detail")
        report = report_service.create_report(node_id, summary, detail)
        return ResponseManager.new_success_response(data=report.to_dict())

class ReportInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        AuthorityGuardianFactory.get_authority_guardian()
        request_auditor.request_args_check(request, ["node_id", "report_id"])
        node_id = request.args.get("node_id")
        report_id = request.args.get("report_id")
        result = report_service.get_report_info(
            node_id,
            report_id
        )
        return ResponseManager.new_success_response(data=result)

class ReportListByNodeAPI(Resource):
    @exception_wrapper
    def get(self):
        AuthorityGuardianFactory.get_authority_guardian()
        node_id = request.args.get("node_id")
        result = report_service.get_report_info_by_node_id(node_id)
        return ResponseManager.new_success_response(data=result)

class ReportEditAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        AuthorityGuardianFactory.get_authority_guardian().require_user_id()
        request_auditor.request_json_check(request, ["node_id", "report_id", "summary", "detail"])
        post_data = request.get_json()
        node_id = post_data.get("node_id")
        report_id = post_data.get("report_id")
        summary = post_data.get("summary")
        detail = post_data.get("detail")
        report = report_service.update_report(node_id, report_id, summary, detail)
        return ResponseManager.new_success_response(data=report.to_dict() if report else None)

class ReportDeleteAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def delete(self):
        AuthorityGuardianFactory.get_authority_guardian().require_user_id()
        request_auditor.request_args_check(request, ["node_id", "report_id"])
        node_id = request.args.get("node_id")
        report_id = request.args.get("report_id")
        report_service.delete_report(node_id, report_id)
        return ResponseManager.new_success_response()

report_bp = Blueprint("report", __name__)
report_api = Api(report_bp, prefix="/report")
report_api.add_resource(ReportCreateAPI, "/create")
report_api.add_resource(ReportInfoGetAPI, "/get")
report_api.add_resource(ReportListByNodeAPI, "/list/by_node")
report_api.add_resource(ReportEditAPI, "/edit")
report_api.add_resource(ReportDeleteAPI, "/delete")

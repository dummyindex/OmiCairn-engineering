from flask import Blueprint, request
from flask_restful import Api, Resource
from service.workflow_report import workflow_report_service
from tool.response_manager import ResponseManager
from wrapper.db_session import transaction_wrapper
from wrapper.exception import exception_wrapper
from authority.guardian_factory import AuthorityGuardianFactory
from tool.requests_auditor import request_auditor
from constants.authority import AuthorityCarrier
from exception.authority.no_authority import NoAuthorityException


def _check_report_owner(uuid, user_id):
    report = workflow_report_service.get_report_by_uuid(uuid)
    if report is None or str(report.user_id) != str(user_id):
        raise NoAuthorityException("You do not own this workflow report.")

class WorkflowReportCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        user_id = guardian.get_user_id()
        post_data = request.get_json()
        if "user_id" not in post_data:
            post_data["user_id"] = user_id
        elif post_data["user_id"] != user_id:
            return ResponseManager.new_unauthorized_response()
        analysis_id = post_data.get("analysis_id")
        if analysis_id:
            guardian.check_authority(analysis_id, check_writable=True)
        report = workflow_report_service.create_report(post_data)
        return ResponseManager.new_success_response(data=report)

class WorkflowReportInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        uuid = request.args.get("uuid")
        report = workflow_report_service.get_report_by_uuid(uuid)
        if report is None:
            return ResponseManager.new_bad_request_response("uuid not found")
        if report.user_id != user_id:
            return ResponseManager.new_unauthorized_response()
        return ResponseManager.new_success_response(data=report)

class WorkflowReportPresignedUrlGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        uuid = request.args.get("uuid")
        file_name = request.args.get("file_name")
        presigned_url = workflow_report_service.get_presigned_url_by_uuid(uuid, file_name, user_id)
        return ResponseManager.new_success_response(presigned_url)
    

class WorkflowReportPresignedPostGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        uuid = request.args.get("uuid")
        file_name = request.args.get("file_name")
        file_size = request.args.get("file_size")
        file_size = int(file_size)
        presigned_post = workflow_report_service.get_presigned_post_by_uuid(file_size, uuid, file_name, user_id)
        return ResponseManager.new_success_response(presigned_post)

class WorkflowReportListByUserAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        reports = workflow_report_service.get_reports_by_user_id(user_id)
        return ResponseManager.new_success_response(data=reports)

class WorkflowReportMetadataEditAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(request, ["uuid"])
        uuid = request.args.get("uuid")
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        _check_report_owner(uuid, guardian.get_user_id())
        post_data = request.get_json()
        for unchangable_key in ["id","uuid", "user_id", "created_time", "updated_time"]:
            if unchangable_key in post_data:
                del post_data[unchangable_key]
        report = workflow_report_service.update_report(uuid, post_data)
        return ResponseManager.new_success_response(data=report)

class WorkflowReportDeleteAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def delete(self):
        request_auditor.request_args_check(request, ["uuid"])
        uuid = request.args.get("uuid")
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        _check_report_owner(uuid, guardian.get_user_id())
        workflow_report_service.delete_report_by_uuid(uuid)
        return ResponseManager.new_success_response()

class WorkflowReportListByAnalysisAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["analysis_id"])
        analysis_id = request.args.get("analysis_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_authority(analysis_id)
        reports = workflow_report_service.get_reports_by_analysis_id(analysis_id)
        return ResponseManager.new_success_response(data=reports)

workflow_report_bp = Blueprint("workflow_report", __name__)
workflow_report_api = Api(workflow_report_bp, prefix="/workflow-report")

workflow_report_api.add_resource(WorkflowReportCreateAPI, "/create")
workflow_report_api.add_resource(WorkflowReportInfoGetAPI, "/get-info")
workflow_report_api.add_resource(WorkflowReportPresignedUrlGetAPI, "/get-presigned-url")
workflow_report_api.add_resource(WorkflowReportPresignedPostGetAPI, "/get-presigned-post")
workflow_report_api.add_resource(WorkflowReportListByUserAPI, "/list-by-user")
workflow_report_api.add_resource(WorkflowReportMetadataEditAPI, "/edit-info")
workflow_report_api.add_resource(WorkflowReportDeleteAPI, "/delete")
workflow_report_api.add_resource(WorkflowReportListByAnalysisAPI, "/list-by-analysis")
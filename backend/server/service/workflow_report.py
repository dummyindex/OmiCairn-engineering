from dao.workflow_report import workflow_report_dao
from sss.porter_factory import PorterFactory
from constants.sss import BUCKET_NAME
from exception.request.parameter_invalid import ParameterInvalidException

class WorkflowReportService:

    def create_report(self, data):
        report = workflow_report_dao.insert_report(data)
        return report

    def get_report_by_uuid(self, uuid):
        return workflow_report_dao.find_report_by_uuid(uuid)
    
    def get_all_reports(self):
        return workflow_report_dao.find_all()

    def update_report(self, uuid, data):
        current_report = workflow_report_dao.find_report_by_uuid(uuid)
        if "report_name" in data:
            porter = PorterFactory.create_porter()
            new_object_key = f"workflow-report/{uuid}/{data['report_name']}.txt"
            porter.set_operation_target(new_object_key)
            object_key = f"workflow-report/{uuid}/{current_report.report_name}.txt"
            porter.copy_file(BUCKET_NAME, object_key)
            porter.set_operation_target(object_key)
            porter.remove_file()
        return workflow_report_dao.update_report(uuid, data)

    def delete_report_by_uuid(self, uuid):
        workflow_report_dao.delete_report_by_uuid(uuid)

    def get_presigned_url_by_uuid(self, uuid: str, file_name: str, user_id: int):
        workflow_report = workflow_report_dao.find_report_by_uuid(uuid)
        if not workflow_report or workflow_report.user_id != user_id:
            raise ParameterInvalidException("uuid not found")
        porter = PorterFactory.create_porter()
        object_key = f"workflow-report/{uuid}/{file_name}"
        porter.set_operation_target(object_key)
        content_url = porter.get_presigned_url(60 * 3)
        return content_url
    
    def get_presigned_post_by_uuid(self, file_size: int, uuid: str, file_name: str, user_id: int):
        workflow_report = workflow_report_dao.find_report_by_uuid(uuid)
        if not workflow_report:
            raise ParameterInvalidException("uuid not found")
        if workflow_report.user_id != user_id:
            raise ParameterInvalidException("unauthorized")
        porter = PorterFactory.create_porter()
        object_key = f"workflow-report/{uuid}/{file_name}"
        porter.set_operation_target(object_key)
        presigned_info = porter.get_presigned_post(file_size, 60)
        return presigned_info
    
    def get_reports_by_analysis_id(self, analysis_id):
        return workflow_report_dao.find_reports_by_analysis_id(analysis_id)
    
    def get_reports_by_user_id(self, user_id):
        return workflow_report_dao.find_reports_by_user_id(user_id)

workflow_report_service = WorkflowReportService()


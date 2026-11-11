from model.workflow_report import WorkflowReport
from db import alchemy_db as db
from typing import List

class WorkflowReportDao:

    def insert_report(self, data) -> WorkflowReport:
        report = WorkflowReport(**data)
        db.session.add(report)
        return report

    def find_report_by_uuid(self, uuid) -> WorkflowReport:
        return WorkflowReport.query.filter_by(uuid=uuid).first()

    def update_report(self, uuid, data) -> WorkflowReport:
        report = WorkflowReport.query.filter_by(uuid=uuid).first()
        if not report:
            return None
        for key, value in data.items():
            setattr(report, key, value)
        return report

    def delete_report_by_uuid(self, uuid) -> None:
        WorkflowReport.query.filter_by(uuid=uuid).delete()

    def find_reports_by_analysis_id(self, analysis_id) -> List[WorkflowReport]:
        return WorkflowReport.query.filter_by(
            analysis_id=analysis_id
        ).order_by(WorkflowReport.created_time.desc()).all()
    
    def find_reports_by_user_id(self, user_id) -> List[WorkflowReport]:
        return WorkflowReport.query.filter_by(user_id=user_id).all()
        
    def find_all(self) -> List[WorkflowReport]:
        return WorkflowReport.query.all()

workflow_report_dao = WorkflowReportDao()

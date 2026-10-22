from db import alchemy_db as db
from model.report import Report
# from sqlalchemy import and_

class ReportDao:
    def insert(self, report: Report):
        db.session.add(report)
        db.session.flush()
        return report
    
    def find_max_report_id_by_node_id(self, node_id):
        max_report_id = db.session.query(
            db.func.max(Report.report_id)
        ).filter_by(node_id=node_id).scalar()
        return max_report_id if max_report_id else 0
     
    def find_by_node_and_report_id(self, node_id, report_id):
        return Report.query.filter((Report.node_id == node_id) & (Report.report_id == report_id)).first()
    
    def find_by_node_id(self, node_id):
        return Report.query.filter(Report.node_id == node_id).all()
    
    def find_by_fb_id(self, fb_id):
        return Report.query.filter(Report.fb_id == fb_id).all()
    
    def update(self, node_id, report_id, attrs_dict):
        Report.query.filter((Report.node_id == node_id) & (Report.report_id == report_id)).update(attrs_dict)
        db.session.flush()

    def delete_by_node_and_report_id(self, node_id, report_id):
        Report.query.filter((Report.node_id == node_id) & (Report.report_id == report_id)).delete()

    def delete_by_node_id(self, node_id):
        Report.query.filter(Report.node_id == node_id).delete()
    
    def delete_by_fd_id(self, fb_id):
        Report.query.filter(Report.fb_id == fb_id).delete()
    
    # Additional methods can be added as needed

report_dao = ReportDao()
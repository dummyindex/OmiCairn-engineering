from db import alchemy_db as db

class WorkflowReport(db.Model):
    __tablename__ = 'workflow_report'

    report_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), nullable=False, unique=True)
    report_name = db.Column(db.String(255), nullable=True)
    created_time = db.Column(db.DateTime, nullable=False)
    updated_time = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.BigInteger, nullable=False, index=True)
    analysis_id = db.Column(db.BigInteger, nullable=False, index=True)
    node_id_list = db.Column(db.Text, nullable=True)
    figure_list = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            "reportId": self.report_id,
            "uuid": self.uuid,
            "reportName": self.report_name,
            "createdTime": self.created_time.timestamp() * 1000,
            "updatedTime": self.updated_time.timestamp() * 1000,
            "userId": self.user_id,
            "analysisId": self.analysis_id,
            "nodeIdList": self.node_id_list,
            "figureList": self.figure_list,
            "url": self.url,
            "status": self.status
        }
from db import alchemy_db as db

class Report(db.Model):
    __tablename__ = 'report'
    node_id = db.Column(db.BigInteger, primary_key=True,
                    nullable=False, comment='Node ID')
    report_id = db.Column(db.BigInteger, primary_key=True,
                    nullable=False, comment='Report ID')
    fb_id = db.Column(db.BigInteger, comment='Feedback ID')
    summary = db.Column(db.String(255), comment='Summary')
    detail = db.Column(db.Text, comment='Detail')
    error_log = db.Column(db.Text, comment='Error Log')
    optimized_error = db.Column(db.Text, default=None, comment='Optimized Error')

    def to_dict(self):
        report_attrs_dict = dict()
        report_attrs_dict["nodeId"] = self.node_id
        report_attrs_dict["reportId"] = self.report_id
        report_attrs_dict["fbId"] = self.fb_id
        report_attrs_dict["summary"] = self.summary
        report_attrs_dict["detail"] = self.detail
        report_attrs_dict["errorLog"] = self.error_log
        report_attrs_dict["optimizedError"] = self.optimized_error
        return report_attrs_dict

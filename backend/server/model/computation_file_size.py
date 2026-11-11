from db import alchemy_db as db
from datetime import datetime


class ComputationFileSize(db.Model):
    __tablename__ = "computation_file_size"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    computation_id = db.Column(db.BigInteger)
    log_size = db.Column(db.BigInteger)
    options_size = db.Column(db.BigInteger)
    output_size = db.Column(db.BigInteger)
    review_error_size = db.Column(db.BigInteger)
    result_size = db.Column(db.BigInteger)
    report_size = db.Column(db.BigInteger)
    figures_size = db.Column(db.BigInteger)
    created_time = db.Column(db.DateTime)
    def to_dict(self):
        return {
            "id": self.id,
            "computationId": self.computation_id,
            "logSize": self.log_size,
            "optionsSize": self.options_size,
            "outputSize": self.output_size,
            "reviewErrorSize": self.review_error_size,
            "resultSize": self.result_size,
            "reportSize": self.report_size,
            "figuresSize": self.figures_size,
            "createdTime": self.created_time.strftime("%Y-%m-%d %H:%M:%S") if self.created_time else None
        }

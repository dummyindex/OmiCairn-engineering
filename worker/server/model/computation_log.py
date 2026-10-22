from db import alchemy_db as db


class ComputationLog(db.Model):
    __tablename__ = 'computation_log'
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='Primary Key')
    computation_id = db.Column(
        db.BigInteger, nullable=False, comment='Computation ID')
    log = db.Column(db.Text, nullable=False, comment='Log')
    created_time = db.Column(db.DateTime, nullable=False,
                             server_default=db.func.current_timestamp(), comment='Created Time')

    def to_dict(self):
        computation_log_attrs_dict = dict()
        computation_log_attrs_dict["id"] = self.id
        computation_log_attrs_dict["computationId"] = self.computation_id
        computation_log_attrs_dict["log"] = self.log
        computation_log_attrs_dict["createdTime"] = self.created_time
        return computation_log_attrs_dict

from db import alchemy_db as db

class OpenApRecord(db.Model):
    __tablename__ = 'open_ap_record'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='ID')
    user_id = db.Column(db.BigInteger, nullable=False)
    analysis_id = db.Column(db.BigInteger, nullable=False)
    open_time = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        open_ap_record_attrs_dict = dict()
        open_ap_record_attrs_dict["id"] = self.id
        open_ap_record_attrs_dict["userId"] = self.user_id
        open_ap_record_attrs_dict["analysisId"] = self.analysis_id
        open_ap_record_attrs_dict["openTime"] = self.open_time.timestamp() * 1000
        return open_ap_record_attrs_dict
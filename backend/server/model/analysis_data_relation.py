from db import alchemy_db as db


class AnalysisDataRelation(db.Model):
    __tablename__ = "analysis_data_relation"

    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    analysis_id = db.Column(db.BigInteger)
    data_id = db.Column(db.BigInteger)
    created_time = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "analysisId": self.analysis_id,
            "dataId": self.data_id,
            "createdTime": self.created_time and self.created_time.timestamp() * 1000
        }

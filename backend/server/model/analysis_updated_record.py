from db import alchemy_db as db


class AnalysisUpdatedRecord(db.Model):
    __tablename__ = "analysis_updated_record"

    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    analysis_id = db.Column(db.BigInteger)
    updated_time = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "analysisId": self.analysis_id,
            "updatedTime": self.updated_time if self.updated_time else None
        }

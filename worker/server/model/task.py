from db import alchemy_db as db


class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    created_time = db.Column(db.DateTime)
    analysis_id = db.Column(db.BigInteger)
    state = db.Column(db.String(50))

    def to_dict(self):
        task_attrs_dict = dict()
        task_attrs_dict["id"] = self.id
        task_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000
        task_attrs_dict["analysisId"] = self.analysis_id
        task_attrs_dict["state"] = self.state
        return task_attrs_dict

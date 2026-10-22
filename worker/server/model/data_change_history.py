from db import alchemy_db as db


class DataChangeHistory(db.Model):
    __tablename__ = "data_change_history"
    id = db.Column(db.BigInteger, primary_key=True)
    data_id = db.Column(db.BigInteger, nullable=False)
    changed_field = db.Column(db.String(20), nullable=False)
    changed_key = db.Column(db.String(100), nullable=False)
    new_key = db.Column(db.String(100), nullable=True)
    file_saved_name = db.Column(db.String(100), nullable=False)
    change_method = db.Column(db.String(10), nullable=False)
    created_time = db.Column(db.DateTime, nullable=False)
    merged = db.Column(db.Boolean, nullable=False, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "dataId": self.data_id,
            "changedField": self.changed_field,
            "changedKey": self.changed_key,
            "newKey": self.new_key,
            "fileSavedName": self.file_saved_name,
            "createdTime": self.created_time and self.created_time.timestamp() * 1000,
            "changeMethod": self.change_method,
            "merged": self.merged
        }
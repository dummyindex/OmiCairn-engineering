from db import alchemy_db as db


class Data(db.Model):
    __tablename__ = "data"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_time = db.Column(db.DateTime, nullable=False)
    collected = db.Column(db.Boolean, nullable=False)
    upload_type = db.Column(db.String(255), nullable=False)
    species = db.Column(db.String(255), nullable=True)
    created_from = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    state = db.Column(db.String(30), nullable=False)
    error_message = db.Column(db.Text, nullable=True)
    buried = db.Column(db.Boolean, nullable=False)
    summary = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "createdTime": self.created_time and self.created_time.timestamp(
            ) * 1000,
            "collected": self.collected,
            "uploadType": self.upload_type,
            "species": self.species,
            "createdFrom": self.created_from,
            "description": self.description,
            "state": self.state,
            "errorMessage": self.error_message,
            "buried": self.buried,
            "summary": self.summary
        }

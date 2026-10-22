# CREATE TABLE dynamic_generation_session(
#     id BIGINT PRIMARY KEY AUTO_INCREMENT,
#     dynamic_generation_id BIGINT NOT NULL,
#     source_node_id BIGINT NOT NULL,
#     consumption_id BIGINT NOT NULL,
#     created_at DATETIME DEFAULT CURRENT_TIMESTAMP
# );

from datetime import datetime
from db import alchemy_db as db


class DynamicGenerationSession(db.Model):
    __tablename__ = "dynamic_generation_session"
    id = db.Column(db.Integer, primary_key=True)
    dynamic_generation_id = db.Column(db.Integer)
    source_node_id = db.Column(db.Integer)
    consumption_id = db.Column(db.Integer)
    is_valid = db.Column(db.Boolean, default=True)
    errors = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    type = db.Column(db.String(255), nullable=True)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "dynamicGenerationId": self.dynamic_generation_id,
            "sourceNodeId": self.source_node_id,
            "consumptionId": self.consumption_id,
            "isValid": self.is_valid,
            "errors": self.errors,
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "type": self.type,
            "startTime": self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else None,
            "endTime": self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None
        }

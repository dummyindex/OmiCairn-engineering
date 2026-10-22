# CREATE TABLE bug_fixer_session(
#     id BIGINT PRIMARY KEY AUTO_INCREMENT,
#     retry_process_id BIGINT NOT NULL,
#     node_id BIGINT NOT NULL,
#     fixed_computation_id BIGINT NOT NULL,
#     type VARCHAR(255) NOT NULL,
#     consumption_id BIGINT NOT NULL,
#     created_at DATETIME DEFAULT CURRENT_TIMESTAMP
# );

from datetime import datetime
from db import alchemy_db as db


class BugFixerSession(db.Model):
    __tablename__ = "bug_fixer_session"
    id = db.Column(db.Integer, primary_key=True)
    retry_process_id = db.Column(db.Integer)
    dynamic_generation_id = db.Column(db.Integer)
    node_id = db.Column(db.Integer)
    fixed_computation_id = db.Column(db.Integer)
    type = db.Column(db.String(255))
    consumption_id = db.Column(db.Integer)
    is_valid = db.Column(db.Boolean, default=True)
    errors = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "retryProcessId": self.retry_process_id,
            "dynamicGenerationId": self.dynamic_generation_id,
            "nodeId": self.node_id,
            "fixedComputationId": self.fixed_computation_id,
            "type": self.type,
            "consumptionId": self.consumption_id,
            "isValid": self.is_valid,
            "errors": self.errors,
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "startTime": self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else None,
            "endTime": self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None
        }

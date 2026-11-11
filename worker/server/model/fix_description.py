# CREATE TABLE fix_description(
#     id BIGINT PRIMARY KEY AUTO_INCREMENT,
#     computation_id BIGINT NOT NULL,
#     error_info TEXT NOT NULL,
#     fix_strategy TEXT NOT NULL,
#     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
#     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
#     INDEX idx_computation_id (computation_id)
# );

from datetime import datetime
from db import alchemy_db as db


class FixDescription(db.Model):
    __tablename__ = "fix_description"
    id = db.Column(db.Integer, primary_key=True)
    computation_id = db.Column(db.Integer, nullable=False)
    error_info = db.Column(db.Text, nullable=False)
    fix_strategy = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "computationId": self.computation_id,
            "errorInfo": self.error_info,
            "fixStrategy": self.fix_strategy,
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updatedAt": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }

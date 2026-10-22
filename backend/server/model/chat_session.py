from db import alchemy_db as db
from datetime import datetime


class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    analysis_id = db.Column(db.BigInteger, db.ForeignKey('analysis.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    message_count = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "analysisId": self.analysis_id,
            "title": self.title,
            "createdTime": int(self.created_time.timestamp() * 1000),
            "updatedTime": int(self.updated_time.timestamp() * 1000),
            "messageCount": self.message_count,
            "isActive": self.is_active
        }
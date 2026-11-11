from db import alchemy_db as db
from datetime import datetime


class Chat(db.Model):
    __tablename__ = 'chat'

    id = db.Column(db.Integer, primary_key=True, comment='Chat ID')
    name = db.Column(db.String(200), nullable=False, comment='Chat name')
    analysis_id = db.Column(db.Integer, nullable=False, comment='Analysis ID')
    current_node_id = db.Column(db.Integer, nullable=True, comment='Current node ID')
    model = db.Column(db.String(100), nullable=False, default='gpt-4o-mini', comment='LLM model')
    status = db.Column(db.String(20), nullable=False, default='normal', comment='Chat status')
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='Created time')
    updated_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Updated time')
    user_id = db.Column(db.Integer, nullable=True, comment='User ID who owns the chat')
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "analysisId": self.analysis_id,
            "currentNodeId": self.current_node_id,
            "model": self.model,
            "status": self.status,
            "createdTime": self.created_time.strftime("%Y-%m-%d %H:%M:%S") if self.created_time else None,
            "updatedTime": self.updated_time.strftime("%Y-%m-%d %H:%M:%S") if self.updated_time else None,
            "userId": self.user_id
        }
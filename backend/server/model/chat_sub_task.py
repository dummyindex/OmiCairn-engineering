from db import alchemy_db as db
from datetime import datetime


class ChatSubTask(db.Model):
    __tablename__ = 'chat_sub_task'

    id = db.Column(db.Integer, primary_key=True, comment='Sub task ID')
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False, comment='Chat ID')
    chat_message_id = db.Column(db.Integer, db.ForeignKey('chat_message.id'), nullable=False, comment='Message ID')
    tool_call_id = db.Column(db.String(255), nullable=True, comment='Associated tool call ID')
    tool_name = db.Column(db.String(255), nullable=False, comment='Tool name')
    tool_params = db.Column(db.Text, nullable=True, comment='Tool parameters JSON string')
    system_task_id = db.Column(db.Integer, nullable=True, comment='System task ID for async tasks')
    outputs = db.Column(db.Text, nullable=True, comment='Task output results')
    status = db.Column(db.String(128), nullable=False, default='running', comment='Task status (running, finished, failed)')
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='Created time')
    start_time = db.Column(db.DateTime, nullable=True, comment='Start time')
    end_time = db.Column(db.DateTime, nullable=True, comment='End time')

    # Relationships
    chat = db.relationship('Chat', backref=db.backref('sub_tasks', lazy=True))
    message = db.relationship('ChatMessage', backref=db.backref('sub_tasks', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "chatId": self.chat_id,
            "chatMessageId": self.chat_message_id,
            "toolCallId": self.tool_call_id,
            "toolName": self.tool_name,
            "toolParams": self.tool_params,
            "systemTaskId": self.system_task_id,
            "outputs": self.outputs,
            "status": self.status,
            "createdTime": self.created_time.strftime("%Y-%m-%d %H:%M:%S") if self.created_time else None,
            "startTime": self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else None,
            "endTime": self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None
        }
from db import alchemy_db as db
from datetime import datetime
import json


class ChatMessage(db.Model):
    __tablename__ = 'chat_message'

    id = db.Column(db.Integer, primary_key=True, comment='Message ID')
    role = db.Column(db.String(20), nullable=False, comment='Message role: user, assistant, tool')
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False, comment='Chat ID')
    tool_calls = db.Column(db.Text, nullable=True, comment='Tool calls JSON string')
    tool_call_id = db.Column(db.String(255), nullable=True, comment='Associated tool call ID')
    content = db.Column(db.Text, nullable=True, comment='Message content')
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='Created time')
    model = db.Column(db.String(100), nullable=True, comment='LLM model used')
    model_time = db.Column(db.Float, nullable=True, default=0, comment='Model response time in seconds')
    prompt_tokens = db.Column(db.Integer, nullable=True, default=0, comment='Prompt tokens count')
    completion_tokens = db.Column(db.Integer, nullable=True, default=0, comment='Completion tokens count')
    is_summary = db.Column(db.Boolean, nullable=False, default=False, comment='Is this message a summary')
    summary_message_id = db.Column(db.Integer, db.ForeignKey('chat_message.id'), nullable=True, comment='Summary message ID')
    attached_file_s3_keys = db.Column(db.Text, nullable=True, comment='JSON array of attached file S3 keys')

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "chatId": self.chat_id,
            "toolCalls": self.tool_calls,
            "toolCallId": self.tool_call_id,
            "content": self.content,
            "createdTime": self.created_time.strftime("%Y-%m-%d %H:%M:%S") if self.created_time else None,
            "model": self.model,
            "modelTime": self.model_time,
            "promptTokens": self.prompt_tokens,
            "completionTokens": self.completion_tokens,
            "isSummary": self.is_summary,
            "summaryMessageId": self.summary_message_id,
            "attachedFileS3Keys": json.loads(self.attached_file_s3_keys) if self.attached_file_s3_keys else []
        }
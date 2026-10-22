from typing import List, Optional
from db import alchemy_db
from model.chat_message import ChatMessage
from model.chat_sub_task import ChatSubTask
from log.logger_factory import logger_factory

logger = logger_factory.create_logger("ChatMessageDao")


class ChatMessageDao:
    def insert(self, message: ChatMessage) -> ChatMessage:
        """Insert a new chat message"""
        alchemy_db.session.add(message)
        alchemy_db.session.flush()
        return message

    def find_by_id(self, message_id: str) -> Optional[ChatMessage]:
        """Find message by ID"""
        return ChatMessage.query.filter(ChatMessage.id == message_id).first()

    def find_by_chat_id(self, chat_id: str, limit: int = 100, offset: int = 0) -> List[ChatMessage]:
        """Find all messages by chat ID"""
        return alchemy_db.session.query(
            ChatMessage.id,
            ChatMessage.role,
            ChatMessage.content,
            ChatMessage.chat_id,
            ChatMessage.tool_call_id,
            ChatMessage.tool_calls,
            ChatMessage.created_time,
            ChatMessage.model,
            ChatMessage.model_time,
            ChatMessage.prompt_tokens,
            ChatMessage.completion_tokens,
            ChatMessage.is_summary,
            ChatMessage.summary_message_id,
            ChatMessage.attached_file_s3_keys,
            ChatSubTask.id.label('sub_task_id'),
            ChatSubTask.tool_name,
            ChatSubTask.status,
            ChatSubTask.tool_params
        )\
            .outerjoin(ChatSubTask, ChatSubTask.chat_message_id == ChatMessage.id)\
            .filter(ChatMessage.chat_id == chat_id)\
            .order_by(ChatMessage.created_time.asc())\
            .offset(offset).limit(limit).all()

    def update(self, message: ChatMessage) -> ChatMessage:
        """Update message record"""
        alchemy_db.session.merge(message)
        alchemy_db.session.flush()
        return message

    def update_content(self, message_id: str, content: str, tool_calls: str = None) -> bool:
        """Update message content"""
        update_data = {'content': content}
        if tool_calls is not None:
            update_data['tool_calls'] = tool_calls
            
        result = ChatMessage.query.filter(ChatMessage.id == message_id).update(update_data)
        alchemy_db.session.flush()
        return result > 0
    
    def batch_update(self, message_ids, updated_attrs: dict) -> int:
        """Batch update messages by IDs"""
        if not message_ids or not updated_attrs:
            return 0
        result = ChatMessage.query.filter(ChatMessage.id.in_(message_ids)).update(updated_attrs, synchronize_session=False)
        alchemy_db.session.flush()
        return result

    def delete_by_chat_id(self, chat_id: str) -> bool:
        """Delete all messages by chat ID"""
        result = ChatMessage.query.filter(ChatMessage.chat_id == chat_id).delete()
        alchemy_db.session.flush()
        return result > 0

    def count_by_chat_id(self, chat_id: str) -> int:
        """Count messages by chat ID"""
        return ChatMessage.query.filter(ChatMessage.chat_id == chat_id).count()


chat_message_dao = ChatMessageDao()
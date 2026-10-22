from typing import List, Optional
from db import alchemy_db
from model.chat import Chat
from log.logger_factory import logger_factory

logger = logger_factory.create_logger("ChatDao")


class ChatDao:
    def insert(self, chat: Chat) -> Chat:
        """Insert a new chat record"""
        alchemy_db.session.add(chat)
        alchemy_db.session.flush()
        return chat

    def find_by_id(self, chat_id: str) -> Optional[Chat]:
        """Find chat by ID"""
        return Chat.query.filter(Chat.id == chat_id).first()
    
    def find_by_user_id(self, user_id: str, limit: int, offset: int) -> List[Chat]:
        """Find chats by user ID with pagination"""
        return Chat.query.filter(Chat.user_id == user_id).order_by(Chat.created_time.desc()).limit(limit).offset(offset).all()
    
    def find_updated_time_by_id(self, chat_id: str):
        """Find chat updated time by ID"""
        return alchemy_db.session.query(Chat.updated_time).filter(Chat.id == chat_id).scalar()

    def find_by_analysis_id(self, analysis_id: str) -> List[Chat]:
        """Find all chats by analysis ID"""
        return Chat.query.filter(Chat.analysis_id == analysis_id).order_by(Chat.created_time.desc()).all()

    def update(self, chat: Chat) -> Chat:
        """Update chat record"""
        alchemy_db.session.merge(chat)
        alchemy_db.session.flush()
        return chat

    def delete(self, chat_id: str) -> bool:
        """Delete chat by ID"""
        chat = self.find_by_id(chat_id)
        if chat:
            alchemy_db.session.delete(chat)
            alchemy_db.session.flush()
            return True
        return False

    def update_status(self, chat_id: str, status: str, updated_time=None) -> bool:
        """Update chat status"""
        from datetime import datetime
        if updated_time is None:
            updated_time = datetime.now()
        
        result = Chat.query.filter(Chat.id == chat_id).update({
            'status': status,
            'updated_time': updated_time
        })
        alchemy_db.session.flush()
        return result > 0


chat_dao = ChatDao()
from model.chat_session import ChatSession
from db import alchemy_db as db


class ChatSessionDao:
    
    @staticmethod
    def create(session_data):
        """Create new chat session"""
        session = ChatSession(**session_data)
        db.session.add(session)
        db.session.commit()
        return session
    
    @staticmethod
    def get_by_id(session_id):
        """Get session by ID"""
        return ChatSession.query.filter_by(id=session_id, is_active=True).first()
    
    @staticmethod
    def get_by_analysis_id(analysis_id):
        """Get all sessions for analysis"""
        return ChatSession.query.filter_by(analysis_id=analysis_id, is_active=True)\
                               .order_by(ChatSession.updated_time.desc()).all()
    
    @staticmethod
    def update(session_id, update_data):
        """Update session"""
        session = ChatSession.query.filter_by(id=session_id).first()
        if session:
            for key, value in update_data.items():
                setattr(session, key, value)
            db.session.commit()
        return session
    
    @staticmethod
    def delete(session_id):
        """Soft delete session"""
        session = ChatSession.query.filter_by(id=session_id).first()
        if session:
            session.is_active = False
            db.session.commit()
            return True
        return False
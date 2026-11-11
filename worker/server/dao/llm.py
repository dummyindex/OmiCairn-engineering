from model.llm_consumption import LLMConsumption
from model.agent_session import AgentSession
from db import alchemy_db as db
from sqlalchemy import and_
from typing import List, Optional

class LLMDao:
    def insert_consumption(self, llm_consumption: LLMConsumption) -> LLMConsumption:
        db.session.add(llm_consumption)
        db.session.flush()
        return llm_consumption
    
    # Agent Session operations
    def insert_agent_session(self, agent_session: AgentSession) -> AgentSession:
        """Insert a new agent session record"""
        db.session.add(agent_session)
        db.session.flush()
        return agent_session
    
    def get_agent_session_by_id(self, session_id: int) -> Optional[AgentSession]:
        """Get agent session by ID"""
        return db.session.query(AgentSession).filter(
            AgentSession.id == session_id
        ).first()
    
    def update_agent_session(self, session_id: int, **kwargs) -> Optional[AgentSession]:
        """Update agent session fields"""
        session = self.get_agent_session_by_id(session_id)
        if session:
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            db.session.flush()
        return session
    
    def delete_agent_session(self, session_id: int) -> bool:
        """Delete an agent session"""
        session = self.get_agent_session_by_id(session_id)
        if session:
            db.session.delete(session)
            db.session.flush()
            return True
        return False
    
    def query_agent_sessions_by_node(
        self, 
        current_node_id: int, 
        agent_type: Optional[str] = None
    ) -> List[tuple]:
        """
        Query agent sessions by node_id with optional agent_type filter
        Returns list of tuples (AgentSession, LLMConsumption)
        """
        query = db.session.query(AgentSession, LLMConsumption).outerjoin(
            LLMConsumption,
            AgentSession.consumption_id == LLMConsumption.id
        ).filter(AgentSession.current_node_id == current_node_id)
        
        if agent_type:
            query = query.filter(AgentSession.agent_type == agent_type)
        
        return query.order_by(AgentSession.created_time.desc()).all()
    
    def query_agent_sessions_by_computation(
        self, 
        current_computation_id: int, 
        agent_type: Optional[str] = None
    ) -> List[tuple]:
        """
        Query agent sessions by computation_id with optional agent_type filter
        Returns list of tuples (AgentSession, LLMConsumption)
        """
        query = db.session.query(AgentSession, LLMConsumption).outerjoin(
            LLMConsumption,
            AgentSession.consumption_id == LLMConsumption.id
        ).filter(AgentSession.current_computation_id == current_computation_id)
        
        if agent_type:
            query = query.filter(AgentSession.agent_type == agent_type)
        
        return query.order_by(AgentSession.created_time.desc()).all()
    
    def query_agent_sessions_by_type(
        self, 
        agent_type: str,
        current_node_id: Optional[int] = None,
        current_computation_id: Optional[int] = None
    ) -> List[tuple]:
        """
        Query agent sessions by agent_type with optional node/computation filters
        Returns list of tuples (AgentSession, LLMConsumption)
        """
        query = db.session.query(AgentSession, LLMConsumption).outerjoin(
            LLMConsumption,
            AgentSession.consumption_id == LLMConsumption.id
        ).filter(AgentSession.agent_type == agent_type)
        
        if current_node_id is not None:
            query = query.filter(AgentSession.current_node_id == current_node_id)
        
        if current_computation_id is not None:
            query = query.filter(AgentSession.current_computation_id == current_computation_id)
        
        return query.order_by(AgentSession.created_time.desc()).all()

llm_dao = LLMDao()

from tool.llm_interface import LlmInterface
from log.logger_factory import LoggerFactory
from dao.llm import llm_dao
from model.agent_session import AgentSession
from typing import List, Dict, Any, Optional
import time

logger = LoggerFactory.get_logger("LLMService")


class LLMService:
    def chat(self, messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """
        Chat with LLM

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name to use

        Returns:
            Dict with 'message', 'token_consumptions', and 'model_time'
        """
        try:
            llm_interface = LlmInterface()

            start_time = time.time()

            # Call LLM
            response = llm_interface.chat(messages, model=model)

            model_time = time.time() - start_time

            # Extract response content
            if isinstance(response, dict):
                message_content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
                usage = response.get('usage', {})
                token_consumptions = {
                    'prompt_tokens': usage.get('prompt_tokens', 0),
                    'completion_tokens': usage.get('completion_tokens', 0),
                    'total_tokens': usage.get('total_tokens', 0)
                }
            elif isinstance(response, str):
                message_content = response
                token_consumptions = {
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'total_tokens': 0
                }
            else:
                message_content = str(response)
                token_consumptions = {
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'total_tokens': 0
                }

            return {
                'message': message_content,
                'token_consumptions': token_consumptions,
                'model_time': model_time
            }

        except Exception as e:
            logger.error(f"Error chatting with LLM: {str(e)}")
            return {
                'message': '',
                'token_consumptions': {
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'total_tokens': 0
                },
                'model_time': 0
            }
    
    def create_agent_session(
        self,
        agent_type: str,
        status: str,
        current_node_id: Optional[int] = None,
        current_analysis_id: Optional[int] = None,
        current_computation_id: Optional[int] = None,
        consumption_id: Optional[int] = None
    ) -> AgentSession:
        """
        Create a new agent session record
        
        Args:
            agent_type: Type of agent (e.g., 'code_agent', 'visualizer_agent', 'job_reviewer')
            status: Session status
            current_node_id: Optional node ID
            current_analysis_id: Optional analysis ID
            current_computation_id: Optional computation ID
            consumption_id: Optional LLM consumption ID
        
        Returns:
            Created AgentSession object
        """
        try:
            session = AgentSession()
            session.agent_type = agent_type
            session.status = status
            session.current_node_id = current_node_id
            session.current_analysis_id = current_analysis_id
            session.current_computation_id = current_computation_id
            session.consumption_id = consumption_id
            
            session = llm_dao.insert_agent_session(session)
            logger.info(f"Created agent session {session.id} for agent_type={agent_type}")
            return session
        except Exception as e:
            logger.error(f"Error creating agent session: {str(e)}")
            raise
    
    def query_sessions_by_node(
        self,
        current_node_id: int,
        agent_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query agent sessions by node_id with optional agent_type filter
        
        Args:
            current_node_id: Node ID to query
            agent_type: Optional agent type filter
        
        Returns:
            List of session dictionaries with consumption info
        """
        try:
            results = llm_dao.query_agent_sessions_by_node(current_node_id, agent_type)
            return self._format_session_results(results)
        except Exception as e:
            logger.error(f"Error querying sessions by node: {str(e)}")
            raise
    
    def query_sessions_by_computation(
        self,
        current_computation_id: int,
        agent_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query agent sessions by computation_id with optional agent_type filter
        
        Args:
            current_computation_id: Computation ID to query
            agent_type: Optional agent type filter
        
        Returns:
            List of session dictionaries with consumption info
        """
        try:
            results = llm_dao.query_agent_sessions_by_computation(current_computation_id, agent_type)
            return self._format_session_results(results)
        except Exception as e:
            logger.error(f"Error querying sessions by computation: {str(e)}")
            raise
    
    def _format_session_results(self, results: List[tuple]) -> List[Dict[str, Any]]:
        """
        Format query results into dictionaries
        
        Args:
            results: List of (AgentSession, LLMConsumption) tuples
        
        Returns:
            List of formatted dictionaries
        """
        formatted = []
        for session, consumption in results:
            session_dict = session.to_dict()
            if consumption:
                session_dict['consumption'] = consumption.to_dict()
            else:
                session_dict['consumption'] = None
            formatted.append(session_dict)
        return formatted


llm_service = LLMService()

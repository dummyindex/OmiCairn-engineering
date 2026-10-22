from dao.chat_session import ChatSessionDao
from dao.node import node_dao
from dao.analysis import AnalysisDao
from dao.computation import computation_dao
from dao.data import data_dao
from dao.figure import figure_dao
from dao.function_block_v1 import function_block_v1_dao
from sss.porter_factory import PorterFactory
from service.flow import flow_service
from service.chatbot_llm import ChatbotLLMService, LLM_UNAVAILABLE_NOTICE
from constants.node import NodeType
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from log.logger_factory import logger_factory

logger = logger_factory.create_logger(__name__)

class ChatbotService:
    
    def __init__(self):
        self.llm_service = ChatbotLLMService()
    
    @classmethod
    def create_session(cls, analysis_id, title):
        """Create new chat session"""
        session_id = str(uuid.uuid4())
        
        session_data = {
            'id': session_id,
            'analysis_id': analysis_id,
            'title': title,
            'created_time': datetime.now(),
            'updated_time': datetime.now(),
            'message_count': 0,
            'is_active': True
        }
        
        session = ChatSessionDao.create(session_data)
        
        # Initialize empty messages file in S3
        cls._init_messages_file(analysis_id, session_id)
        
        return session
    
    @staticmethod
    def get_session(session_id):
        """Get session by ID"""
        return ChatSessionDao.get_by_id(session_id)
    
    @staticmethod
    def get_session_history(analysis_id):
        """Get all sessions for an analysis"""
        return ChatSessionDao.get_by_analysis_id(analysis_id)
    
    @staticmethod
    def delete_session(session_id):
        """Delete session and its messages"""
        session = ChatSessionDao.get_by_id(session_id)
        if session:
            # Delete messages from S3
            ChatbotService._delete_messages_file(session.analysis_id, session_id)
            # Delete session from database
            ChatSessionDao.delete(session_id)
            return True
        return False
    
    @staticmethod
    def get_messages(session_id):
        """Get messages from S3"""
        session = ChatSessionDao.get_by_id(session_id)
        if not session:
            raise Exception("Session not found")
        
        porter = PorterFactory.create_porter()
        s3_path = f"chatbot-messages/analysis-{session.analysis_id}/session-{session_id}/messages.json"
        
        try:
            porter.set_operation_target(s3_path)
            content = porter.fetch_file_stream()
            return json.loads(content.decode('utf-8'))
        except:
            return []
    
    def send_message(self, session_id, content, files=None, context_nodes=None, model=None, context_type=None, user_id=None):
        """Send message and get LLM response"""
        session = ChatSessionDao.get_by_id(session_id)
        if not session:
            raise Exception("Session not found")
        
        # Get current messages for context
        messages = ChatbotService.get_messages(session_id)
        
        
        # Add user message
        user_message = {
            'id': str(uuid.uuid4()),
            'role': 'user',
            'content': content,
            'timestamp': int(datetime.now().timestamp() * 1000),
            'files': files or [],
            'contextNodes': context_nodes,
            'contextType': context_type,
        }
        messages.append(user_message)
        
        # Prepare context data for LLM
        context_data = {}
            
        # Get enhanced context based on context type
        if context_type == 'analysis':
            analysis_context = ChatbotService._get_analysis_context(session.analysis_id)
            if analysis_context:
                context_data = {"analysis_info": analysis_context}
        elif context_type == 'pipeline' and context_nodes:
            pipeline_context = ChatbotService.get_pipeline_context(context_nodes)
            if pipeline_context:
                context_data = pipeline_context
        elif context_type == 'node' and context_nodes:
            node_context = ChatbotService.get_node_context(context_nodes)
            if node_context:
                context_data = node_context
        elif context_type == 'multinodes' and context_nodes:
            multinodes_context = ChatbotService.get_multinodes_context(context_nodes)
            if multinodes_context:
                context_data = multinodes_context 

        try:
            llm_response, recommended_functionalities = self.llm_service.generate_response(
                content=content,
                context_type=context_type or 'analysis',
                context_data=context_data,
                analysis_id=session.analysis_id,
                user_id=user_id
            )
        except Exception as e:
            # Fallback to a clearly labelled template response if the LLM service fails
            llm_response = LLM_UNAVAILABLE_NOTICE + self._generate_simple_response(content, context_type or 'analysis')
            recommended_functionalities = []
        
        assistant_message = {
            'id': str(uuid.uuid4()),
            'role': 'assistant',
            'content': llm_response,
            'timestamp': int(datetime.now().timestamp() * 1000),
            'contextType': context_type or 'analysis',
            'recommendedFunctionalities': recommended_functionalities
        }
        messages.append(assistant_message)
        
        # Save messages to S3
        ChatbotService._save_messages(session.analysis_id, session_id, messages)
        
        is_first_message = len(messages) == 2
        session_updates = {
            'message_count': len(messages),
            'updated_time': datetime.now()
        }
        
        if is_first_message and session.title and (session.title.startswith('New Chat') or 'New Chat' in session.title):
            # Generate a meaningful title based on the first user message
            try:
                new_title = self.llm_service.generate_chat_title(content, context_type)
                session_updates['title'] = new_title
            except Exception as e:
                pass
        
        # Update session
        ChatSessionDao.update(session_id, session_updates)
        
        return assistant_message
    
    def _generate_simple_response(self, content, context_type):
        """Generate simple placeholder response"""
        responses = {
            'analysis': f"I understand you're asking about the analysis: '{content}'. I'm here to help with your bioinformatics analysis. How can I assist you further?",
            'pipeline': f"Regarding the pipeline you mentioned: '{content}'. I can help you understand the workflow, troubleshoot issues, or interpret results.",
            'node': f"About the node you're asking about: '{content}'. I can provide information about this analysis step and help with any questions.",
            'multinodes': f"Concerning the multiple nodes: '{content}'. I can help you understand how these analysis steps work together."
        }
        return responses.get(context_type, "I'm your bioinformatics AI assistant. How can I help you today?")
    
    @staticmethod
    def get_pipeline_context(data_node_id):
        """Get complete pipeline context from data node"""
        node = node_dao.find_by_id(data_node_id)
        if not node:
            return None
            
        # Get all nodes downstream from the data node
        pipeline_nodes = flow_service.get_later_node_list_by_node_id(data_node_id, with_self=True)
        
        if not pipeline_nodes:
            return None
            
        context = {
            'nodes': [],
            'computations': {},
        }
        
        node_ids = [n.id for n in pipeline_nodes]
        computations = computation_dao.find_all_by_node_id_list(node_ids)
        computation_by_node = {}
        latest_computation_by_node = {}
        
        # Group computations by node and find latest for each
        for comp in computations:
            if comp.node_id not in computation_by_node:
                computation_by_node[comp.node_id] = []
            computation_by_node[comp.node_id].append(comp)
            
            # Track latest computation (by created_time)
            if (comp.node_id not in latest_computation_by_node or 
                comp.created_time > latest_computation_by_node[comp.node_id].created_time):
                latest_computation_by_node[comp.node_id] = comp
        
        # Process each node
        for pipeline_node in pipeline_nodes:
            node_info = {
                'id': pipeline_node.id,
                'name': pipeline_node.name,
                'type': pipeline_node.type,
                'state': pipeline_node.state,
                'created_time': pipeline_node.created_time.isoformat() if pipeline_node.created_time else None,
                'position': {'x': pipeline_node.x, 'y': pipeline_node.y} if hasattr(pipeline_node, 'x') and hasattr(pipeline_node, 'y') else None,
                'locked': getattr(pipeline_node, 'locked', False),
                'tag': getattr(pipeline_node, 'tag', None),
                'system_env': getattr(pipeline_node, 'system_env', None),
                'avg_duration': getattr(pipeline_node, 'avg_duration', None)
            }
            
            # Add computation information for computation nodes
            if (pipeline_node.type == NodeType.COMPUTATION_NODE.value or pipeline_node.type == NodeType.COMPUTATION_NODE_V2.value) and pipeline_node.id in latest_computation_by_node:
                latest_comp = latest_computation_by_node[pipeline_node.id]
                computation_info = {
                    'latest_computation_id': latest_comp.id,
                    'computation_state': latest_comp.computation_state,
                    'created_time': latest_comp.created_time.isoformat() if latest_comp.created_time else None,
                    'duration': latest_comp.duration,
                    'computation_params': latest_comp.computation_params,
                    'source_data_ids': json.loads(latest_comp.source_data_ids) if latest_comp.source_data_ids else None,
                    'result_data_id': latest_comp.result_data_id,
                    'error_message': getattr(latest_comp, 'error_message', None)
                }

                context['computations'][pipeline_node.id] = computation_info
                node_info['latest_computation'] = computation_info
            
            context['nodes'].append(node_info)
        logger.info(f"[get_pipeline_context] Final pipeline context: {context}")
        return context
    
    @staticmethod
    def get_node_context(node_id):
        """Get context for a single node"""
        node = node_dao.find_by_id(node_id)
        if not node:
            return None
            
        context = {
            'node': {
                'id': node.id,
                'name': node.name,
                'type': node.type,
                'state': node.state,
                'created_time': node.created_time.isoformat() if node.created_time else None,
                'position': {'x': node.x, 'y': node.y} if hasattr(node, 'x') and hasattr(node, 'y') else None,
                'locked': getattr(node, 'locked', False),
                'tag': getattr(node, 'tag', None),
                'system_env': getattr(node, 'system_env', None),
                'avg_duration': getattr(node, 'avg_duration', None)
            }
        }
        
        # Add computation information if it's a computation node
        if node.type == NodeType.COMPUTATION_NODE.value or node.type == NodeType.COMPUTATION_NODE_V2.value:
            computations = computation_dao.find_all_by_node_id_list([node.id])
            if computations:
                latest_comp = max(computations, key=lambda c: c.created_time)
                computation_info = {
                    'latest_computation_id': latest_comp.id,
                    'computation_state': latest_comp.computation_state,
                    'created_time': latest_comp.created_time.isoformat() if latest_comp.created_time else None,
                    'duration': latest_comp.duration,
                    'computation_params': latest_comp.computation_params,
                    'source_data_ids': json.loads(latest_comp.source_data_ids) if latest_comp.source_data_ids else None,
                    'result_data_id': latest_comp.result_data_id,
                    'error_message': getattr(latest_comp, 'error_message', None)
                }
                context['computation'] = computation_info
                context['node']['latest_computation'] = computation_info
        
        logger.info(f"[get_node_context] Context for node {node_id}: {context}")
        return context
    
    @staticmethod
    def get_multinodes_context(node_ids):
        """Get context for multiple nodes"""
        if isinstance(node_ids, str):
            try:
                node_ids = json.loads(node_ids)
            except:
                node_ids = [node_ids]
        
        if not isinstance(node_ids, list):
            node_ids = [node_ids]
            
        nodes = []
        for node_id in node_ids:
            node = node_dao.find_by_id(node_id)
            if node:
                nodes.append(node)
        
        if not nodes:
            return None
            
        context = {
            'nodes': [],
            'computations': {}
        }
        
        # Get computations for all nodes
        all_node_ids = [n.id for n in nodes]
        computations = computation_dao.find_all_by_node_id_list(all_node_ids)
        
        # Group computations by node and find latest for each
        latest_computation_by_node = {}
        for comp in computations:
            if (comp.node_id not in latest_computation_by_node or 
                comp.created_time > latest_computation_by_node[comp.node_id].created_time):
                latest_computation_by_node[comp.node_id] = comp
        
        # Process each node
        for node in nodes:
            node_info = {
                'id': node.id,
                'name': node.name,
                'type': node.type,
                'state': node.state,
                'created_time': node.created_time.isoformat() if node.created_time else None,
                'position': {'x': node.x, 'y': node.y} if hasattr(node, 'x') and hasattr(node, 'y') else None,
                'locked': getattr(node, 'locked', False),
                'tag': getattr(node, 'tag', None),
                'system_env': getattr(node, 'system_env', None),
                'avg_duration': getattr(node, 'avg_duration', None)
            }
            
            # Add computation information for computation nodes
            if (node.type == NodeType.COMPUTATION_NODE.value or node.type == NodeType.COMPUTATION_NODE_V2.value) and node.id in latest_computation_by_node:
                latest_comp = latest_computation_by_node[node.id]
                computation_info = {
                    'latest_computation_id': latest_comp.id,
                    'computation_state': latest_comp.computation_state,
                    'created_time': latest_comp.created_time.isoformat() if latest_comp.created_time else None,
                    'duration': latest_comp.duration,
                    'computation_params': latest_comp.computation_params,
                    'source_data_ids': json.loads(latest_comp.source_data_ids) if latest_comp.source_data_ids else None,
                    'result_data_id': latest_comp.result_data_id,
                    'error_message': getattr(latest_comp, 'error_message', None)
                }
                context['computations'][node.id] = computation_info
                node_info['latest_computation'] = computation_info
            
            context['nodes'].append(node_info)
        
        logger.info(f"[get_multinodes_context] Final context for nodes {node_ids}: {context}")
        return context
    
    @staticmethod
    def _get_analysis_context(analysis_id: int) -> Dict[str, Any]:
        """Get analysis-level context information"""
        try:
            data_list = data_dao.find_imported_by_analysis_id(analysis_id)
            
            analysis_info = {
                "id": analysis_id,
                "data_count": len(data_list) if data_list else 0,
                "has_results": False
            }
            
            computations = computation_dao.find_by_analysis_id(analysis_id)
            if computations:
                completed_count = sum(1 for comp in computations if comp.computation_state == "finished")
                analysis_info["has_results"] = completed_count > 0
                
            return analysis_info
            
        except Exception as e:
            logger.error(f"Error getting analysis context: {e}")
            return {"id": analysis_id, "data_count": 0, "has_results": False}
    
    @staticmethod
    def _init_messages_file(analysis_id, session_id):
        """Initialize empty messages file in S3"""
        porter = PorterFactory.create_porter()
        s3_path = f"chatbot-messages/analysis-{analysis_id}/session-{session_id}/messages.json"
        porter.set_operation_target(s3_path)
        porter.save_file_text(json.dumps([]))
    
    @staticmethod
    def _save_messages(analysis_id, session_id, messages):
        """Save messages to S3"""
        porter = PorterFactory.create_porter()
        s3_path = f"chatbot-messages/analysis-{analysis_id}/session-{session_id}/messages.json"
        porter.set_operation_target(s3_path)
        porter.save_file_text(json.dumps(messages))
    
    @staticmethod
    def _delete_messages_file(analysis_id, session_id):
        """Delete messages file from S3"""
        porter = PorterFactory.create_porter()
        s3_path = f"chatbot-messages/analysis-{analysis_id}/session-{session_id}/messages.json"
        # Delete the messages file
        try:
            porter.set_operation_target(s3_path)
            porter.remove_file()
        except:
            pass  # Ignore if file doesn't exist
from flask import Blueprint, request, jsonify
from service.chatbot import ChatbotService
from tool.response_manager import ResponseManager
from authority.guardian_factory import AuthorityGuardianFactory
import uuid

chatbot_bp = Blueprint('chatbot', __name__)
chatbot_service = ChatbotService()

@chatbot_bp.route('/api/v1/analysis/<int:analysis_id>/chat/sessions', methods=['POST'])
def create_session(analysis_id):
    """Create a new chat session"""
    try:
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        guardian.check_authority(analysis_id)

        data = request.get_json() or {}
        title = data.get('title', 'New Chat Session')
        
        session = ChatbotService.create_session(
            analysis_id=analysis_id,
            title=title,
        )
        
        return ResponseManager.new_success_response(data=session.to_dict())
    except Exception as e:
        return ResponseManager.new_server_error_response(str(e))

@chatbot_bp.route('/api/v1/analysis/<int:analysis_id>/chat/sessions', methods=['GET'])
def get_sessions(analysis_id):
    """Get chat session history by analysis"""
    try:
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        guardian.check_authority(analysis_id)
        
        sessions = ChatbotService.get_session_history(analysis_id)
        return ResponseManager.new_success_response(data=[s.to_dict() for s in sessions])
    except Exception as e:
        return ResponseManager.new_server_error_response(str(e))

@chatbot_bp.route('/api/v1/chat/sessions/<string:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a chat session"""
    try:
        # Check if session exists and user has access
        session = ChatbotService.get_session(session_id)
        if not session:
            return ResponseManager.new_bad_request_response("Session not found")
        
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        guardian.check_authority(session.analysis_id)
        
        success = ChatbotService.delete_session(session_id)
        if success:
            return ResponseManager.new_success_response(data={"message": "Session deleted successfully"})
        else:
            return ResponseManager.new_server_error_response("Failed to delete session")
    except Exception as e:
        return ResponseManager.new_server_error_response(str(e))

@chatbot_bp.route('/api/v1/chat/sessions/<string:session_id>/messages', methods=['GET'])
def get_messages(session_id):
    """Get messages by session"""
    try:
        # Check if session exists and user has access
        session = ChatbotService.get_session(session_id)
        if not session:
            return ResponseManager.new_bad_request_response("Session not found")
        
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        guardian.check_authority(session.analysis_id)
        
        messages = ChatbotService.get_messages(session_id)
        return ResponseManager.new_success_response(data=messages)
    except Exception as e:
        return ResponseManager.new_server_error_response(str(e))

@chatbot_bp.route('/api/v1/chat/sessions/<string:session_id>/messages', methods=['POST'])
def send_message(session_id):
    """Send message to chatbot"""
    try:
        # Check if session exists and user has access
        session = ChatbotService.get_session(session_id)
        if not session:
            return ResponseManager.new_bad_request_response("Session not found")
        
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        guardian.check_authority(session.analysis_id)
        user_id = guardian.get_user_id()
        
        data = request.get_json()
        
        context_type = data.get('contextType', 'analysis')
        
        # Extract context-specific node references based on context type from request
        context_nodes = None
        
        if context_type == 'pipeline':
            context_nodes = data.get('dataNodeId')
        elif context_type == 'node':
            context_nodes = data.get('nodeId')
        elif context_type == 'multinodes':
            context_nodes = data.get('nodeIds', [])
        
        response = chatbot_service.send_message(
            session_id=session_id,
            content=data.get('content'),
            files=data.get('files', []),
            context_nodes=context_nodes,
            model=data.get('model'),
            context_type=context_type,
            user_id=user_id
        )
        
        return ResponseManager.new_success_response(data=response)
    except Exception as e:
        return ResponseManager.new_server_error_response(str(e))
from flask import Blueprint, request
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from service.chat import chat_service
from wrapper.exception import exception_wrapper
from exception.request.parameter_invalid import ParameterInvalidException
from constants.authority import AuthorityCarrier
import subprocess
import os
import sys
import tempfile

CHAT_AGENT_LOG_DIR = os.environ.get("CHAT_AGENT_LOG_DIR", tempfile.gettempdir())
import json
from log.logger_factory import logger_factory
from db import alchemy_db

logger = logger_factory.create_logger("ChatController")

class ChatListAPI(Resource):
    @exception_wrapper
    def get(self):
        """List chats - /v3.0/chat/list"""
        guardian = AuthorityGuardianFactory.get_authority_guardian()

        user_id = guardian.require_user_id()
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        result = chat_service.list_chats(user_id, limit, offset)
        return ResponseManager.new_success_response(data=result)

class ChatCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """Create a new chat - /v3.0/chat/create"""
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)

        user_id = guardian.get_user_id()
        
        data = request.get_json() or {}
        analysis_id = data.get('analysis_id')
        current_node_id = data.get('current_node_id')
        model = data.get('model', 'gpt-4o-mini')
        
        if not analysis_id:
            raise ParameterInvalidException("analysis_id is required")

        # Check authority for analysis
        guardian.check_authority(analysis_id)

        result = chat_service.create_chat(analysis_id, current_node_id, model=model, user_id=user_id)
        alchemy_db.session.commit()
        
        # Initialize chat agent
        self._call_chat_agent_init(result.id, user_id=user_id)

        return ResponseManager.new_success_response(data=result)

    def _call_chat_agent_init(self, chat_id: int, user_id: int):
        """Call chat agent initialization via subprocess asynchronously"""
        script_path = os.path.join(os.path.dirname(__file__), '../../chat_agent/main.py')
        cmd = [sys.executable, script_path, 'init', '--chat_id', str(chat_id), '--user_id', str(user_id)]
        # Start the process asynchronously; no need to wait
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"Started chat agent init process {process.pid} for chat {chat_id}")


class ChatSendMessageAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """Send message to chat - /v3.0/chat/send-message"""
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        user_id = guardian.get_user_id()
        
        data = request.get_json() or {}
        chat_id = data.get('chat_id')
        message = data.get('message')
        fileS3Key = data.get('fileS3Key', [])
        
        if not chat_id or not message:
            raise ParameterInvalidException("chat_id and message are required")

        # Check if chat exists and get analysis_id for authority check
        chat = chat_service.get_chat_information(chat_id)
        if not chat:
            raise ParameterInvalidException(f"Chat {chat_id} not found")

        guardian.check_authority(chat.analysis_id)

        # Call chat agent via subprocess
        self._call_chat_agent_send_message(chat_id, message, fileS3Key, user_id=user_id)
        
        return ResponseManager.new_success_response(message="Message sent successfully")

    def _call_chat_agent_send_message(self, chat_id: int, message: str, fileS3Key: list, user_id: int):
        """Call chat agent send message via subprocess asynchronously"""
        script_path = os.path.join(os.path.dirname(__file__), '../../chat_agent/main.py')
        cmd = [sys.executable, script_path, 'send_message', '--chat_id', str(chat_id), '--message', message, '--user_id', str(user_id)]
        
        if fileS3Key:
            cmd.extend(['--attached_files', json.dumps(fileS3Key)])
        
        # Start the process asynchronously; no need to wait
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # TODO: Save chatbot process stdout/stderr to log file if needed
        # process = subprocess.Popen(cmd)
        logger.info(f"Started chat agent send message process {process.pid} for chat {chat_id}")


class ChatCallToolAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """Call tool in chat - /v3.0/chat/call-tool"""
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        user_id = guardian.get_user_id()
        
        data = request.get_json() or {}
        chat_id = data.get('chat_id')
        tool_call_id = data.get('tool_call_id')
        tool_name = data.get('tool_name')
        tool_params = data.get('tool_params', {})
        
        if not chat_id or not tool_name:
            raise ParameterInvalidException("chat_id and tool_name are required")

        # Check if chat exists and get analysis_id for authority check
        chat = chat_service.get_chat_information(chat_id)
        if not chat:
            raise ParameterInvalidException(f"Chat {chat_id} not found")

        guardian.check_authority(chat.analysis_id)

        # Call chat agent via subprocess
        self._call_chat_agent_call_tool(chat_id, tool_call_id, tool_name, tool_params, user_id=user_id)
        return ResponseManager.new_success_response(message="Tool call started")

    def _call_chat_agent_call_tool(self, chat_id: int, tool_call_id: str, tool_name: str, tool_params: dict, user_id: int):
        """Call chat agent call tool via subprocess asynchronously"""
        script_path = os.path.join(os.path.dirname(__file__), '../../chat_agent/main.py')
        params_json = json.dumps(tool_params)
        cmd = [sys.executable, script_path, 'call_tool', '--chat_id', str(chat_id), '--tool_call_id', tool_call_id, '--tool_name', tool_name, '--tool_params', params_json, '--user_id', str(user_id)]
        # Write logs to the /tmp/chat_agent_tool.log file
        log_file_path = os.path.join(CHAT_AGENT_LOG_DIR, 'chat_agent_tool.log')
        with open(log_file_path, 'a') as log_file:
            # Start the process asynchronously; no need to wait
            process = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
            # process = subprocess.Popen(cmd)
            logger.info(f"Started chat agent call tool process {process.pid} for chat {chat_id}, tool {tool_name}")


class ChatHeartbeatAPI(Resource):
    @exception_wrapper
    def get(self):
        """Get chat heartbeat - /v3.0/chat/heartbeat"""
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        
        chat_id = request.args.get('chat_id')
        
        if not chat_id:
            raise ParameterInvalidException("chat_id is required")

        # Check if chat exists and get analysis_id for authority check
        updated_time = chat_service.get_chat_updated_time(chat_id)
        return ResponseManager.new_success_response(data={"updatedTime": updated_time})


class ChatDeleteAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """Delete chat - /v3.0/chat/delete"""
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        
        data = request.get_json() or {}
        chat_id = data.get('chat_id')
        
        if not chat_id:
            raise ParameterInvalidException("chat_id is required")

        # Check if chat exists and get analysis_id for authority check
        chat = chat_service.get_chat_information(chat_id)
        if not chat:
            raise ParameterInvalidException(f"Chat {chat_id} not found")

        guardian.check_authority(chat.analysis_id)

        success = chat_service.delete_chat(chat_id)
        if success:
            return ResponseManager.new_success_response(message="Deleted successfully")
        else:
            return ResponseManager.new_server_error_response("Delete failed")


class ChatUpdateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """Update chat - /v3.0/chat/update"""
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        
        chat_id = request.args.get('chat_id')
        updated_attrs = request.get_json() or {}

        chat = chat_service.get_chat_information(chat_id)
        if not chat:
            raise ParameterInvalidException(f"Chat {chat_id} not found")
        guardian.check_authority(chat.analysis_id, check_writable=True)

        chat_service.update_chat_information(chat_id, updated_attrs)
        return ResponseManager.new_success_response(message="Updated successfully")

# APIs for frontend and ChatAgent
class ChatGetInformationAPI(Resource):
    @exception_wrapper
    def get(self):
        """Get chat information - /v3.0/chat/get-information"""
        chat_id = request.args.get('chat_id')
        
        if not chat_id:
            raise ParameterInvalidException("chat_id is required")

        result = chat_service.get_chat_information(chat_id)
        if not result:
            raise ParameterInvalidException(f"Chat {chat_id} not found")
            
        return ResponseManager.new_success_response(data=result)


class ChatGetMessagesAPI(Resource):
    @exception_wrapper
    def get(self):
        """Get chat messages - /v3.0/chat/get-messages"""
        chat_id = request.args.get('chat_id')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if not chat_id:
            raise ParameterInvalidException("chat_id is required")

        messages = chat_service.get_chat_messages(chat_id, limit, offset)
        return ResponseManager.new_success_response(data={"messages": messages})


class ChatUpdateInformationAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """Update chat information - /v3.0/chat/update-chat-information"""
        data = request.get_json() or {}
        chat_id = data.get('chat_id')
        updated_attrs = data.get('updated_chat_attrs', {})
        
        if not chat_id:
            raise ParameterInvalidException("chat_id is required")

        success = chat_service.update_chat_information(chat_id, updated_attrs)
        if success:
            return ResponseManager.new_success_response(message="Updated successfully")
        else:
            return ResponseManager.new_server_error_response("Update failed")
        
class ChatListSubTaskAPI(Resource):
    @exception_wrapper
    def get(self):
        """List chat sub tasks - /v3.0/chat/list-chat-sub-tasks"""
        chat_id = request.args.get('chat_id')
        
        if not chat_id:
            raise ParameterInvalidException("chat_id is required")

        sub_tasks = chat_service.get_chat_sub_tasks(chat_id)
        return ResponseManager.new_success_response(data={"sub_tasks": sub_tasks})


# APIs for ChatAgent only
class ChatCreateSubTaskAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """Create chat sub task - /v3.0/chat/create-chat-sub-task"""
        data = request.get_json() or {}
        chat_id = data.get('chat_id')
        sub_task_attrs = data.get('chat_sub_task_attrs', {})
        
        if not chat_id:
            raise ParameterInvalidException("chat_id is required")

        result = chat_service.create_chat_sub_task(chat_id, sub_task_attrs)
        return ResponseManager.new_success_response(data=result)


class ChatUpdateSubTaskAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """Update chat sub task - /v3.0/chat/update-chat-sub-task"""
        data = request.get_json() or {}
        sub_task_id = data.get('chat_sub_task_id')
        updated_attrs = data.get('updated_chat_sub_task_attrs', {})
        
        if not sub_task_id:
            raise ParameterInvalidException("chat_sub_task_id is required")

        success = chat_service.update_chat_sub_task(sub_task_id, updated_attrs)
        if success:
            return ResponseManager.new_success_response(message="Updated successfully")
        else:
            return ResponseManager.new_server_error_response("Update failed")


class ChatGetSubTaskAPI(Resource):
    @exception_wrapper
    def get(self):
        """Get chat sub task - /v3.0/chat/get-chat-sub-task"""
        sub_task_id = request.args.get('chat_sub_task_id')
        
        if not sub_task_id:
            raise ParameterInvalidException("chat_sub_task_id is required")

        result = chat_service.get_chat_sub_task(sub_task_id)
        if not result:
            raise ParameterInvalidException(f"Sub task {sub_task_id} not found")
            
        return ResponseManager.new_success_response(data=result)
    
class ChatSubTaskQueryAPI(Resource):
    @exception_wrapper
    def get(self):
        """Query chat sub task by system_task_id and tool_name - /v3.0/chat/query-chat-sub-task"""
        system_task_id = request.args.get('system_task_id')
        tool_name = request.args.get('tool_name')
        
        if not system_task_id or not tool_name:
            raise ParameterInvalidException("system_task_id and tool_name are required")

        result = chat_service.get_chat_sub_task_by_system_id(system_task_id, tool_name)
            
        return ResponseManager.new_success_response(data=result)

class ChatCallbackSubTaskAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """Callback chat sub task - /v3.0/chat/callback-chat-sub-task"""
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        sub_task_id = request.args.get('chat_sub_task_id')

        callback_data = request.get_json() or {}

        if not sub_task_id:
            raise ParameterInvalidException("chat_sub_task_id is required")

        sub_task = chat_service.get_chat_sub_task(sub_task_id)
        if not sub_task:
            raise ParameterInvalidException(f"Sub task with chat_sub_task_id {sub_task_id} not found")
        if sub_task.status != "running":
            return ResponseManager.new_success_response(message="Sub task is not running, no need to callback")
        self._call_tool_feedback(sub_task.chat_id, sub_task.id, json.dumps(callback_data), user_id=user_id)
        return ResponseManager.new_success_response(message="Tool callback started")

    def _call_tool_feedback(self, chat_id: int, chat_sub_task_id: int, output: str, user_id: int) -> bool:
        """Process tool feedback asynchronously"""
        import tempfile
        _fd, tempfile_path = tempfile.mkstemp()
        os.close(_fd)
        with open(tempfile_path, 'w') as f:
            f.write(output)
        script_path = os.path.join(os.path.dirname(__file__), '../../chat_agent/main.py')
        cmd = [sys.executable, script_path, 'call_tool_feedback', '--chat_id', str(chat_id), '--chat_sub_task_id', str(chat_sub_task_id), '--output_path', tempfile_path, '--user_id', str(user_id)]
        # Write logs to the /tmp/chat_agent_tool_callback.log file
        log_file_path = os.path.join(CHAT_AGENT_LOG_DIR, 'chat_agent_tool_callback.log')
        with open(log_file_path, 'a') as log_file:
            # Start the process asynchronously; no need to wait
            process = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
            logger.info(f"Started chat agent tool feedback process {process.pid} for chat {chat_id}, sub_task {chat_sub_task_id}")

class ChatCreateMessageAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """Create chat message - /v3.0/chat/create-message"""
        data = request.get_json() or {}
        chat_id = data.get('chat_id')
        message_data = data.get('message', {})
        
        if not chat_id:
            raise ParameterInvalidException("chat_id is required")

        result = chat_service.create_chat_message(chat_id, message_data)
        return ResponseManager.new_success_response(data=result)


class ChatUpdateMessageAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """Update chat message - /v3.0/chat/update-message"""
        data = request.get_json() or {}
        message_id = data.get('chat_message_id')
        updated_attrs = data.get('updated_message_attrs', {})
        
        if not message_id:
            raise ParameterInvalidException("chat_message_id is required")

        success = chat_service.update_chat_message(message_id, updated_attrs)
        if success:
            return ResponseManager.new_success_response(message="Updated successfully")
        else:
            return ResponseManager.new_server_error_response("Update failed")


class ChatUpdateBatchMessagesAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """Batch update chat messages - /v3.0/chat/update-batch-messages"""
        data = request.get_json() or {}
        message_ids = data.get('chat_message_ids', [])
        updated_attrs = data.get('updated_message_attrs', {})
        
        if not message_ids:
            raise ParameterInvalidException("chat_message_ids are required")

        updated_count = chat_service.update_batch_chat_messages(message_ids, updated_attrs)
        return ResponseManager.new_success_response(data={"updatedCount": updated_count})

# Create blueprint and register routes
chat_bp = Blueprint('chat_v3', __name__)
chat_api = Api(chat_bp, prefix='/v3.0/chat')

# Frontend APIs
chat_api.add_resource(ChatListAPI, '/list')
chat_api.add_resource(ChatCreateAPI, '/create')
chat_api.add_resource(ChatSendMessageAPI, '/send-message')
chat_api.add_resource(ChatCallToolAPI, '/call-tool')
chat_api.add_resource(ChatHeartbeatAPI, '/heartbeat')
chat_api.add_resource(ChatDeleteAPI, '/delete')
chat_api.add_resource(ChatUpdateAPI, '/update')

# Frontend and ChatAgent APIs
chat_api.add_resource(ChatGetInformationAPI, '/get-information')
chat_api.add_resource(ChatGetMessagesAPI, '/get-messages')
chat_api.add_resource(ChatUpdateInformationAPI, '/update-chat-information')
chat_api.add_resource(ChatListSubTaskAPI, '/list-chat-sub-tasks')

# ChatAgent only APIs
chat_api.add_resource(ChatCreateSubTaskAPI, '/create-chat-sub-task')
chat_api.add_resource(ChatUpdateSubTaskAPI, '/update-chat-sub-task')
chat_api.add_resource(ChatGetSubTaskAPI, '/get-chat-sub-task')
chat_api.add_resource(ChatSubTaskQueryAPI, '/query-chat-sub-task')
chat_api.add_resource(ChatCallbackSubTaskAPI, '/callback-chat-sub-task')
chat_api.add_resource(ChatCreateMessageAPI, '/create-message')
chat_api.add_resource(ChatUpdateMessageAPI, '/update-message')
chat_api.add_resource(ChatUpdateBatchMessagesAPI, '/update-batch-messages')
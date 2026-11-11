from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from dao.chat import chat_dao
from dao.chat_message import chat_message_dao
from dao.chat_sub_task import chat_sub_task_dao
from model.chat import Chat
from model.chat_message import ChatMessage
from model.chat_sub_task import ChatSubTask
from constants.chat import ChatStatus, ChatSubTaskStatus, MessageRole
from exception.request.parameter_invalid import ParameterInvalidException
from log.logger_factory import logger_factory

logger = logger_factory.create_logger("ChatService")


class ChatService:

    def list_chats(self, user_id: str, limit: int, offset: int) -> List[Chat]:
        """List chats for a user"""
        chats = chat_dao.find_by_user_id(user_id, limit, offset)
        return chats

    def create_chat(self, analysis_id: str, current_node_id, model, user_id: str = None) -> Dict[str, Any]:
        """Create a new chat"""
        if not analysis_id:
            raise ParameterInvalidException("analysis_id is required")

        name = f"Analysis-{analysis_id}"
        
        chat = Chat(
            name=name,
            analysis_id=analysis_id,
            current_node_id=current_node_id,
            model=model,
            status=ChatStatus.NORMAL.value,
            created_time=datetime.now(),
            updated_time=datetime.now(),
            user_id=user_id
        )
        
        created_chat = chat_dao.insert(chat)
        logger.info(f"Created chat {created_chat.id} for analysis {analysis_id}")
        return created_chat

    def get_chat_information(self, chat_id: str) -> Optional[Chat]:
        """Get chat information by ID"""
        chat = chat_dao.find_by_id(chat_id)
        if not chat:
            return None
        return chat
    
    def get_chat_updated_time(self, chat_id: str) -> Optional[str]:
        """Get chat updated time by ID"""
        updated_time = chat_dao.find_updated_time_by_id(chat_id)
        return updated_time.strftime("%Y-%m-%d %H:%M:%S") if updated_time else None

    def update_chat_information(self, chat_id: str, updated_attrs: Dict[str, Any]) -> bool:
        """Update chat information"""
        chat = chat_dao.find_by_id(chat_id)
        if not chat:
            return False

        # Update allowed attributes
        if 'status' in updated_attrs:
            chat.status = updated_attrs['status']
        if 'model' in updated_attrs:
            chat.model = updated_attrs['model']
        if 'current_node_id' in updated_attrs:
            chat.current_node_id = updated_attrs['current_node_id']
        if 'name' in updated_attrs:
            chat.name = updated_attrs['name']
        
        chat.updated_time = datetime.now()
        chat_dao.update(chat)
        return True

    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat and all related data"""
        chat = chat_dao.find_by_id(chat_id)
        if not chat:
            return False

        # Delete related data
        chat_message_dao.delete_by_chat_id(chat_id)
        chat_sub_task_dao.delete_by_chat_id(chat_id)
        
        # Delete chat
        return chat_dao.delete(chat_id)

    def get_chat_messages(self, chat_id: str, limit: int = 100, offset: int = 0) -> List[ChatMessage]:
        """Get chat messages"""
        messages = chat_message_dao.find_by_chat_id(chat_id, limit, offset)
        return messages

    def create_chat_message(self, chat_id: str, message_data: Dict[str, Any]) -> ChatMessage:
        """Create a new chat message"""
        if not chat_dao.find_by_id(chat_id):
            raise ParameterInvalidException(f"Chat {chat_id} not found")

        attached_file_s3_keys = message_data.get('attached_file_s3_keys')
        attached_file_s3_keys_json = json.dumps(attached_file_s3_keys) if attached_file_s3_keys else None

        message = ChatMessage(
            role=message_data.get('role', MessageRole.USER.value),
            chat_id=chat_id,
            content=message_data.get('content', ''),
            tool_calls=message_data.get('tool_calls'),
            tool_call_id=message_data.get('tool_call_id'),
            created_time=datetime.now(),
            model=message_data.get('model'),
            model_time=message_data.get('model_time', 0),
            prompt_tokens=message_data.get('prompt_tokens', 0),
            completion_tokens=message_data.get('completion_tokens', 0),
            is_summary=message_data.get('is_summary', False),
            summary_message_id=message_data.get('summary_message_id', None),
            attached_file_s3_keys=attached_file_s3_keys_json
        )
        
        created_message = chat_message_dao.insert(message)
        logger.info(f"Created message {created_message.id} for chat {chat_id}")
        return created_message

    def update_chat_message(self, message_id: str, updated_attrs: Dict[str, Any]) -> bool:
        """Update chat message"""
        message = chat_message_dao.find_by_id(message_id)
        if not message:
            return False

        # Update allowed attributes
        if 'content' in updated_attrs:
            message.content = updated_attrs['content']
        if 'tool_calls' in updated_attrs:
            message.tool_calls = updated_attrs['tool_calls']
        if 'model_time' in updated_attrs:
            message.model_time = updated_attrs['model_time']
        if 'prompt_tokens' in updated_attrs:
            message.prompt_tokens = updated_attrs['prompt_tokens']
        if 'completion_tokens' in updated_attrs:
            message.completion_tokens = updated_attrs['completion_tokens']
        if 'tool_call_id' in updated_attrs:
            message.tool_call_id = updated_attrs['tool_call_id']

        chat_message_dao.update(message)
        return True
    
    def update_batch_chat_messages(self, message_ids: List[str], updated_attrs: Dict[str, Any]) -> int:
        """Batch update chat messages"""
        updated_count = chat_message_dao.batch_update(message_ids, updated_attrs)
        return updated_count

    def create_chat_sub_task(self, chat_id: str, sub_task_data: Dict[str, Any]) -> ChatSubTask:
        """Create a new chat sub task"""
        if not chat_dao.find_by_id(chat_id):
            raise ParameterInvalidException(f"Chat {chat_id} not found")

        sub_task = ChatSubTask(
            chat_id=chat_id,
            chat_message_id=sub_task_data.get('chat_message_id'),
            tool_call_id=sub_task_data.get('tool_call_id'),
            tool_name=sub_task_data.get('tool_name'),
            tool_params=sub_task_data.get('tool_params'),
            system_task_id=sub_task_data.get('system_task_id'),
            outputs=sub_task_data.get('outputs'),
            status=sub_task_data.get('status', ChatSubTaskStatus.RUNNING.value),
            created_time=datetime.now(),
            start_time=datetime.now(),
            end_time=None
        )
        
        created_sub_task = chat_sub_task_dao.insert(sub_task)
        logger.info(f"Created sub task {created_sub_task.id} for chat {chat_id}")
        return created_sub_task

    def update_chat_sub_task(self, sub_task_id: str, updated_attrs: Dict[str, Any]) -> bool:
        """Update chat sub task"""
        sub_task = chat_sub_task_dao.find_by_id(sub_task_id)
        if not sub_task:
            return False

        # Update allowed attributes
        if 'system_task_id' in updated_attrs:
            sub_task.system_task_id = updated_attrs['system_task_id']
        if 'outputs' in updated_attrs:
            sub_task.outputs = updated_attrs['outputs']
        if 'status' in updated_attrs:
            sub_task.status = updated_attrs['status']
            if updated_attrs['status'] in ['finished', 'failed'] and not sub_task.end_time:
                sub_task.end_time = datetime.now()
        if 'end_time' in updated_attrs:
            sub_task.end_time = updated_attrs['end_time']
        if 'tool_call_id' in updated_attrs:
            sub_task.tool_call_id = updated_attrs['tool_call_id']

        chat_sub_task_dao.update(sub_task)
        return True

    def get_chat_sub_task(self, sub_task_id: str) -> Optional[ChatSubTask]:
        """Get chat sub task by ID"""
        sub_task = chat_sub_task_dao.find_by_id(sub_task_id)
        if not sub_task:
            return None
        return sub_task

    def get_chat_sub_task_by_system_id(self, system_task_id: str, tool_name: str) -> Optional[ChatSubTask]:
        """Callback to update chat sub task by system task ID"""
        sub_task = chat_sub_task_dao.find_by_tool_name_and_system_task_id(tool_name, system_task_id)
        return sub_task

    def get_chat_sub_tasks(self, chat_id: str) -> List[ChatSubTask]:
        """Get all sub tasks for a chat"""
        sub_tasks = chat_sub_task_dao.find_by_chat_id(chat_id)
        return sub_tasks


chat_service = ChatService()
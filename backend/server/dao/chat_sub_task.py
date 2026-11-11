from typing import List, Optional
from db import alchemy_db
from model.chat_sub_task import ChatSubTask
from log.logger_factory import logger_factory

logger = logger_factory.create_logger("ChatSubTaskDao")


class ChatSubTaskDao:
    def insert(self, sub_task: ChatSubTask) -> ChatSubTask:
        """Insert a new chat sub task"""
        alchemy_db.session.add(sub_task)
        alchemy_db.session.flush()
        return sub_task

    def find_by_id(self, sub_task_id: str) -> Optional[ChatSubTask]:
        """Find sub task by ID"""
        return ChatSubTask.query.filter(ChatSubTask.id == sub_task_id).first()

    def find_by_chat_id(self, chat_id: str) -> List[ChatSubTask]:
        """Find all sub tasks by chat ID"""
        return ChatSubTask.query.filter(ChatSubTask.chat_id == chat_id)\
            .order_by(ChatSubTask.created_time.desc()).all()

    def find_by_system_task_id(self, system_task_id: str) -> Optional[ChatSubTask]:
        """Find sub task by system task ID"""
        return ChatSubTask.query.filter(ChatSubTask.system_task_id == system_task_id).first()
    
    def find_by_tool_name_and_system_task_id(self, tool_name: str, system_task_id: str) -> Optional[ChatSubTask]:
        """Find sub task by tool name and system task ID"""
        return ChatSubTask.query.filter(ChatSubTask.tool_name == tool_name, ChatSubTask.system_task_id == system_task_id).first()

    def update(self, sub_task: ChatSubTask) -> ChatSubTask:
        """Update sub task record"""
        alchemy_db.session.merge(sub_task)
        alchemy_db.session.flush()
        return sub_task

    def update_status(self, sub_task_id: str, status: str, outputs: str = None, end_time=None) -> bool:
        """Update sub task status and outputs"""
        from datetime import datetime
        update_data = {'status': status}
        if outputs is not None:
            update_data['outputs'] = outputs
        if end_time is None and status in ['finished', 'failed']:
            update_data['end_time'] = datetime.now()
        elif end_time is not None:
            update_data['end_time'] = end_time
            
        result = ChatSubTask.query.filter(ChatSubTask.id == sub_task_id).update(update_data)
        alchemy_db.session.flush()
        return result > 0

    def update_system_task_id(self, sub_task_id: str, system_task_id: str) -> bool:
        """Update system task ID"""
        result = ChatSubTask.query.filter(ChatSubTask.id == sub_task_id).update({
            'system_task_id': system_task_id
        })
        alchemy_db.session.flush()
        return result > 0

    def delete_by_chat_id(self, chat_id: str) -> bool:
        """Delete all sub tasks by chat ID"""
        result = ChatSubTask.query.filter(ChatSubTask.chat_id == chat_id).delete()
        alchemy_db.session.flush()
        return result > 0

    def find_running_tasks(self) -> List[ChatSubTask]:
        """Find all running sub tasks"""
        return ChatSubTask.query.filter(ChatSubTask.status == 'running').all()


chat_sub_task_dao = ChatSubTaskDao()
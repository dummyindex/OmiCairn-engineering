from model.openai_logs import OpenaiLogs
from db import alchemy_db as db

class OpenaiLogsDao():

    def find_by_user_id(self, user_id, offset, limit):
        return OpenaiLogs.query.filter(
            OpenaiLogs.user_id == user_id
        ).order_by(OpenaiLogs.timestamp.desc()).offset(offset).limit(limit).all()
    
    def find_count_by_user_id(self, user_id):
        return OpenaiLogs.query.filter(
            OpenaiLogs.user_id == user_id
        ).count()
    
openai_logs_dao = OpenaiLogsDao()
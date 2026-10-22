from dao.openai_logs import openai_logs_dao
from dao.llm import llm_dao
from model.llm_consumption import LLMConsumption
from datetime import datetime

    # __tablename__ = 'llm_consumption'
    # id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    # prompt_tokens = db.Column(db.Integer, nullable=False)
    # completion_tokens = db.Column(db.Integer, nullable=False)
    # total_tokens = db.Column(db.Integer, nullable=False)
    # cost = db.Column(db.Numeric(10, 4), nullable=True)
    # created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # model = db.Column(db.String(255), nullable=False)
    # functionality = db.Column(db.String(255), nullable=False)
    # functionality_task_id = db.Column(db.BigInteger, nullable=False)
    # node_id = db.Column(db.BigInteger, nullable=False)
    # user_id = db.Column(db.BigInteger, nullable=False)

class GptService():
    def get_by_user_id(self, user_id, offset, limit):
        records = openai_logs_dao.find_by_user_id(user_id, offset, limit)
        total = openai_logs_dao.find_count_by_user_id(user_id)
        return records, total
    
    def record_consumption(self, consumption, user_id):
        now = datetime.now()
        prompt_tokens = consumption.get("prompt_tokens", 0)
        completion_tokens = consumption.get("completion_tokens", 0)
        total_tokens = consumption.get("total_tokens", 0)
        created_at = now
        model = consumption.get("model", "unknown")
        functionality = consumption.get("functionality", "unknown")
        functionality_task_id = consumption.get("functionality_task_id", -1)
        node_id = consumption.get("node_id", -1)
        
        consumption = LLMConsumption(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=None,  # Cost can be calculated later if needed
            created_at=created_at,
            model=model or "unknown",
            functionality=functionality,
            functionality_task_id=functionality_task_id,
            node_id=node_id,
            user_id=user_id
        )
        llm_dao.insert_consumption(consumption)
        return consumption

gpt_service = GptService()
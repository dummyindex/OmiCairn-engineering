from model.llm_consumption import LLMConsumption
from db import alchemy_db as db
from typing import List
from sqlalchemy import func, extract

class LlmDao:
    def insert_consumption(self, consumption: LLMConsumption):
        db.session.add(consumption)
        db.session.flush()

    def list_consumptions(self, user_id) -> List[LLMConsumption]:
        return db.session.query(LLMConsumption).filter(LLMConsumption.user_id == user_id).all()

    def get_llm_consumptions_by_month(self, user_id):
        """
        Get LLM consumption statistics grouped by year, month, functionality, and model
        Returns list of tuples: (year, month, functionality, model,
                                  total_tokens, prompt_tokens, completion_tokens,
                                  reasoning_tokens, total_cost)
        """
        results = db.session.query(
            extract('year', LLMConsumption.created_at).label('year'),
            extract('month', LLMConsumption.created_at).label('month'),
            LLMConsumption.functionality,
            LLMConsumption.model,
            func.sum(func.coalesce(LLMConsumption.total_tokens, 0)).label('total_tokens'),
            func.sum(func.coalesce(LLMConsumption.prompt_tokens, 0)).label('prompt_tokens'),
            func.sum(func.coalesce(LLMConsumption.completion_tokens, 0)).label('completion_tokens'),
            func.sum(func.coalesce(LLMConsumption.reasoning_tokens, 0)).label('reasoning_tokens'),
            func.sum(func.coalesce(LLMConsumption.cost, 0)).label('total_cost')
        ).filter(
            LLMConsumption.user_id == user_id
        ).group_by(
            extract('year', LLMConsumption.created_at),
            extract('month', LLMConsumption.created_at),
            LLMConsumption.functionality,
            LLMConsumption.model
        ).order_by(
            extract('year', LLMConsumption.created_at).desc(),
            extract('month', LLMConsumption.created_at).desc(),
            LLMConsumption.functionality,
            LLMConsumption.model
        ).all()
        return results

llm_dao = LlmDao()
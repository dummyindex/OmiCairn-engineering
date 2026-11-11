from model.llm_consumption import LLMConsumption
from model.analysis import Analysis
from model.dynamic_generation import DynamicGeneration
from model.agent_session import AgentSession
from model.computation_retry_process import ComputationRetryProcess
from model.task import Task
from model.computation import Computation
from sqlalchemy import and_, extract
from typing import List
from db import alchemy_db

class LLMConsumptionDao:

    def find_autogenie_consumptions_by_analysis(self, analysis_id, month=None) -> List[LLMConsumption]:
        query = alchemy_db.session.query(LLMConsumption).join(
            DynamicGeneration, LLMConsumption.functionality_task_id == DynamicGeneration.generation_id
        ).filter(
            and_(
                DynamicGeneration.analysis_id == analysis_id,
                LLMConsumption.functionality == 'Auto Genie'
            )
        )

        # If month is specified, filter by month
        if month:
            # Parse month string (e.g., "2025-01") to year and month
            year, month_num = map(int, month.split('-'))
            query = query.filter(
                and_(
                    extract('year', LLMConsumption.created_at) == year,
                    extract('month', LLMConsumption.created_at) == month_num
                )
            )

        return query.all()

    def find_bugfixer_consumptions_by_analysis(self, analysis_id, month=None) -> List[LLMConsumption]:
        query = alchemy_db.session.query(LLMConsumption).join(
            ComputationRetryProcess, LLMConsumption.functionality_task_id == ComputationRetryProcess.id
        ).filter(
            and_(
                ComputationRetryProcess.analysis_id == analysis_id,
                LLMConsumption.functionality == 'Bug Fixer'
            )
        )

        # If month is specified, filter by month
        if month:
            # Parse month string (e.g., "2025-01") to year and month
            year, month_num = map(int, month.split('-'))
            query = query.filter(
                and_(
                    extract('year', LLMConsumption.created_at) == year,
                    extract('month', LLMConsumption.created_at) == month_num
                )
            )

        return query.all()

    def find_agent_consumptions_by_analysis(self, analysis_id, month=None):
        query = alchemy_db.session.query(
            AgentSession.agent_type,
            AgentSession.id,
            AgentSession.created_time,
            LLMConsumption.model,
            LLMConsumption.functionality,
            LLMConsumption.prompt_tokens,
            LLMConsumption.completion_tokens,
            LLMConsumption.total_tokens,
            LLMConsumption.reasoning_tokens,
            LLMConsumption.user_id
        ).join(
            LLMConsumption, AgentSession.consumption_id == LLMConsumption.id
        ).join(
            Computation, AgentSession.current_computation_id == Computation.id
        ).join(
            Task, Computation.task_id == Task.id
        ).filter(
            Task.analysis_id == analysis_id
        )

        # If month is specified, filter by month
        if month:
            # Parse month string (e.g., "2025-01") to year and month
            year, month_num = map(int, month.split('-'))
            query = query.filter(
                and_(
                    extract('year', LLMConsumption.created_at) == year,
                    extract('month', LLMConsumption.created_at) == month_num
                )
            )

        return query.all()
    
    def find_node_interpreter_consumptions_by_analysis(self, analysis_id, month=None):
        query = LLMConsumption.query.filter(
            and_(
                LLMConsumption.functionality == 'Node Report Generation',
                LLMConsumption.functionality_task_id == analysis_id,
            )
        )

        # If month is specified, filter by month
        if month:
            # Parse month string (e.g., "2025-01") to year and month
            year, month_num = map(int, month.split('-'))
            query = query.filter(
                and_(
                    extract('year', LLMConsumption.created_at) == year,
                    extract('month', LLMConsumption.created_at) == month_num
                )
            )

        return query.all()
    
    def find_branch_report_consumptions_by_analysis(self, analysis_id, month=None):
        query = LLMConsumption.query.filter(
            and_(
                LLMConsumption.functionality.in_(["Branch Report Manual", "Branch Report Automation", "Figure Description Generation"]),
                LLMConsumption.functionality_task_id == analysis_id,
            )
        )

        # If month is specified, filter by month
        if month:
            # Parse month string (e.g., "2025-01") to year and month
            year, month_num = map(int, month.split('-'))
            query = query.filter(
                and_(
                    extract('year', LLMConsumption.created_at) == year,
                    extract('month', LLMConsumption.created_at) == month_num
                )
            )

        return query.all()

llm_consumption_dao = LLMConsumptionDao()
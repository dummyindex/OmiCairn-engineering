from model.dynamic_generation import DynamicGeneration
from model.node import Node
from model.dynamic_generation_session import DynamicGenerationSession
from model.dynamic_generation_branch import DynamicGenerationBranch
from model.llm_consumption import LLMConsumption
from db import alchemy_db
from sqlalchemy import and_, or_
from typing import List


class DynamicGenerationDao:
    def insert(self, dynamic_generation: DynamicGeneration) -> DynamicGeneration:
        alchemy_db.session.add(dynamic_generation)
        alchemy_db.session.flush()
        return dynamic_generation

    def insert_branch(self, dynamic_generation_branch: DynamicGenerationBranch) -> DynamicGenerationBranch:
        alchemy_db.session.add(dynamic_generation_branch)
        alchemy_db.session.flush()
        return dynamic_generation_branch

    def update(self, generation_id, attrs: dict):
        DynamicGeneration.query.filter(
            DynamicGeneration.generation_id == generation_id).update(attrs)
        alchemy_db.session.flush()

    def update_branch(self, branch_id, attrs: dict):
        DynamicGenerationBranch.query.filter(
            DynamicGenerationBranch.id == branch_id).update(attrs)
        alchemy_db.session.flush()

    def delete(self, generation_id) -> bool:
        """Delete a dynamic generation record by its ID."""
        result = DynamicGeneration.query.filter(
            DynamicGeneration.generation_id == generation_id
        ).delete()
        alchemy_db.session.flush()
        return result > 0

    def find_by_id(self, generation_id) -> DynamicGeneration:
        return DynamicGeneration.query.filter(DynamicGeneration.generation_id == generation_id).first()

    def find_by_analysis_id(self, analysis_id) -> List[DynamicGeneration]:
        return DynamicGeneration.query.filter(DynamicGeneration.analysis_id == analysis_id).all()

    def find_by_analysis_id_with_consumption(self, analysis_id) -> List[DynamicGeneration]:
        # Join the dynamic_generation, dynamic_generation_session and llm_consumption tables
        # dynamic_generation and dynamic_generation_session are joined on dynamic_generation_id (one-to-many)
        # dynamic_generation_session and llm_consumption are joined on consumption_id (one-to-one)
        # Count sessions and total llm_consumption tokens per dynamic_generation
        return alchemy_db.session.query(
            DynamicGeneration.generation_id,
            DynamicGeneration.analysis_id,
            DynamicGeneration.state,
            DynamicGeneration.created_time,
            DynamicGeneration.max_node,
            DynamicGeneration.max_branch,
            DynamicGeneration.previous_node_id,
            DynamicGeneration.rest_node_count,
            DynamicGeneration.max_debug,
            DynamicGeneration.user_request,
            alchemy_db.func.count(
                DynamicGenerationSession.id).label('session_count'),
            alchemy_db.func.sum(LLMConsumption.prompt_tokens).label(
                'total_prompt_tokens'),
            alchemy_db.func.sum(LLMConsumption.completion_tokens).label(
                'total_completion_tokens'),
            alchemy_db.func.sum(
                LLMConsumption.total_tokens).label('total_tokens')
        ).join(
            DynamicGenerationSession,
            DynamicGeneration.generation_id == DynamicGenerationSession.dynamic_generation_id,
            isouter=True
        ).join(
            LLMConsumption,
            DynamicGenerationSession.consumption_id == LLMConsumption.id,
            isouter=True
        ).filter(
            DynamicGeneration.analysis_id == analysis_id
        ).group_by(
            DynamicGeneration.generation_id
        ).all()

    def find_by_previous_node_id(self, previous_node_id) -> List[DynamicGeneration]:
        return DynamicGeneration.query.filter(DynamicGeneration.previous_node_id == previous_node_id).all()

    def find_by_generated_node_id(self, generated_node_id) -> DynamicGeneration:
        node: Node = Node.query.filter(Node.id == generated_node_id).first()
        if not node:
            return None
        return DynamicGeneration.query.filter(
            DynamicGeneration.generation_id == node.dynamic_generation_id
        ).first()

    def find_running_by_analysis_id(self, analysis_id) -> List[DynamicGeneration]:
        return DynamicGeneration.query.filter(
            and_(
                DynamicGeneration.analysis_id == analysis_id,
                DynamicGeneration.state == "running"
            )
        ).all()

    def find_running_branches_by_analysis_id(self, analysis_id) -> List[DynamicGenerationBranch]:
        generation_list = self.find_running_by_analysis_id(analysis_id)
        generation_id_list = [
            generation.generation_id for generation in generation_list]
        return DynamicGenerationBranch.query.filter(
            and_(
                DynamicGenerationBranch.dynamic_generation_id.in_(
                    generation_id_list),
                DynamicGenerationBranch.state == "running"
            )
        ).all()

    def find_by_state(self, state) -> List[DynamicGeneration]:
        return DynamicGeneration.query.filter(DynamicGeneration.state == state).all()

    def find_branches_by_state(self, state) -> List[DynamicGenerationBranch]:
        return DynamicGenerationBranch.query.filter(DynamicGenerationBranch.state == state).all()

    def find_by_previous_node_id(self, previous_node_id) -> List[DynamicGeneration]:
        return DynamicGeneration.query.filter(DynamicGeneration.previous_node_id == previous_node_id).all()

    def find_by_previous_computation_id(self, previous_computation_id) -> List[DynamicGeneration]:
        return DynamicGeneration.query.filter(DynamicGeneration.previous_computation_id == previous_computation_id).all()

    def find_by_previous_node_id_and_previous_computation_id(self, previous_node_id, previous_computation_id) -> List[DynamicGeneration]:
        return DynamicGeneration.query.filter(
            and_(
                DynamicGeneration.previous_node_id == previous_node_id,
                DynamicGeneration.previous_computation_id == previous_computation_id
            )
        ).all()

    def find_branches_by_dynamic_generation_id(self, generation_id) -> List[DynamicGenerationBranch]:
        return DynamicGenerationBranch.query.filter(DynamicGenerationBranch.dynamic_generation_id == generation_id).all()

    def find_branch_by_id(self, branch_id) -> DynamicGenerationBranch:
        return DynamicGenerationBranch.query.filter(DynamicGenerationBranch.id == branch_id).first()

    def find_branch_by_end_node_id(self, end_node_id) -> DynamicGenerationBranch:
        return DynamicGenerationBranch.query.filter(DynamicGenerationBranch.end_node_id == end_node_id).all()

    def insert_session(self, session: DynamicGenerationSession) -> DynamicGenerationSession:
        alchemy_db.session.add(session)
        alchemy_db.session.flush()
        return session

    def find_sessions_by_dynamic_generation_id(self, generation_id):
        return alchemy_db.session.query(
            DynamicGenerationSession.id,
            DynamicGenerationSession.dynamic_generation_id,
            DynamicGenerationSession.created_at,
            DynamicGenerationSession.source_node_id,
            DynamicGenerationSession.is_valid,
            DynamicGenerationSession.errors,
            LLMConsumption.model,
            LLMConsumption.prompt_tokens,
            LLMConsumption.completion_tokens,
            LLMConsumption.total_tokens,
            LLMConsumption.functionality,
            LLMConsumption.functionality_task_id
        ).join(
            LLMConsumption,
            DynamicGenerationSession.consumption_id == LLMConsumption.id
        ).filter(
            DynamicGenerationSession.dynamic_generation_id == generation_id
        ).all()

    def find_session_by_source_node_id_and_generation_id(self, source_node_id, generation_id):
        return DynamicGenerationSession.query.filter(
            and_(
                DynamicGenerationSession.source_node_id == source_node_id,
                DynamicGenerationSession.dynamic_generation_id == generation_id
            )
        ).first()
    
    def find_sessions_by_source_node_id_and_generation_id(self, source_node_id, generation_id):
        return DynamicGenerationSession.query.filter(
            and_(
                DynamicGenerationSession.source_node_id == source_node_id,
                DynamicGenerationSession.dynamic_generation_id == generation_id
            )
        ).all()

    def find_session_by_id(self, session_id):
        return DynamicGenerationSession.query.filter(
            DynamicGenerationSession.id == session_id
        ).first()


dynamic_generation_dao = DynamicGenerationDao()

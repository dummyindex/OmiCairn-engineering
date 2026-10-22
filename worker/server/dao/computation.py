from model.computation import Computation
from model.computation_user_relation import ComputationUserRelation
from model.computation_retry_process import ComputationRetryProcess
from model.bug_fixer_session import BugFixerSession
from model.llm_consumption import LLMConsumption
from model.fix_description import FixDescription
from datetime import datetime
from typing import List
from constants.computation import ComputationState
from db import alchemy_db as db
from sqlalchemy import or_
from sqlalchemy import text


class ComputationDao:
    def find(self, computation_id) -> Computation:
        return Computation.query.filter(Computation.id == computation_id).first()

    def find_by_computation_state(self, computation_state) -> List[Computation]:
        return Computation.query.filter(
            Computation.computation_state == computation_state
        ).all()

    def find_by_computation_state_list(self, computation_state_list) -> List[Computation]:
        return Computation.query.filter(
            Computation.computation_state.in_(computation_state_list)
        ).all()

    def find_first_queuing(self) -> Computation:
        return Computation.query.filter(
            Computation.computation_state == ComputationState.QUEUING.value
        ).order_by(
            Computation.created_time.asc()
        ).first()

    def find_by_job_ident(self, job_ident) -> Computation:
        return Computation.query.filter(
            Computation.job_ident == job_ident
        ).first()

    def find_latest_by_node_id(self, node_id) -> Computation:
        computation = Computation.query.filter(
            Computation.node_id == node_id
        ).order_by(
            Computation.created_time.desc()
        ).first()
        return computation

    def find_user_relation_by_computation_id_and_relation(self, computation_id, relation) -> List[ComputationUserRelation]:
        return ComputationUserRelation.query.filter(
            ComputationUserRelation.computation_id == computation_id,
            ComputationUserRelation.relation == relation
        ).all()

    def find_by_task_id(self, task_id) -> List[Computation]:
        computation = Computation.query.filter(
            Computation.task_id == task_id
        ).all()
        return computation

    def find_by_node_id(self, node_id) -> List[Computation]:
        computation = Computation.query.filter(
            Computation.node_id == node_id
        ).order_by(
            Computation.created_time.desc()
        ).all()
        return computation

    def find_by_retry_process_id(self, retry_process_id) -> List[Computation]:
        computation = Computation.query.filter(
            Computation.retry_process_id == retry_process_id
        ).order_by(
            Computation.created_time.desc()
        ).all()
        return computation

    def find_by_retry_process_id_list(self, retry_process_id_list) -> List[Computation]:
        computation = Computation.query.filter(
            Computation.retry_process_id.in_(retry_process_id_list)
        ).order_by(
            Computation.created_time.desc()
        ).all()
        return computation

    def find_by_task_id(self, task_id) -> List[Computation]:
        return Computation.query.filter(
            Computation.task_id == task_id
        ).order_by(
            Computation.created_time.desc()
        )

    def find_retry_process_by_node_id(self, node_id) -> List[ComputationRetryProcess]:
        return db.session.query(
            ComputationRetryProcess.id,
            ComputationRetryProcess.node_id,
            ComputationRetryProcess.new_node_id,
            ComputationRetryProcess.task_id,
            ComputationRetryProcess.state,
            ComputationRetryProcess.created_time,
            ComputationRetryProcess.analysis_id,
            ComputationRetryProcess.rest_retry,
            ComputationRetryProcess.max_retry,
            ComputationRetryProcess.user_prompt,
            db.func.count(BugFixerSession.id).label('session_count'),
            db.func.sum(LLMConsumption.prompt_tokens).label(
                'total_prompt_tokens'),
            db.func.sum(LLMConsumption.completion_tokens).label(
                'total_completion_tokens'),
            db.func.sum(LLMConsumption.total_tokens).label('total_tokens')
        ).join(
            BugFixerSession,
            BugFixerSession.retry_process_id == ComputationRetryProcess.id,
        ).join(
            LLMConsumption,
            LLMConsumption.id == BugFixerSession.consumption_id
        ).filter(
            or_(
                ComputationRetryProcess.node_id == node_id,
                ComputationRetryProcess.new_node_id == node_id
            )
        ).group_by(
            ComputationRetryProcess.id
        ).all()

    def find_retry_process_by_new_node_id(self, new_node_id) -> List[ComputationRetryProcess]:
        return db.session.query(
            ComputationRetryProcess.id,
            ComputationRetryProcess.node_id,
            ComputationRetryProcess.new_node_id,
            ComputationRetryProcess.task_id,
            ComputationRetryProcess.state,
            ComputationRetryProcess.created_time,
            ComputationRetryProcess.analysis_id,
            ComputationRetryProcess.rest_retry,
            ComputationRetryProcess.max_retry,
            ComputationRetryProcess.user_prompt,
            db.func.count(BugFixerSession.id).label('session_count'),
            db.func.sum(LLMConsumption.prompt_tokens).label(
                'total_prompt_tokens'),
            db.func.sum(LLMConsumption.completion_tokens).label(
                'total_completion_tokens'),
            db.func.sum(LLMConsumption.total_tokens).label('total_tokens')
        ).join(
            BugFixerSession,
            BugFixerSession.retry_process_id == ComputationRetryProcess.id,
        ).join(
            LLMConsumption,
            LLMConsumption.id == BugFixerSession.consumption_id
        ).filter(
            ComputationRetryProcess.new_node_id == new_node_id
        ).group_by(
            ComputationRetryProcess.id
        ).all()

    def find_retry_process_by_state(self, state) -> List[ComputationRetryProcess]:
        return ComputationRetryProcess.query.filter(
            ComputationRetryProcess.state == state
        ).order_by(
            ComputationRetryProcess.created_time.desc()
        ).all()

    def find_retry_process_list_by_analysis_id(self, analysis_id) -> List[ComputationRetryProcess]:
        # Join the computation_retry_process, bug_fixer_session and llm_consumption tables
        # computation_retry_process and bug_fixer_session are joined on computation_retry_process_id (one-to-many)
        # bug_fixer_session and llm_consumption are joined on consumption_id (one-to-one)
        # Count sessions and total llm_consumption tokens per computation_retry_process
        return db.session.query(
            ComputationRetryProcess.id,
            ComputationRetryProcess.node_id,
            ComputationRetryProcess.new_node_id,
            ComputationRetryProcess.task_id,
            ComputationRetryProcess.state,
            ComputationRetryProcess.created_time,
            ComputationRetryProcess.analysis_id,
            ComputationRetryProcess.rest_retry,
            ComputationRetryProcess.max_retry,
            ComputationRetryProcess.user_prompt,
            db.func.count(BugFixerSession.id).label('session_count'),
            db.func.sum(LLMConsumption.prompt_tokens).label(
                'total_prompt_tokens'),
            db.func.sum(LLMConsumption.completion_tokens).label(
                'total_completion_tokens'),
            db.func.sum(LLMConsumption.total_tokens).label('total_tokens')
        ).join(
            BugFixerSession,
            BugFixerSession.retry_process_id == ComputationRetryProcess.id,
        ).join(
            LLMConsumption,
            LLMConsumption.id == BugFixerSession.consumption_id
        ).filter(
            ComputationRetryProcess.analysis_id == analysis_id
        ).group_by(
            ComputationRetryProcess.id
        ).all()

    def update(self, computation_id, attrs):
        Computation.query.filter(
            Computation.id == computation_id).update(attrs)

    def insert(self, computation: Computation):
        computation.created_time = datetime.now()
        db.session.add(computation)
        db.session.flush()

    def insert_user_relation(self, computation_user_relation):
        db.session.add(computation_user_relation)
        db.session.flush()

    def find_retry_process_by_task_id(self, task_id) -> List[ComputationRetryProcess]:
        return ComputationRetryProcess.query.filter(
            ComputationRetryProcess.task_id == task_id
        ).all()

    def find_retry_process_by_id(self, retry_process_id) -> ComputationRetryProcess:
        return ComputationRetryProcess.query.filter(
            ComputationRetryProcess.id == retry_process_id
        ).first()

    def update_retry_process(self, retry_process_id, attrs):
        ComputationRetryProcess.query.filter(
            ComputationRetryProcess.id == retry_process_id).update(attrs)
        db.session.flush()

    def refresh_function_block_average_duration(self):
        db.session.execute(text("TRUNCATE function_block_average_duration"))
        db.session.execute(text(
            """
            INSERT INTO function_block_average_duration
            (function_block_version_id, avg_duration, system_env, computation_resource_configure)
            SELECT
                function_block_version_id,
                AVG(duration) as avg_duration,
                system_env,
                JSON_OBJECT(
                    'ram', COALESCE(JSON_EXTRACT(computation_resource_configure, '$.ram'), 0),
                    'vcpu', COALESCE(JSON_EXTRACT(computation_resource_configure, '$.vcpu'), 0),
                    'timeout', COALESCE(JSON_EXTRACT(computation_resource_configure, '$.timeout'), 0),
                    'gpu', COALESCE(JSON_EXTRACT(computation_resource_configure, '$.gpu'), 0)
                ) as computation_resource_configure
            FROM
                computation
            WHERE
                computation_state = 'finished'
            GROUP BY
                function_block_version_id,
                system_env,
                JSON_OBJECT(
                    'ram', COALESCE(JSON_EXTRACT(computation_resource_configure, '$.ram'), 0),
                    'vcpu', COALESCE(JSON_EXTRACT(computation_resource_configure, '$.vcpu'), 0),
                    'timeout', COALESCE(JSON_EXTRACT(computation_resource_configure, '$.timeout'), 0),
                    'gpu', COALESCE(JSON_EXTRACT(computation_resource_configure, '$.gpu'), 0)
                );
            """
        ))

        db.session.execute(text(
            """
            UPDATE node n
            JOIN function_block_average_duration fbad
                ON fbad.function_block_version_id = n.function_block_version_id
                AND fbad.system_env = n.system_env
                AND (
                    CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(fbad.computation_resource_configure, '$.gpu'), '0')) AS DECIMAL(10,2)) =
                    CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(n.computation_resource_configure, '$.gpu'), '0')) AS DECIMAL(10,2))
                )
                AND (
                    CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(fbad.computation_resource_configure, '$.ram'), '0')) AS DECIMAL(10,2)) =
                    CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(n.computation_resource_configure, '$.ram'), '0')) AS DECIMAL(10,2))
                )
                AND (
                    CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(fbad.computation_resource_configure, '$.vcpu'), '0')) AS DECIMAL(10,2)) =
                    CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(n.computation_resource_configure, '$.vcpu'), '0')) AS DECIMAL(10,2))
                )
                AND (
                    CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(fbad.computation_resource_configure, '$.timeout'), '0')) AS DECIMAL(10,2)) =
                    CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(n.computation_resource_configure, '$.timeout'), '0')) AS DECIMAL(10,2))
                )
            SET n.avg_duration = fbad.avg_duration;
            """
        ))

        db.session.commit()

    def insert_bug_fixer_session(self, session: BugFixerSession) -> BugFixerSession:
        db.session.add(session)
        db.session.flush()
        return session

    def find_bug_fixer_sessions_by_retry_process_id(self, retry_process_id):
        return db.session.query(
            BugFixerSession.id,
            BugFixerSession.retry_process_id,
            BugFixerSession.fixed_computation_id,
            BugFixerSession.created_at,
            BugFixerSession.node_id,
            BugFixerSession.is_valid,
            BugFixerSession.errors,
            BugFixerSession.start_time,
            BugFixerSession.end_time,
            BugFixerSession.type,
            BugFixerSession.dynamic_generation_id,
            LLMConsumption.model,
            LLMConsumption.prompt_tokens,
            LLMConsumption.completion_tokens,
            LLMConsumption.total_tokens,
            LLMConsumption.functionality,
            LLMConsumption.functionality_task_id
        ).join(
            LLMConsumption,
            LLMConsumption.id == BugFixerSession.consumption_id
        ).filter(
            BugFixerSession.retry_process_id == retry_process_id
        ).all()

    def find_bug_fixer_session_by_fixed_computation_id(self, fixed_computation_id):
        return db.session.query(BugFixerSession).filter(
            BugFixerSession.fixed_computation_id == fixed_computation_id
        ).first()

    def insert_fix_description(self, fix_description: FixDescription) -> FixDescription:
        """
        Insert a new fix description record
        
        :param fix_description: FixDescription instance
        :return: Inserted FixDescription instance
        """
        db.session.add(fix_description)
        db.session.flush()
        return fix_description

    def find_fix_descriptions_by_computation_id(self, computation_id) -> List[FixDescription]:
        """
        Find all fix descriptions for a given computation_id
        
        :param computation_id: The computation ID
        :return: List of FixDescription instances
        """
        return FixDescription.query.filter(
            FixDescription.computation_id == computation_id
        ).order_by(
            FixDescription.created_at.desc()
        ).all()


computation_dao = ComputationDao()

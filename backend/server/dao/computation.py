from typing import List
from model.computation import Computation
from constants.computation import ComputationState
from model.user import User
from model.node import Node
from model.computation_user_relation import ComputationUserRelation
from db import alchemy_db as db
from datetime import datetime, timedelta
from model.computation_retry_process import ComputationRetryProcess
from model.computation_file_size import ComputationFileSize
from model.analysis import Analysis
from model.task import Task
from sqlalchemy import and_, func, extract


class ComputationDao:

    def find_by_id(self, id) -> Computation:
        computation = Computation.query.filter(
            Computation.id == id
        ).first()
        return computation

    def find_by_node_id(self, node_id) -> List[Computation]:
        computation = Computation.query.filter(
            Computation.node_id == node_id
        ).order_by(
            Computation.created_time.desc()
        ).all()
        return computation
    
    def find_all_by_node_id_list(self, node_id_list) -> List[Computation]:
        computation = Computation.query.filter(
            Computation.node_id.in_(node_id_list)
        ).all()
        return computation

    def find_not_buried_by_node_id(self, node_id) -> List[Computation]:
        computation = Computation.query.filter(
            and_(
                Computation.node_id == node_id,
                Computation.buried == False
            )
        ).order_by(
            Computation.created_time.desc()
        ).all()
        return computation

    def find_latest_by_node_id(self, node_id) -> Computation:
        computation = Computation.query.filter(
            Computation.node_id == node_id
        ).order_by(
            Computation.created_time.desc()
        ).first()
        return computation

    
    def find_by_analysis_id(self, analysis_id) -> List[Computation]:
        """Find all computations for nodes in a specific analysis"""
        computations = Computation.query.join(
            Node, Computation.node_id == Node.id
        ).filter(
            Node.analysis_id == analysis_id
        ).order_by(
            Computation.created_time.desc()
        ).all()
        return computations

    def find_by_task_id(self, task_id) -> List[Computation]:
        computation = Computation.query.filter(
            Computation.task_id == task_id
        ).all()
        return computation
    
    def find_by_retry_process_id(self, retry_process_id) -> List[Computation]:
        computations = Computation.query.filter(
            Computation.retry_process_id == retry_process_id
        ).order_by(
            Computation.created_time.desc()
        ).all()
        return computations

    def find_by_task_id_and_state_list(self, task_id, state_list) -> List[Computation]:
        computation = Computation.query.filter(
            Computation.task_id == task_id,
            Computation.computation_state.in_(state_list)
        ).all()
        return computation

    def find_user_relation_by_user_id(self, user_id) -> List[ComputationUserRelation]:
        user_relation_list = ComputationUserRelation.query.filter(
            ComputationUserRelation.user_id == user_id
        ).all()
        return user_relation_list
    
    def find_not_buried_with_page(self, offset, limit) -> List[Computation]:
        computation = Computation.query.filter(
            Computation.buried == False
        ).offset(offset).limit(limit).all()
        return computation
    
    def find_by_result_data_id(self, result_data_id) -> Computation:
        computation = Computation.query.filter(
            Computation.result_data_id == result_data_id
        ).first()
        return computation
    
    def find_retry_process_by_id(self, retry_process_id) -> ComputationRetryProcess:
        retry_process = ComputationRetryProcess.query.filter(
            ComputationRetryProcess.id == retry_process_id
        ).first()
        return retry_process
    
    def find_retry_process_by_task_id(self, task_id) -> ComputationRetryProcess:
        retry_process = ComputationRetryProcess.query.filter(
            ComputationRetryProcess.task_id == task_id
        ).first()
        return retry_process
    
    def find_retry_process_by_node_id(self, node_id) -> ComputationRetryProcess:
        retry_process = ComputationRetryProcess.query.filter(
            ComputationRetryProcess.node_id == node_id
        ).first()
        return retry_process
    
    def find_retry_process_by_new_node_id(self, new_node_id) -> ComputationRetryProcess:
        retry_process = ComputationRetryProcess.query.filter(
            ComputationRetryProcess.new_node_id == new_node_id
        ).first()
        return retry_process
    
    def find_retry_process_by_analysis_id(self, analysis_id) -> List[ComputationRetryProcess]:
        retry_process = ComputationRetryProcess.query.filter(
            ComputationRetryProcess.analysis_id == analysis_id
        ).all()
        return retry_process
    
    def find_by_node_id_list(self, node_id_list, limit, offset) -> List[Computation]:
        computation = Computation.query.filter(
            Computation.node_id.in_(node_id_list)
        ).offset(offset).limit(limit).all()
        return computation
    
    def find_user_relation_by_computation_id_list(self, computation_id_list, relation) -> List[ComputationUserRelation]:
        if relation is None:
            user_relation_list = ComputationUserRelation.query.filter(
                ComputationUserRelation.computation_id.in_(computation_id_list)
            ).all()
            return user_relation_list
        else:
            user_relation_list = ComputationUserRelation.query.filter(
                ComputationUserRelation.computation_id.in_(computation_id_list),
                ComputationUserRelation.relation == relation
            ).all()
            return user_relation_list

    def find_done_unrecorded_size_list(self) -> List[Computation]:
        computation = Computation.query.filter(
            and_(
                Computation.s3_size_recorded == False,
                Computation.computation_state.in_([ComputationState.FINISHED.value, ComputationState.FAILED.value])
            )
        ).all()
        return computation

    def insert(self, computation) -> Computation:
        db.session.add(computation)
        db.session.flush()
        return computation

    def insert_list(self, computation_list) -> List[Computation]:
        db.session.bulk_save_objects(computation_list)
        db.session.flush()
        return computation_list

    def insert_computation_file_size(self, computation_file_size: ComputationFileSize) -> ComputationFileSize:
        db.session.add(computation_file_size)
        db.session.flush()
        return computation_file_size

    def update(self, computation_id, attrs):
        Computation.query.filter(
            Computation.id == computation_id
        ).update(attrs)
        db.session.flush()

    def update_by_id_list(self, id_list, attrs):
        Computation.query.filter(
            Computation.id.in_(id_list)
        ).update(attrs)
        db.session.flush()

    def update_by_task_id(self, task_id, attrs):
        Computation.query.filter(
            Computation.task_id == task_id
        ).update(attrs)
        db.session.flush()

    def delete(self, computation_id):
        Computation.query.filter(
            Computation.id == computation_id
        ).delete()

    def delete_by_node_id(self, node_id):
        Computation.query.filter(
            Computation.node_id == node_id
        ).delete()

    def delete_by_id_list(self, id_list):
        Computation.query.filter(
            Computation.id.in_(id_list)
        ).delete()

    def find_computation_file_size_list_by_user_id(self, user_id) -> List[ComputationFileSize]:
        file_size_list = db.session.query(ComputationFileSize).join(
            ComputationUserRelation, ComputationUserRelation.computation_id == ComputationFileSize.computation_id
        ).filter(
            ComputationUserRelation.user_id == user_id
        ).all()
        return file_size_list
    
    def find_computation_file_size_list_by_analysis_id(self, analysis_id, month=None) -> List[ComputationFileSize]:
        query = db.session.query(
            ComputationFileSize
        ).join(
            Computation, Computation.id == ComputationFileSize.computation_id
        ).join(
            Task, Task.id == Computation.task_id
        ).filter(
            Task.analysis_id == analysis_id
        )

        # If month is specified, filter by month
        if month:
            # Parse month string (e.g., "2025-01") to year and month
            year, month_num = map(int, month.split('-'))
            query = query.filter(
                and_(
                    extract('year', ComputationFileSize.created_time) == year,
                    extract('month', ComputationFileSize.created_time) == month_num
                )
            )

        return query.all()
    
    def find_by_user_id(self, user_id) -> List[Computation]:
        computation_list = db.session.query(Computation).join(
            ComputationUserRelation, ComputationUserRelation.computation_id == Computation.id
        ).filter(
            ComputationUserRelation.user_id == user_id
        ).all()
        return computation_list
    
    def find_by_analysis_id_and_month(self, analysis_id, month=None) -> List[Computation]:
        query = db.session.query(Computation).join(
            Task, Task.id == Computation.task_id
        ).filter(
            Task.analysis_id == analysis_id
        )

        if month:
            # Parse month string (e.g., "2025-01") to year and month
            year, month_num = map(int, month.split('-'))
            query = query.filter(
                and_(
                    extract('year', Computation.created_time) == year,
                    extract('month', Computation.created_time) == month_num
                )
            )

        return query.all()

computation_dao = ComputationDao()

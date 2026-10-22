from db import alchemy_db as db
from model.task_node_relation import TaskNodeRelation
from constants.task_node_relation import TaskNodeRelationType
from typing import List
from sqlalchemy import and_


class TaskNodeRelationDao:
    def insert_list(self, task_node_relation_list: List[TaskNodeRelation]):
        db.session.bulk_save_objects(task_node_relation_list)
        db.session.flush()
        return task_node_relation_list

    def find_by_task_id(self, task_id) -> List[TaskNodeRelation]:
        return TaskNodeRelation.query.filter(TaskNodeRelation.task_id == task_id).all()

    def find_latest_by_node_id(self, node_id) -> TaskNodeRelation:
        return TaskNodeRelation.query.filter(
            TaskNodeRelation.node_id == node_id
        ).order_by(TaskNodeRelation.created_time.desc()).first()

    def find_by_task_id_and_relation_type(self, task_id, relation_type) -> List[TaskNodeRelation]:
        return TaskNodeRelation.query.filter(
            and_(
                TaskNodeRelation.task_id == task_id,
                TaskNodeRelation.relation_type == relation_type
            )
        ).all()

    def find_roots_by_task_id(self, task_id) -> List[TaskNodeRelation]:
        return TaskNodeRelation.query.filter(
            and_(
                TaskNodeRelation.task_id == task_id,
                TaskNodeRelation.is_root == True
            )
        ).all()

    def find_leaves_by_task_id(self, task_id) -> List[TaskNodeRelation]:
        return TaskNodeRelation.query.filter(
            and_(
                TaskNodeRelation.task_id == task_id,
                TaskNodeRelation.is_leaf == True
            )
        ).all()

    def find_by_task_id_and_node_id(self, task_id, node_id) -> TaskNodeRelation:
        return TaskNodeRelation.query.filter(
            and_(
                TaskNodeRelation.task_id == task_id,
                TaskNodeRelation.node_id == node_id
            )
        ).first()

    def find_by_node_id(self, node_id) -> List[TaskNodeRelation]:
        return TaskNodeRelation.query.filter(TaskNodeRelation.node_id == node_id).all()

    def update(self, task_node_relation_id, attrs: dict):
        TaskNodeRelation.query.filter(
            TaskNodeRelation.id == task_node_relation_id).update(attrs)
        db.session.flush()

    def update_by_node_id_and_task_id(self, node_id, task_id, attrs: dict):
        TaskNodeRelation.query.filter(
            and_(
                TaskNodeRelation.node_id == node_id,
                TaskNodeRelation.task_id == task_id
            )
        ).update(attrs)
        db.session.flush()

    def delete_by_task_id_and_node_id_list(self, task_id, node_id_list):
        TaskNodeRelation.query.filter(
            and_(
                TaskNodeRelation.task_id == task_id,
                TaskNodeRelation.node_id.in_(node_id_list)
            )
        ).delete()
        db.session.flush()


task_node_relation_dao = TaskNodeRelationDao()

from db import alchemy_db as db
from model.task_edge_relation import TaskEdgeRelation
from typing import List
from sqlalchemy import and_


class TaskEdgeRelationDao:

    def insert_list(self, task_edge_relation_list: List[TaskEdgeRelation]):
        db.session.bulk_save_objects(task_edge_relation_list)
        db.session.flush()
        return task_edge_relation_list

    def find_by_task_id(self, task_id) -> List[TaskEdgeRelation]:
        return TaskEdgeRelation.query.filter(TaskEdgeRelation.task_id == task_id).all()

    def find_by_task_id_and_edge_id(self, task_id, edge_id) -> TaskEdgeRelation:
        return TaskEdgeRelation.query.filter(
            and_(
                TaskEdgeRelation.task_id == task_id,
                TaskEdgeRelation.edge_id == edge_id
            )
        ).first()
    
    def delete_by_task_id_and_edge_id_list(self, task_id, edge_id_list):
        TaskEdgeRelation.query.filter(
            and_(
                TaskEdgeRelation.task_id == task_id,
                TaskEdgeRelation.edge_id.in_(edge_id_list)
            )
        ).delete()
        db.session.flush()

task_edge_relation_dao = TaskEdgeRelationDao()

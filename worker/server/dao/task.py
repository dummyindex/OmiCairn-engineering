from db import alchemy_db
from model.task import Task
from model.task_user_relation import TaskUserRelation
from typing import List
from constants.task import TaskState
from sqlalchemy import and_


class TaskDao:
    def insert(self, task: Task) -> Task:
        alchemy_db.session.add(task)
        alchemy_db.session.flush()
        return task

    def insert_user_relation(self, task_user_relation: TaskUserRelation) -> TaskUserRelation:
        alchemy_db.session.add(task_user_relation)
        alchemy_db.session.flush()
        return task_user_relation

    def find_by_id(self, task_id) -> Task:
        return Task.query.filter(Task.id == task_id).first()

    def find_user_relation_by_task_id(self, task_id) -> List[TaskUserRelation]:
        return TaskUserRelation.query.filter(TaskUserRelation.task_id == task_id).all()

    def find_by_ids_and_state(self, task_ids, state) -> List[Task]:
        return Task.query.filter(
            and_(
                Task.id.in_(task_ids),
                Task.state == state
            )
        ).all()

    def find_by_state(self, state) -> List[Task]:
        return Task.query.filter(Task.state == state).all()

    def find_by_analysis_id(self, analysis_id) -> List[Task]:
        return Task.query.filter(Task.analysis_id == analysis_id).all()

    def find_user_relation_by_task_id_and_user_ids(self, task_id, user_ids) -> List[TaskUserRelation]:
        return TaskUserRelation.query.filter(
            and_(
                TaskUserRelation.task_id == task_id,
                TaskUserRelation.user_id.in_(user_ids)
            )
        ).all()

    def update(self, task_id, update_dict):
        Task.query.filter(Task.id == task_id).update(update_dict)


task_dao = TaskDao()

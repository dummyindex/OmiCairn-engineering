from model.node import Node
from model.node_user_relation import NodeUserRelation
from model.computation import Computation
from model.analysis import Analysis
from model.function_block_v1 import FunctionBlockV1
from model.function_block_version_v1 import FunctionBlockVersionV1
from model.data_vitessce import DataVitessce
from model.task_user_relation import TaskUserRelation
from db import alchemy_db
from sqlalchemy import and_
from sqlalchemy import text
from typing import List
import json
from model.node import Node
from model.task import Task
from model.task_node_relation import TaskNodeRelation
from model.task_edge_relation import TaskEdgeRelation
from model.edge import Edge
from log.logger_factory import logger_factory

logger = logger_factory.create_logger(__name__)

class TaskDao:
    def find_by_analysis_id(self, analysis_id) -> List[Task]:
        tasks = Task.query.filter(Task.analysis_id == analysis_id).all()
        return tasks

    def delete_task_node_relation_by_node_id(self, node_id: int):
        TaskNodeRelation.query.filter(TaskNodeRelation.node_id == node_id).delete()
        alchemy_db.session.flush()

    def delete_task_edge_relation_by_edge_id(self, edge_id: int):
        TaskEdgeRelation.query.filter(TaskEdgeRelation.edge_id == edge_id).delete()
        alchemy_db.session.flush()

task_dao = TaskDao()
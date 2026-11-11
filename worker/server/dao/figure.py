from model.figure import Figure
from model.task_edge_relation import TaskEdgeRelation
from db import alchemy_db
from sqlalchemy import and_, or_
from typing import List


class FigureDao:
    def find_by_computation_id(self, computation_id) -> List[Figure]:
        return Figure.query.filter(Figure.computation_id == computation_id).all()


figure_dao = FigureDao()

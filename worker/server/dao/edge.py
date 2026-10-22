from model.edge import Edge
from model.task_edge_relation import TaskEdgeRelation
from db import alchemy_db
from sqlalchemy import and_, or_
from typing import List


class EdgeDao:
    def insert(self, edge: Edge) -> Edge:
        alchemy_db.session.add(edge)
        alchemy_db.session.flush()
        return edge

    def update(self, edge_id, attrs: dict):
        Edge.query.filter(Edge.id == edge_id).update(attrs)
        alchemy_db.session.flush()

    def find_by_id(self, edge_id) -> Edge:
        return Edge.query.filter(Edge.id == edge_id).first()

    def find_by_analysis_id(self, analysis_id) -> List[Edge]:
        return Edge.query.filter(Edge.analysis_id == analysis_id).all()

    def find_by_id_list(self, edge_id_list) -> List[Edge]:
        return Edge.query.filter(Edge.id.in_(edge_id_list)).all()

    def find_by_source_node_id(self, source_node_id) -> List[Edge]:
        return Edge.query.filter(
            Edge.source_node_id == source_node_id
        ).all()

    def find_by_target_node_id(self, target_node_id) -> List[Edge]:
        return Edge.query.filter(
            Edge.target_node_id == target_node_id
        ).all()

    def find_by_target_node_id_list(self, target_node_id_list) -> List[Edge]:
        return Edge.query.filter(
            Edge.target_node_id.in_(target_node_id_list)
        ).all()

    def find_by_source_and_target_node_id(
        self,
        source_node_id,
        target_node_id
    ) -> Edge:
        return Edge.query.filter(
            and_(
                Edge.source_node_id == source_node_id,
                Edge.target_node_id == target_node_id
            )
        ).first()

    def find_all_front_edges(self, node_id) -> List[Edge]:
        previous_edge_path = self.find_by_target_node_id(node_id)
        index = 0
        while index < len(previous_edge_path):
            previous_edge = previous_edge_path[index]
            previous_edge_path += self.find_by_target_node_id(
                previous_edge.source_node_id
            )
            index += 1
        return previous_edge_path

    def find_all_after_edges(self, node_id) -> List[Edge]:
        next_edge_path = self.find_by_source_node_id(node_id)
        index = 0
        while index < len(next_edge_path):
            next_edge = next_edge_path[index]
            next_edge_path += self.find_by_source_node_id(
                next_edge.target_node_id
            )
            index += 1
        return next_edge_path

    def find_next_edges_in_task(self, node_id, task_id) -> List[Edge]:
        return alchemy_db.session.query(
            Edge
        ).join(
            TaskEdgeRelation,
            Edge.id == TaskEdgeRelation.edge_id
        ).filter(
            and_(
                Edge.source_node_id == node_id,
                TaskEdgeRelation.task_id == task_id
            )
        ).all()


edge_dao = EdgeDao()

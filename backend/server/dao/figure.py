from model.figure import Figure
from db import alchemy_db as db
from typing import List

class FigureDao:
    def find_by_computation_id(self, computation_id) -> List[Figure]:
        figure_list = Figure.query.filter(
            Figure.computation_id==computation_id
        ).all()
        return figure_list
    
    def find_by_node_id(self, node_id):
        figure_list = Figure.query.filter(
            Figure.node_id==node_id
        ).all()
        return figure_list
    
    def find_by_computation_id_list(self, computation_id_list) -> List[Figure]:
        figure_list = Figure.query.filter(
            Figure.computation_id.in_(computation_id_list)
        ).all()
        return figure_list
    
    def find_by_node_id_list(self, node_id_list):
        figure_list = Figure.query.filter(
            Figure.node_id.in_(node_id_list)
        ).all()
        return figure_list
    
    def insert(self, figure: Figure):
        db.session.add(figure)
        db.session.commit()
        return figure
    
figure_dao = FigureDao()
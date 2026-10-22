from model.visualizer import Visualizer
from typing import List
from db import alchemy_db as db


class VisualizerDao:
    def insert(self, visualizer: Visualizer):
        db.session.add(visualizer)
        db.session.flush()
        return visualizer

    def find_by_analysis_id(self, analysis_id):
        return Visualizer.query.filter(Visualizer.analysis_id == analysis_id).all()

    def find_by_original_node_id(self, original_node_id):
        return Visualizer.query.filter(Visualizer.original_node_id == original_node_id).all()

    def find_by_original_computation_id(self, original_computation_id):
        return Visualizer.query.filter(Visualizer.original_computation_id == original_computation_id).all()

    def find(self, id) -> Visualizer:
        return Visualizer.query.filter(Visualizer.id == id).first()

    def update(self, id, attrs):
        Visualizer.query.filter(Visualizer.id == id).update(attrs)
        db.session.flush()

    def find_by_state(self, state) -> List[Visualizer]:
        return Visualizer.query.filter(Visualizer.state == state).all()


visualizer_dao = VisualizerDao()

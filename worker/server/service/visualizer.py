from dao.visualizer import visualizer_dao
from model.visualizer import Visualizer
from datetime import datetime
from dao.node import node_dao
from dao.edge import edge_dao
from dao.computation import computation_dao
from db import alchemy_db as db
from sss.porter_factory import PorterFactory
import os
from tool.llm_interface import LlmInterface
from log.logger_factory import LoggerFactory
from constants.visualizer import VisualizerState
import json
from tool.conn_to_main_server import copy_node

logger = LoggerFactory.get_logger("VisualizerService")


class VisualizerService:
    def create(self, original_node_id, max_count, user_prompt, computation_resource_configure, generation_mode, user_id, llm_model):
        now = datetime.now()
        node = node_dao.find_by_id(original_node_id)
        computation = computation_dao.find_latest_by_node_id(original_node_id)
        if not computation:
            raise Exception("Computation not found")
        visualizer = Visualizer(
            analysis_id=node.analysis_id,
            original_node_id=node.id,
            original_computation_id=computation.id,
            max_count=max_count,
            rest_count=max_count,
            user_prompt=user_prompt,
            state=VisualizerState.RUNNING.value,
            user_id=user_id,
            created_time=now,
            generation_mode=generation_mode,
            computation_resource_configure=computation_resource_configure,
            llm_model=llm_model
        )
        visualizer_dao.insert(visualizer)
        return visualizer

    def get(self, visualizer_id):
        return visualizer_dao.find(visualizer_id)

    def list_by_analysis_id(self, analysis_id):
        return visualizer_dao.find_by_analysis_id(analysis_id)

    def report_step_done(self, visualizer_id, node_id, satisfied):
        node_dao.update(node_id, {
            "visualizer_locked": False,
        })
        if satisfied:
            visualizer = visualizer_dao.find(visualizer_id)
            if visualizer is None:
                raise Exception("Visualizer not found")
            original_node = node_dao.find_by_id(
                visualizer.original_node_id)
            if original_node is None:
                raise Exception("Original node not found")
            before_edges = edge_dao.find_all_front_edges(
                original_node.id)
            node_dao.update_by_id_list(
                [edge.source_node_id for edge in before_edges], {
                    "visualizer_locked": False,
                }
            )
            visualizer_dao.update(visualizer_id, {
                "state": "finished",
            })
        else:
            visualizer_dao.update(visualizer_id, {
                "state": "running"
            })

    def edit(self, visualizer_id, attrs):
        visualizer = visualizer_dao.find(visualizer_id)
        if visualizer is None:
            raise Exception("Visualizer not found")
        visualizer_dao.update(visualizer_id, attrs)

    def stop(self, visualizer_id):
        visualizer = visualizer_dao.find(visualizer_id)
        if visualizer is None:
            raise Exception("Visualizer not found")
        visualizer_dao.update(visualizer_id, {
            "state": VisualizerState.STOPPED.value
        })
        node_dao.update(visualizer.original_node_id, {
            "visualizer_locked": False,
        })
        before_edges = edge_dao.find_all_front_edges(
            visualizer.original_node_id)
        node_dao.update_by_id_list(
            [edge.source_node_id for edge in before_edges], {
                "visualizer_locked": False,
            }
        )

    def stop_all(self):
        running_visualizers = visualizer_dao.find_by_state(
            VisualizerState.RUNNING.value)
        for visualizer in running_visualizers:
            self.stop(visualizer.id)


visualizer_service = VisualizerService()

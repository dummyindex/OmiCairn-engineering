from typing import List
from model.edge import Edge


class FlowTool:
    @staticmethod
    def get_root_ids_by_edge_list(edge_list: List[Edge], node_id_list: List[int]):
        node_id_2_be_target_count_map = { node_id: 0 for node_id in node_id_list }
        for edge in edge_list:
            node_id_2_be_target_count_map[edge.target_node_id] += 1
        header_id_list = [
            key for key, value
            in node_id_2_be_target_count_map.items()
            if value == 0
        ]
        return header_id_list

    @staticmethod
    def get_leaf_ids_by_edge_list(edge_list: List[Edge], node_id_list: List[int]):
        node_id_2_be_source_count_map = { node_id: 0 for node_id in node_id_list }
        for edge in edge_list:
            node_id_2_be_source_count_map[edge.source_node_id] += 1
        tail_id_list = [
            key for key, value
            in node_id_2_be_source_count_map.items()
            if value == 0
        ]
        return tail_id_list

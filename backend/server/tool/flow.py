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

    @staticmethod
    def check_edge_cycle(edge_list: List[Edge], new_edge_source_id: int, new_edge_target_id: int):
        source_node_id_2_target_node_id_list_map = {}
        for edge in edge_list:
            if edge.source_node_id not in source_node_id_2_target_node_id_list_map:
                source_node_id_2_target_node_id_list_map[edge.source_node_id] = []
            source_node_id_2_target_node_id_list_map[edge.source_node_id].append(edge.target_node_id)
        # BFS: check whether new_source_id is reachable from new_edge_target_id
        queue = [new_edge_target_id]
        while len(queue) > 0:
            current_node_id = queue.pop(0)
            if current_node_id == new_edge_source_id:
                return True
            if current_node_id in source_node_id_2_target_node_id_list_map:
                queue.extend(source_node_id_2_target_node_id_list_map[current_node_id])
        return False
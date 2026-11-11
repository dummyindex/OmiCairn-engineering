from model.pipeline_template import PipelineTemplate
from typing import List
from model.node import Node
from model.edge import Edge
from dto import Dto

class PipelineTemplateImportResult(Dto):
    def __init__(
            self, 
            new_node_list: List[Node],
            new_edge_list: List[Edge],
        ):
        self.new_node_list = new_node_list
        self.new_edge_list = new_edge_list
    
    def to_dict(self):
        return {
            'newNodeList': [node.to_dict() for node in self.new_node_list],
            'newEdgeList': [edge.to_dict() for edge in self.new_edge_list]
        }
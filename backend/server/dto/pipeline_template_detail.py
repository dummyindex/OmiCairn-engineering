from dto import Dto
from model.pipeline_template import PipelineTemplate
from model.pipeline_template_node import PipelineTemplateNode
from model.pipeline_template_edge import PipelineTemplateEdge
from typing import List


class PipelineTemplateDetailDto(Dto):
    def __init__(
            self,
            pt: PipelineTemplate,
            pt_node_list: List[PipelineTemplateNode],
            pt_edge_list: List[PipelineTemplateEdge],
            group_name: str
    ):
        super().__init__()
        self.pt = pt
        self.pt_node_list = pt_node_list
        self.pt_edge_list = pt_edge_list
        self.group_name = group_name

    def to_dict(self):
        pipeline_template_dict = self.pt.to_dict()
        pipeline_template_dict['ptNodeList'] = [
            pt_node.to_dict() for pt_node in self.pt_node_list
        ]
        pipeline_template_dict['ptEdgeList'] = [
            pt_edge.to_dict() for pt_edge in self.pt_edge_list
        ]
        return pipeline_template_dict

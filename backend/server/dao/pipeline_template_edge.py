from typing import List
from db import alchemy_db
from model.pipeline_template_edge import PipelineTemplateEdge


class PipelineTemplateEdgeDao:
    def insert_list(self, pt_edge_list: List[PipelineTemplateEdge]):
        alchemy_db.session.add_all(pt_edge_list)
        alchemy_db.session.flush()
        return pt_edge_list

    def update(self, pt_edge_id, attrs: dict):
        PipelineTemplateEdge.query.filter(
            PipelineTemplateEdge.id == pt_edge_id
        ).update(attrs)
        alchemy_db.session.flush()

    def delete_by_pt_id(self, pt_id):
        PipelineTemplateEdge.query.filter(
            PipelineTemplateEdge.pipeline_template_id == pt_id
        ).delete()

    def delete_by_pt_id_list(self, pt_id_list):
        PipelineTemplateEdge.query.filter(
            PipelineTemplateEdge.pipeline_template_id.in_(pt_id_list)
        ).delete(synchronize_session=False)

    def find_by_pt_id(self, pt_id) -> List[PipelineTemplateEdge]:
        return PipelineTemplateEdge.query.filter(
            PipelineTemplateEdge.pipeline_template_id == pt_id
        ).all()


pipeline_template_edge_dao = PipelineTemplateEdgeDao()

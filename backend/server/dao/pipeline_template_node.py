from typing import List
from db import alchemy_db
from model.pipeline_template_node import PipelineTemplateNode


class PipelineTemplateNodeDao:
    def insert_list(self, pt_node_list: List[PipelineTemplateNode]):
        alchemy_db.session.add_all(pt_node_list)
        alchemy_db.session.flush()
        return pt_node_list

    def update(self, pt_node_id, attrs: dict):
        PipelineTemplateNode.query.filter(
            PipelineTemplateNode.id == pt_node_id
        ).update(attrs)
        alchemy_db.session.flush()

    def delete_by_pt_id(self, pt_id):
        PipelineTemplateNode.query.filter(
            PipelineTemplateNode.pipeline_template_id == pt_id
        ).delete()

    def delete_by_pt_id_list(self, pt_id_list):
        PipelineTemplateNode.query.filter(
            PipelineTemplateNode.pipeline_template_id.in_(pt_id_list)
        ).delete(synchronize_session=False)

    def find_by_pt_id(self, pt_id) -> List[PipelineTemplateNode]:
        return PipelineTemplateNode.query.filter(
            PipelineTemplateNode.pipeline_template_id == pt_id
        ).all()


pipeline_template_node_dao = PipelineTemplateNodeDao()

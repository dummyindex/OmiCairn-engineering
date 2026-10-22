from db import alchemy_db as db


class PipelineTemplateEdge(db.Model):
    __tablename__ = 'pipeline_template_edge'
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    created_time = db.Column(db.DateTime)
    source_pt_node_id = db.Column(db.BigInteger)
    target_pt_node_id = db.Column(db.BigInteger)
    pipeline_template_id = db.Column(db.BigInteger)

    def to_dict(self):
        pipeline_template_edge_attrs_dict = dict()
        pipeline_template_edge_attrs_dict["id"] = self.id
        pipeline_template_edge_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000
        pipeline_template_edge_attrs_dict["sourcePtNodeId"] = self.source_pt_node_id
        pipeline_template_edge_attrs_dict["targetPtNodeId"] = self.target_pt_node_id
        pipeline_template_edge_attrs_dict["pipelineTemplateId"] = self.pipeline_template_id
        return pipeline_template_edge_attrs_dict

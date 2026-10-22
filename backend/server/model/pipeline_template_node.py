from db import alchemy_db as db
import json

class PipelineTemplateNode(db.Model):
    __tablename__ = 'pipeline_template_node'
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    created_time = db.Column(db.DateTime)
    function_block_id = db.Column(db.BigInteger)
    function_block_version_id = db.Column(db.BigInteger)
    computation_params = db.Column(db.Text)
    pipeline_template_id = db.Column(db.BigInteger)
    name = db.Column(db.String(255))
    relative_x = db.Column(db.Double)
    relative_y = db.Column(db.Double)
    computation_resource_configure = db.Column(db.String(50))

    def to_dict(self):
        pipeline_template_node_attrs_dict = dict()
        pipeline_template_node_attrs_dict["id"] = self.id
        pipeline_template_node_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000
        pipeline_template_node_attrs_dict["functionBlockId"] = self.function_block_id
        pipeline_template_node_attrs_dict["functionBlockVersionId"] = self.function_block_version_id
        pipeline_template_node_attrs_dict["computationParams"] = self.computation_params
        pipeline_template_node_attrs_dict["pipelineTemplateId"] = self.pipeline_template_id
        pipeline_template_node_attrs_dict["name"] = self.name
        pipeline_template_node_attrs_dict["relativeX"] = self.relative_x
        pipeline_template_node_attrs_dict["relativeY"] = self.relative_y
        pipeline_template_node_attrs_dict["computationResourceConfigure"] = json.loads(self.computation_resource_configure) if self.computation_resource_configure is not None else None
        return pipeline_template_node_attrs_dict

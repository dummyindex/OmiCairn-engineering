from db import alchemy_db as db


class PipelineTemplate(db.Model):
    __tablename__ = "pipeline_template"
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    created_time = db.Column(db.DateTime)
    name = db.Column(db.String(255))
    description = db.Column(db.Text)
    group_name = db.Column(db.String(200))

    def to_dict(self):
        pipeline_template_attrs_dict = dict()
        pipeline_template_attrs_dict["id"] = self.id
        pipeline_template_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000
        pipeline_template_attrs_dict["name"] = self.name
        pipeline_template_attrs_dict["description"] = self.description
        pipeline_template_attrs_dict["groupName"] = self.group_name
        return pipeline_template_attrs_dict

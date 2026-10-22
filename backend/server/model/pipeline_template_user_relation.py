from db import alchemy_db as db

class PipelineTemplateUserRelation(db.Model):
    __tablename__ = 'pipeline_template_user_relation'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    pipeline_template_id = db.Column(db.BigInteger)
    user_id = db.Column(db.BigInteger)
    relation = db.Column(db.String(100))
    permission = db.Column(db.String(100))

    def to_dict(self):
        pipeline_template_user_relation_attrs_dict = dict()
        pipeline_template_user_relation_attrs_dict["id"] = self.id
        pipeline_template_user_relation_attrs_dict["pipelineTemplateId"] = self.pipeline_template_id
        pipeline_template_user_relation_attrs_dict["userId"] = self.user_id
        pipeline_template_user_relation_attrs_dict["relation"] = self.relation
        pipeline_template_user_relation_attrs_dict["permission"] = self.permission
        return pipeline_template_user_relation_attrs_dict

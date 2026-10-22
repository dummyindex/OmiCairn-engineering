from db import alchemy_db

class AnalysisUserRelation(alchemy_db.Model):
    __tablename__ = 'analysis_user_relation'
    id = alchemy_db.Column(alchemy_db.BigInteger, primary_key=True, autoincrement=True)
    analysis_id = alchemy_db.Column(alchemy_db.BigInteger, nullable=False)
    user_id = alchemy_db.Column(alchemy_db.BigInteger, nullable=False)
    relation = alchemy_db.Column(alchemy_db.String(100), nullable=False)
    permission = alchemy_db.Column(alchemy_db.String(100), nullable=False)

    def to_dict(self):
        analysis_user_relation_attrs_dict = dict()
        analysis_user_relation_attrs_dict["id"] = self.id
        analysis_user_relation_attrs_dict["analysisId"] = self.analysis_id
        analysis_user_relation_attrs_dict["userId"] = self.user_id
        analysis_user_relation_attrs_dict["relation"] = self.relation
        analysis_user_relation_attrs_dict["permission"] = self.permission
        return analysis_user_relation_attrs_dict

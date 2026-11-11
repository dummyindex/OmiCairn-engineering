from db import alchemy_db

class ComputationUserRelation(alchemy_db.Model):
    __tablename__ = 'computation_user_relation'
    id = alchemy_db.Column(alchemy_db.BigInteger, primary_key=True, autoincrement=True)
    computation_id = alchemy_db.Column(alchemy_db.BigInteger, nullable=False)
    user_id = alchemy_db.Column(alchemy_db.BigInteger, nullable=False)
    relation = alchemy_db.Column(alchemy_db.String(100), nullable=False)
    permission = alchemy_db.Column(alchemy_db.String(100), nullable=False)

    def to_dict(self):
        computation_user_relation_attrs_dict = dict()
        computation_user_relation_attrs_dict["id"] = self.id
        computation_user_relation_attrs_dict["computationId"] = self.computation_id
        computation_user_relation_attrs_dict["userId"] = self.user_id
        computation_user_relation_attrs_dict["relation"] = self.relation
        computation_user_relation_attrs_dict["permission"] = self.permission
        return computation_user_relation_attrs_dict

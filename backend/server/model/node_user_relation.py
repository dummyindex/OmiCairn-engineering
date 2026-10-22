from db import alchemy_db as db

class NodeUserRelation(db.Model):
    __tablename__ = 'node_user_relation'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    node_id = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.BigInteger, nullable=False)
    relation = db.Column(db.String(100), nullable=False)
    permission = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        node_user_relation_attrs_dict = dict()
        node_user_relation_attrs_dict["id"] = self.id
        node_user_relation_attrs_dict["nodeId"] = self.node_id
        node_user_relation_attrs_dict["userId"] = self.user_id
        node_user_relation_attrs_dict["relation"] = self.relation
        node_user_relation_attrs_dict["permission"] = self.permission
        return node_user_relation_attrs_dict

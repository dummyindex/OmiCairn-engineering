from db import alchemy_db as db

class DataUserRelation(db.Model):
    __tablename__ = 'data_user_relation'
    id = db.Column(db.BigInteger, primary_key=True)
    data_id = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.BigInteger, nullable=False)
    relation = db.Column(db.String(100), nullable=False)
    permission = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        data_user_relation_attrs_dict = dict()
        data_user_relation_attrs_dict["id"] = self.id
        data_user_relation_attrs_dict["dataId"] = self.data_id
        data_user_relation_attrs_dict["userId"] = self.user_id
        data_user_relation_attrs_dict["relation"] = self.relation
        data_user_relation_attrs_dict["permission"] = self.permission
        return data_user_relation_attrs_dict
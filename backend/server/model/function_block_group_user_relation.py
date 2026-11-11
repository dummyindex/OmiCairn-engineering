from db import alchemy_db as db

class FunctionBlockGroupUserRelation(db.Model):
    __tablename__ = 'function_block_group_user_relation'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    function_block_group_id = db.Column(db.BigInteger)
    user_id = db.Column(db.BigInteger)
    relation = db.Column(db.String(100))
    permission = db.Column(db.String(100))

    def to_dict(self):
        function_block_group_user_relation_attrs_dict = dict()
        function_block_group_user_relation_attrs_dict["id"] = self.id
        function_block_group_user_relation_attrs_dict["functionBlockGroupId"] = self.function_block_group_id
        function_block_group_user_relation_attrs_dict["userId"] = self.user_id
        function_block_group_user_relation_attrs_dict["relation"] = self.relation
        function_block_group_user_relation_attrs_dict["permission"] = self.permission
        return function_block_group_user_relation_attrs_dict

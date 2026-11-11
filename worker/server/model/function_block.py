from db import alchemy_db as db


class FunctionBlock(db.Model):
    __tablename__ = "function_block"
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    name = db.Column(db.String(255), nullable=False)
    group_id = db.Column(db.BigInteger, nullable=False)
    created_time = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        function_block_attrs_dict = dict()
        function_block_attrs_dict["id"] = self.id
        function_block_attrs_dict["name"] = self.name
        function_block_attrs_dict["groupId"] = self.group_id
        function_block_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000
        return function_block_attrs_dict

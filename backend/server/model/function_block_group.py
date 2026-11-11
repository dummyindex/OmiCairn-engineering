from db import alchemy_db as db


class FunctionBlockGroup(db.Model):
    __tablename__ = "function_block_group"

    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    name = db.Column(db.String(255), nullable=False)
    created_time = db.Column(db.DateTime, nullable=False)
    serial_number = db.Column(db.BigInteger, nullable=True)
    alt_name = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        function_block_group_attrs_dict = dict()
        function_block_group_attrs_dict["id"] = self.id
        function_block_group_attrs_dict["name"] = self.name
        function_block_group_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000
        function_block_group_attrs_dict["serialNumber"] = self.serial_number
        function_block_group_attrs_dict["altName"] = self.alt_name
        return function_block_group_attrs_dict

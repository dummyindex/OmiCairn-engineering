from db import alchemy_db as db

class FunctionBlockUpdatedRecord(db.Model):
    __tablename__ = "function_block_updated_record"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='ID')
    function_block_id = db.Column(db.BigInteger, nullable=False)
    updated_time = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        function_block_updated_record_attrs_dict = dict()
        function_block_updated_record_attrs_dict["id"] = self.id
        function_block_updated_record_attrs_dict["functionBlockId"] = self.function_block_id
        function_block_updated_record_attrs_dict["updatedTime"] = self.updated_time.timestamp() * 1000
        return function_block_updated_record_attrs_dict
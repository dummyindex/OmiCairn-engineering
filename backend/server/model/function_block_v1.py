"""
    CREATE TABLE `omicairn`.`function_block_v1` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(200) NULL,
  `type` VARCHAR(50) NULL,
  `group_id` BIGINT NULL,
  `owner_id` BIGINT NULL,
  `current_version_id` BIGINT NULL,
  `created_time` DATETIME NULL,
  `occasion` VARCHAR(50) NULL,
  PRIMARY KEY (`id`));
"""

from db import alchemy_db as db

class FunctionBlockV1(db.Model):

    __tablename__ = "function_block_v1"

    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    name = db.Column(db.String(200), nullable=False)
    group_id = db.Column(db.BigInteger, nullable=False)
    current_version_id = db.Column(db.BigInteger, nullable=False)
    created_time = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    occasion = db.Column(db.String(50), nullable=False)
    alt_name = db.Column(db.String(255), nullable=True)


    def to_dict(self):
        function_block_attrs_dict = dict()
        function_block_attrs_dict["id"] = self.id
        function_block_attrs_dict["name"] = self.name
        function_block_attrs_dict["groupId"] = self.group_id
        function_block_attrs_dict["currentVersionId"] = self.current_version_id
        function_block_attrs_dict["type"] = self.type
        function_block_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000 if self.created_time else None
        function_block_attrs_dict["occasion"] = self.occasion
        function_block_attrs_dict["altName"] = self.alt_name
        return function_block_attrs_dict

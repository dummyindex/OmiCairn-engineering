from db import alchemy_db as db

class ParamFile(db.Model):
    __tablename__ = "param_file"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.BigInteger, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    size = db.Column(db.BigInteger, nullable=False)
    suffix = db.Column(db.String(100), nullable=False)
    content_type = db.Column(db.String(100), nullable=False)
    object_key = db.Column(db.String(100), nullable=False)
    bucket = db.Column(db.String(100), nullable=False)
    created_time = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        param_file_attrs_dict = dict()
        param_file_attrs_dict["id"] = self.id
        param_file_attrs_dict["uuid"] = self.uuid
        param_file_attrs_dict["userId"] = self.user_id
        param_file_attrs_dict["name"] = self.name
        param_file_attrs_dict["size"] = self.size
        param_file_attrs_dict["suffix"] = self.suffix
        param_file_attrs_dict["contentType"] = self.content_type
        param_file_attrs_dict["objectKey"] = self.object_key
        param_file_attrs_dict["bucket"] = self.bucket
        param_file_attrs_dict["createdTime"] = self.created_time.timestamp() * 1000
        return param_file_attrs_dict

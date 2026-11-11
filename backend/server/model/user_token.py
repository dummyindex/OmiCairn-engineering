from db import alchemy_db as db
from tool.user_token import UserTokenTool
from datetime import datetime


class UserToken(db.Model):
    __tablename__ = 'user_token'
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    value = db.Column(db.String(50), nullable=False, unique=True)
    user_id = db.Column(db.BigInteger, nullable=False)
    created_time = db.Column(db.DateTime, nullable=False)
    disabled = db.Column(db.Boolean, nullable=False)
    extend1 = db.Column(db.String(50), nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)

    def is_overdue(self):
        deadline = datetime.now()
        return self.end_time < deadline

    def to_dict(self):
        user_token_attrs_dict = dict()
        user_token_attrs_dict["id"] = self.id
        user_token_attrs_dict["value"] = self.value
        user_token_attrs_dict["userId"] = self.user_id
        user_token_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000
        user_token_attrs_dict["disabled"] = self.disabled
        user_token_attrs_dict["extend1"] = self.extend1
        user_token_attrs_dict["endTime"] = self.end_time.timestamp() * 1000
        return user_token_attrs_dict

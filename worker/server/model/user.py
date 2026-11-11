from db import alchemy_db as db
from constants.authority import AccountType


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    user_name = db.Column(db.String(30), nullable=True)
    phone_number = db.Column(db.String(18), unique=True)
    password = db.Column(db.String(255), nullable=False)  # stores a werkzeug password hash (see backend service/user.py)
    created_time = db.Column(db.DateTime, nullable=False)
    disabled = db.Column(db.Boolean, nullable=False, default=False)
    email = db.Column(db.String(200), unique=True)
    account_type = db.Column(db.String(20), nullable=False, default=AccountType.PERSONAL.value)
    extend1 = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        user_attrs_dict = dict()
        user_attrs_dict["id"] = self.id
        user_attrs_dict["userName"] = self.user_name
        user_attrs_dict["phoneNumber"] = self.phone_number
        user_attrs_dict["createdTime"] = self.created_time.timestamp() * 1000
        user_attrs_dict["disabled"] = self.disabled
        user_attrs_dict["email"] = self.email
        user_attrs_dict["accountType"] = self.account_type
        user_attrs_dict["extend1"] = self.extend1
        return user_attrs_dict

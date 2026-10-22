
from datetime import datetime

from sqlalchemy import and_
from model.user_token import UserToken
from db import alchemy_db


class UserTokenDao:
    def insert(self, user_token: UserToken):
        if user_token.created_time is None:
            user_token.created_time = datetime.now()
        alchemy_db.session.add(user_token)
        alchemy_db.session.flush()
        return user_token

    def find_by_value(self, value):
        user_token: UserToken = UserToken.query.filter(
            UserToken.value == value
        ).first()
        return user_token


# singleton
user_token_dao = UserTokenDao()

from datetime import datetime
from typing import List
from model.user import User
from db import alchemy_db


class UserDAO:
    def find_by_id(self, user_id):
        user: User = User.query.get(user_id)
        if not user:
            return None
        return user

    def insert(self, user: User):
        if user.created_time is None:
            user.created_time = datetime.now()
        alchemy_db.session.add(user)
        alchemy_db.session.flush()
        return user

# singleton
user_dao = UserDAO()

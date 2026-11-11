from datetime import datetime
from typing import List
from model.user import User
from db import alchemy_db
from sqlalchemy import and_, or_


class UserDao:
    def find_by_id(self, user_id):
        if user_id is None:
            return None
        user: User = User.query.get(user_id)
        if not user:
            return None
        return user

    def find_by_phone_number(self, phone_number):
        user: User = User.query.filter(
            User.phone_number == phone_number).first()
        return user
    
    def find_by_id_list(self, user_id_list):
        users: List[User] = User.query.filter(
            User.id.in_(user_id_list)
        ).all()
        return users
    
    def search(self, keyword: str, offset: int, limit: int) -> List[User]:
        users: List[User] = User.query.filter(
            or_(
                User.user_name.like(f'%{keyword}%'),
                # User.phone_number.like(f'%{keyword}%'),
                User.email.like(f'%{keyword}%')
            )
        ).limit(limit).offset(offset).all()
        return users

    def insert(self, user: User):
        if user.created_time is None:
            user.created_time = datetime.now()
        alchemy_db.session.add(user)
        alchemy_db.session.flush()
        return user
    
    def update(self, user_id, attrs: dict):
        effect_row_count = User.query.filter(User.id == user_id).update(attrs)
        return effect_row_count

    def destroy(self, user_id):
        effect_row_count = User.query.filter(User.id == user_id).delete()
        return effect_row_count


# singleton
user_dao = UserDao()

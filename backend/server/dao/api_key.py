from model.api_key import APIKey

from db import alchemy_db as db

class APIKeyDao:
    def insert(self, api_key: APIKey):
        db.session.add(api_key)
        db.session.flush()
        return api_key

    def find_by_user_id(self, user_id):
        return APIKey.query.filter(APIKey.user_id == user_id).all()

    def update(self, api_key_id, updated_attrs: dict):
        APIKey.query.filter(APIKey.id == api_key_id).update(updated_attrs)
        db.session.flush()

    def delete(self, api_key_id:str | int):
        APIKey.query.filter(APIKey.id == api_key_id).delete()
        db.session.flush()

api_key_dao = APIKeyDao()

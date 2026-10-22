from model.api_key import APIKey

from datetime import datetime

from dao.api_key import api_key_dao
from exception.authority.no_authority import NoAuthorityException

class APIKeyService:
    def create_api_key(self, **kwargs):
        now = datetime.now()
        kwargs['created_time'] = now
        api_key = APIKey(**kwargs)
        return api_key_dao.insert(api_key)

    def get_api_keys(self, user_id):
        return api_key_dao.find_by_user_id(user_id)

    def check_owner(self, api_key_id, user_id):
        owned_ids = {str(k.id) for k in api_key_dao.find_by_user_id(user_id)}
        if str(api_key_id) not in owned_ids:
            raise NoAuthorityException("You do not own this API key.")

    def delete_api_key(self, api_key_id):
        api_key_dao.delete(api_key_id)

    def update_api_key(self, api_key_id, updated_attrs: dict):
        api_key_dao.update(api_key_id, updated_attrs)

api_key_service = APIKeyService()


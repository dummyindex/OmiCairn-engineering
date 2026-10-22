from typing import List
from flask import Blueprint, request
from service.api_key import api_key_service
from flask_restful import Api, Resource
from tool.requests_auditor import request_auditor
from authority.guardian_factory import AuthorityGuardianFactory
from tool.response_manager import ResponseManager
from wrapper.exception import exception_wrapper
from wrapper.db_session import transaction_wrapper
from datetime import datetime
from exception.authority.token_invalid import TokenInvalidException


def _require_login(guardian):
    user_id = guardian.get_user_id()
    if user_id is None:
        raise TokenInvalidException()
    return user_id

class APIKeyCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = _require_login(guardian)
        api_key_data = request.get_json()
        api_key_data['user_id'] = user_id
        api_key_obj = api_key_service.create_api_key(**api_key_data)
        return ResponseManager.new_success_response(data=api_key_obj)

class APIKeyListAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = _require_login(guardian)
        api_key_list = api_key_service.get_api_keys(user_id=user_id)
        return ResponseManager.new_success_response(data=api_key_list)

class APIKeyDeleteAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def delete(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = _require_login(guardian)
        key_id = request.args.get('key_id')
        api_key_service.check_owner(key_id, user_id)
        api_key_service.delete_api_key(api_key_id=key_id)
        return ResponseManager.new_success_response(message="API key deleted successfully.")

class APIKeyUpdateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = _require_login(guardian)
        key_id = request.args.get('key_id')
        api_key_service.check_owner(key_id, user_id)
        api_key_data = request.get_json()
        for unchangeable_key in ["id", "user_id", "created_time"]:
            api_key_data.pop(unchangeable_key, None)
        api_key_service.update_api_key(api_key_id=key_id, updated_attrs=api_key_data)
        return ResponseManager.new_success_response(message="API key updated successfully.")

api_key_bp = Blueprint('api_key', __name__)
api_key_api = Api(api_key_bp, prefix='/api-key')
api_key_api.add_resource(APIKeyCreateAPI, '/create-key')
api_key_api.add_resource(APIKeyListAPI, '/list-keys')
api_key_api.add_resource(APIKeyDeleteAPI, '/delete-key')
api_key_api.add_resource(APIKeyUpdateAPI, '/update-key')

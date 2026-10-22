from flask import Blueprint, request
from flask_restful import Api, Resource
from datetime import datetime
from authority.guardian_factory import AuthorityGuardianFactory
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from service.user import user_service
from constants.authority import AccountType
from wrapper.exception import exception_wrapper


class UserLoginByPasswordAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_form_check(
            request=request, checked_list=["phone_number", "password"])
        phone_number = request.form.get("phone_number")
        password = request.form.get("password")
        token = user_service.login_by_password(
            phone_number,
            password
        )
        return ResponseManager.new_success_response(data=token.value)
    
class UserLoginBySystemAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(
            request=request, checked_list=["user_id"])
        user_id = request.args.get("user_id")
        # Prefer the X-System-Agent-Key header; the query parameter is kept for
        # backward compatibility with existing internal agents.
        system_agent_key = request.headers.get("X-System-Agent-Key") or request.args.get("system_agent_key")
        token = user_service.login_by_system(
            user_id,
            system_agent_key
        )
        return ResponseManager.new_success_response(data=token.value)


class TokenValidateAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        try:
            user_id = guardian.get_user_id()
            return ResponseManager.new_success_response(data=user_id is not None)
        except Exception as e:
            return ResponseManager.new_success_response(data=False)

class UserRegisterCodeAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_form_check(
            request=request, checked_list=["phone_number", "password"])
        phone_number = request.form.get("phone_number")
        password = request.form.get("password")
        user_name = request.form.get("user_name", "unamed_user")
        email = request.form.get("email", "")
        account_type = request.form.get("account_type", AccountType.PERSONAL.value)

        valid_account_types = [AccountType.PERSONAL.value, AccountType.ENTERPRISE.value]
        if account_type not in valid_account_types:
            account_type = AccountType.PERSONAL.value
            
        register_result = user_service.register(
            user_name,
            phone_number,
            password,
            email,
            account_type
        )
        return ResponseManager.new_success_response(data=register_result)


class UserInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        user_info = user_service.get_info(user_id)
        return ResponseManager.new_success_response(data=user_info)
    
class UserSearchAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request, checked_list=["keyword", "offset", "limit"])
        keyword = request.args.get("keyword")
        offset = int(request.args.get("offset", 0))
        limit = int(request.args.get("limit", 10))
        AuthorityGuardianFactory.get_authority_guardian().require_user_id()
        user_list = user_service.search_by_keyword(keyword, offset, limit)
        return ResponseManager.new_success_response(data=user_list)
    

class UserEditAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        request_auditor.request_json_check(
            request,
            [
                "user_name",
                "email",
                "phone_number",
            ]
        )
        post_data = request.get_json()
        user_name = post_data.get("user_name")
        email = post_data.get("email")
        phone_number = post_data.get("phone_number")
        account_type = post_data.get("account_type")
        
        if account_type is not None:
            # Users may not promote themselves to ADMINISTRATOR.
            valid_account_types = [AccountType.PERSONAL.value, AccountType.ENTERPRISE.value]
            if account_type not in valid_account_types:
                account_type = None
        
        user_service.edit(user_id, user_name, email, phone_number, account_type)
        return ResponseManager.new_success_response()

# class UserDestroyAPI(Resource):
#     @exception_wrapper
#     @transaction_wrapper
#     def get(self):
#         guardian = AuthorityGuardianFactory.get_authority_guardian()
#         user_id = guardian.get_user_id()
#         return user_service.


user_bp = Blueprint("user", __name__)
user_api = Api(user_bp, prefix="/user")
user_api.add_resource(UserLoginByPasswordAPI, '/login-by-password')
user_api.add_resource(TokenValidateAPI, '/validate-token')
user_api.add_resource(UserRegisterCodeAPI, '/register')
user_api.add_resource(UserInfoGetAPI, '/info/get')
user_api.add_resource(UserSearchAPI, '/search')
user_api.add_resource(UserEditAPI, '/edit')
user_api.add_resource(UserLoginBySystemAPI, '/login-by-system')
# user_api.add_resource(UserDestroyAPI, '/destroy')

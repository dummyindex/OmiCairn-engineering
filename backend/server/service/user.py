from datetime import datetime, timedelta
import hmac
import json
from werkzeug.security import generate_password_hash, check_password_hash
from constants.authority import SpecialUserId, SYSTEM_AGENT_KEY, AccountType
from exception.authority.login_error import LoginErrorException
from model.user_token import UserToken
from exception.authority.register_error import RegisterErrorException
from model.user import User
from model.inform import Inform
from tool.user_token import UserTokenTool
from dao.user import user_dao
from dao.user_token import user_token_dao
from constants.inform import InformType
from dao.inform import inform_dao

class UserService:
    def __init__(self):
        pass

    def encrypt_password(self, password):
        # Salted, iterated hash (werkzeug PBKDF2/scrypt default).
        return generate_password_hash(password)

    def verify_password(self, password, saved_encryption_password):
        if not password or not saved_encryption_password:
            return False
        try:
            return check_password_hash(saved_encryption_password, password)
        except (ValueError, TypeError):
            return False

    def instantiate_user_token(self, user_id, end_time: datetime = None) -> UserToken:
        now = datetime.now()
        user_token: UserToken = UserToken(
            value=UserTokenTool.generate_new_token_value(),
            created_time=now,
            user_id=user_id,
            disabled=False,
            end_time=(now + timedelta(days=1)) if end_time is None else end_time
        )
        return user_token

    def list_lack_of_info(self, user: User):
        lack_of_info = []
        if user.user_name is None:
            lack_of_info.append("user_name")
        if user.email is None:
            lack_of_info.append("email")
        if user.phone_number is None:
            lack_of_info.append("phone_number")
        return lack_of_info
    
    def login_by_password(
        self,
        phone_number,
        password
    ) -> UserToken:
        now = datetime.now()
        user = user_dao.find_by_phone_number(phone_number)
        if user is None:
            raise LoginErrorException("phone_number does not exist.")
        handled_password = user.password
        verify_result = self.verify_password(password, handled_password)
        if not verify_result:
            raise LoginErrorException("password is not correct.")
        user_id = user.id
        user_token_dao.delete_the_overdue(user_id)
        user_token = self.instantiate_user_token(user_id)
        new_token = user_token_dao.insert(user_token)
        lack_of_info = self.list_lack_of_info(user)
        if len(lack_of_info) > 0:
            inform = inform_dao.find_unread_informs_by_receiver_id_and_type(
                user_id,
                InformType.INFORMATION_COMPLETION_NOTICE.value,
            )
            if len(inform) == 0:
                payload = json.dumps({
                    "lack_of_info": lack_of_info
                })
                inform = Inform(
                    sender_id=SpecialUserId.SYSTEM.value,
                    receiver_id=user_id,
                    created_time=now,
                    have_read=False,
                    type=InformType.INFORMATION_COMPLETION_NOTICE.value,
                    payload=payload
                )
                inform_dao.insert_inform(inform)
        return new_token
    
    def login_by_system(self, user_id, system_agent_key):
        if not SYSTEM_AGENT_KEY or not system_agent_key or not hmac.compare_digest(
            str(system_agent_key), str(SYSTEM_AGENT_KEY)
        ):
            raise LoginErrorException("system_key is not correct.")
        now = datetime.now()
        user = user_dao.find_by_id(user_id)
        if user is None:
            raise LoginErrorException("user does not exist.")
        user_token_dao.delete_the_overdue(user_id)
        user_token = self.instantiate_user_token(user_id, now + timedelta(days=3))
        new_token = user_token_dao.insert(user_token)
        return new_token

    def register(self, user_name, phone_number, password, email, account_type=AccountType.PERSONAL.value):
        if not phone_number or not password:
            raise RegisterErrorException("phone_number and password are required.")
        user_with_phone_number = user_dao.find_by_phone_number(
            phone_number
        )
        if user_with_phone_number is not None:
            raise RegisterErrorException("phone_number has been registered.")
        handled_password = self.encrypt_password(password)
        user = User(
            user_name=user_name,
            phone_number=phone_number,
            password=handled_password,
            email=email,
            account_type=account_type
        )
        user_dao.insert(user)
        return user

    def get_info(self, user_id):
        user = user_dao.find_by_id(user_id)
        return user
    
    def search_by_keyword(self, keyword, offset, limit):
        users = user_dao.search(keyword, offset, limit)
        return users
    
    def edit(self, user_id, user_name, email, phone_number, account_type=None):
        updated_attrs = {
            "user_name": user_name,
            "email": email,
            "phone_number": phone_number
        }
        if account_type is not None:
            updated_attrs["account_type"] = account_type
        user_dao.update(user_id, updated_attrs)
    
user_service = UserService()

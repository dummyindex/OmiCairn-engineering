from abc import ABC, abstractmethod
from flask import request
from dao.user_token import user_token_dao
from exception.authority.token_invalid import TokenInvalidException


class AuthorityGrardian(ABC):

    def __init__(self):
        token_value = request.headers.get("token", default=None)
        user_token = user_token_dao.find_by_value(token_value)
        if user_token is None or user_token.is_overdue():
            # A missing/expired token is treated as an anonymous caller (user_id=None);
            # analysis-scoped check_authority() then only grants access to public or shared-with-all
            # objects. Other carriers use EmptyGuardian (no per-object check), so the worker API must
            # sit behind the backend on a private network and must not be exposed publicly.
            user_id = None
        else:
            user_id = user_token.user_id
        self.user_id = user_id

    def get_user_id(self):
        return self.user_id

    @abstractmethod
    def get_user_relations(self, object_id):
        pass

    @abstractmethod
    def check_authority(self, object_id, check_writable=False):
        pass

    @abstractmethod
    def share_to_all(self, object_id):
        pass

    @abstractmethod
    def cancel_share_to_all(self, object_id):
        pass

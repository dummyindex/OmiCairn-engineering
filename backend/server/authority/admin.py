from authority.guardian_factory import AuthorityGuardianFactory
from constants.authority import AccountType
from dao.user import user_dao
from exception.authority.no_authority import NoAuthorityException


def require_administrator() -> int:
    """Return the current user's id, raising unless the user is an administrator."""
    guardian = AuthorityGuardianFactory.get_authority_guardian()
    user_id = guardian.require_user_id()
    user = user_dao.find_by_id(user_id)
    if user is None or user.account_type != AccountType.ADMINISTRATOR.value:
        raise NoAuthorityException("Administrator privileges are required.")
    return user_id

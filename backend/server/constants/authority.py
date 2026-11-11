##################################################
# authority related
##################################################
from constants.common import AugmentedEnum
import os

class AuthorityCarrier(AugmentedEnum):
    ANALYSIS = "analysis"
    NODE = "node"
    COMPUTATUION = "computation"
    FUNCTION_BLOCK_GROUP = "function-block-group"
    FUNCTION_BLOCK = "function-block"
    DATA = "data"
    PIPELINE_TEMPLATE = "pipeline-template"
    TASK = "task"


# Shared secret used by internal services (worker, agent runners) to obtain a
# token on behalf of a user via /user/login-by-system. Must be set via env; no default.
SYSTEM_AGENT_KEY=os.environ.get("SYSTEM_AGENT_KEY")

class SpecialUserId(AugmentedEnum):
    PUBLIC = 0
    ALL = -1
    SYSTEM = -2

class Relation(AugmentedEnum):
    BELONG_TO = "belong-to"
    SHARED_WITH = "shared-with"

class Permission(AugmentedEnum):
    ADMIN = "admin"
    WRITE = "write"
    READ = "read"
    NO_PERMISSION = "no-permission"

class AccountType(AugmentedEnum):
    PERSONAL = "personal"
    ENTERPRISE = "enterprise"
    ADMINISTRATOR = "administrator"

PermissionLevelDict = {
    Permission.ADMIN.value : 200,
    Permission.WRITE.value : 150,
    Permission.READ.value : 100,
    Permission.NO_PERMISSION.value : 50
}

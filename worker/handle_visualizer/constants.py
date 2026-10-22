from enum import Enum
import os


class AugmentedEnum(Enum):
    def __hash__(self):
        return self.value.__hash__()

    def __eq__(self, other):
        if isinstance(other, type(self)) or isinstance(other, str):
            return self.value == other
        return False

    def __str__(self) -> str:
        return self.value


class InformType(AugmentedEnum):
    ANALYSIS_COLLABORATION_INVITATION = "analysis_collaboration_invitation"
    COMPUTATION_END_NOTICE = "computation_end_notice"
    TASK_END_NOTICE = "task_end_notice"


class Relation(AugmentedEnum):
    BELONG_TO = "belong-to"
    SHARED_WITH = "shared-with"


class Permission(AugmentedEnum):
    ADMIN = "admin"
    WRITE = "write"
    READ = "read"
    NO_PERMISSION = "no-permission"


class FigureExistType(AugmentedEnum):
    STATIC_IMAGE: str = "static-image"
    JSON_DATA: str = "json-data"
    IN_ADATA: str = "in-adata"


class SpecialUserId(AugmentedEnum):
    PUBLIC = 0
    ALL = -1
    SYSTEM = -2


class TaskNodeRelationType(AugmentedEnum):
    BELONG_TO = "belong to"
    BE_AFFECTED = "be affected"


class TaskState(AugmentedEnum):
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"


class DataState(AugmentedEnum):
    UPLOADING = "uploading"
    WAITING = "waiting"
    PREHANDLING = "prehandling"
    ERROR = "error"
    OK = "ok"


def create_folder_if_not_exist(folder_path):
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)


class PorterType(AugmentedEnum):
    S3_PORTER = "s3-porter"


class ComputationSystemEnv(AugmentedEnum):
    AWS_BATCH = "aws-batch"
    SERVER_LOCAL = "server-local"


class ComputationState(AugmentedEnum):
    PENDING = "pending"
    QUEUING = "queuing"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ComputationRetryProcessState(AugmentedEnum):
    RUNNING = "running"
    STOPPED = "stopped"


class NodeType(AugmentedEnum):
    DATA_NODE = "data node"
    COMPUTATION_NODE = "computation node"
    REPORT_NODE = "report node"
    DATA_NODE_V2 = "data node v2"
    COMPUTATION_NODE_V2 = "computation node v2"
    NOTEBOOK_NODE = "notebook node"


class NodeState(AugmentedEnum):
    ORIGINAL = "original"
    PENDING = "pending"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    DEBUGGING = "debugging"
    BEAUTIFYING = "beautifying"
    GENERATING = "generating"
    CANCELLED = "cancelled"


class NodeListFetchMode(AugmentedEnum):
    ANALYSIS = "analysis"
    IDX = "idx"


class CreatedFrom(AugmentedEnum):
    UPLOAD = "upload"
    COMPUTATION = "computation"


class VisualizerState(AugmentedEnum):
    RUNNING = "running"
    FINISHED = "finished"
    STOPPED = "stopped"


class GenerationMode(AugmentedEnum):
    MIXED = "mixed"
    ONLY_EXISTING = "only_existing"
    ONLY_NEW = "only_new"


PORTER_TYPE = PorterType.S3_PORTER.value

BUCKET_NAME = os.environ.get("BUCKET_NAME")

DEPLOY_ENV = os.environ.get("DEPLOY_ENV", "dev")

GPT_WORKFLOW_SERVER_HOST = os.environ.get("GPT_WORKFLOW_SERVER_HOST")
GPT_WORKFLOW_SERVER_PORT = os.environ.get("GPT_WORKFLOW_SERVER_PORT")

NETWORK_PROXY_HOST = os.environ.get("NETWORK_PROXY_HOST")
NETWORK_PROXY_PORT = os.environ.get("NETWORK_PROXY_PORT")

# Optional outbound HTTP proxy; requests uses no proxy when unset.
PROXIES = {
    "http": f"http://{NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}",
    "https": f"http://{NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}"
} if NETWORK_PROXY_HOST and NETWORK_PROXY_PORT else None

DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")
DB_PORT = os.environ.get("DB_PORT")

SYSTEM_AGENT_KEY = os.environ.get("SYSTEM_AGENT_KEY")

VISUALIZER_ID = os.environ.get("VISUALIZER_ID")

USER_ID = os.environ.get("USER_ID")

USER_REQUEST = os.environ.get("USER_REQUEST")

FUNCTION_BLOCK_VERSION_PREFIX = "function-block-version"

MAIN_SERVER_HOST = os.environ.get("MAIN_SERVER_HOST")
COMPUTATION_SERVER_HOST = os.environ.get("COMPUTATION_SERVER_HOST")

CURRENT_NODE_ID = os.environ.get("CURRENT_NODE_ID")

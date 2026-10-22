import os
from constants.common import AugmentedEnum


class ComputationState(AugmentedEnum):
    PENDING = "pending"
    QUEUING = "queuing"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ComputationListFetchMode(AugmentedEnum):
    NODE: str = "node"
    TASK: str = "task"


COMPUTATION_IP = os.environ.get("COMPUTATION_IP")

class SystemEnv(AugmentedEnum):
    AWS_BATCH = "aws-batch"
    SERVER_LOCAL = "server-local"

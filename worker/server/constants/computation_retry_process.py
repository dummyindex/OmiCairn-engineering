from constants.common import AugmentedEnum


class ComputationRetryProcessState(AugmentedEnum):
    RUNNING = "running"
    STOPPED = "stopped"

from constants.common import AugmentedEnum

class TaskState(AugmentedEnum):
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
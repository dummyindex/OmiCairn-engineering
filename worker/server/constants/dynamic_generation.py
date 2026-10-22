from constants.common import AugmentedEnum


class DynamicGenerationState(AugmentedEnum):
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"

class PlanStatus(AugmentedEnum):
    GENERATING = "generating"
    GENERATED = "generated"
    GENERATION_FAILED = "generation_failed"
    EXECUTING = "executing"
    STOPPED = "stopped"
    EXECUTION_FAILED = "execution_failed"
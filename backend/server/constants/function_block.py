from constants.common import AugmentedEnum
import os

class FunctionBlockVersionState(AugmentedEnum):
    UNUPLOAD = "unupload"
    PREHANDLING = "prehandling"
    OK = "ok"
    FAILED = "failed"

FB_PP_QUEUE = os.environ.get("FB_PP_QUEUE")

MINI_TOOL_GROUP_ID = -1

class FBOccasion(AugmentedEnum):
    FLOW = "flow"
    MINI_TOOL = "mini-tool"
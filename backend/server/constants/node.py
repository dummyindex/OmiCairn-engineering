##################################################
# analysis node related
##################################################

from constants.common import AugmentedEnum


class NodeType(AugmentedEnum):
    DATA_NODE = "data node"
    COMPUTATION_NODE = "computation node"
    REPORT_NODE = "report node"
    DATA_NODE_V2 = "data node v2"
    COMPUTATION_NODE_V2 = "computation node v2"
    NOTEBOOK_NODE = "notebook node"
    CLAUDE_CODE_NODE = "claude code node"


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

from enum import Enum


class ChatStatus(Enum):
    """Chat status enumeration"""
    NORMAL = "normal"
    EXECUTING = "executing"
    RESPONDING = "responding"
    SUMMARIZING = "summarizing"


class ChatSubTaskStatus(Enum):
    """Chat sub task status enumeration"""
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"


class MessageRole(Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant" 
    TOOL = "tool"


class AvailableTools(Enum):
    """Available tools enumeration"""
    GET_ANALYSIS_INFO = "get_analysis_info"
    GET_CURRENT_NODE_INFO = "get_current_node_info"
    GET_WHOLE_TREE_INFO = "get_whole_tree_info"
    GET_WHOLE_BRANCH_INFO = "get_whole_branch_info"
    GET_DATASET_LIST = "get_dataset_list"
    CAPTURE_DATA = "capture_data"
    FIX_BUG = "fix_bug"
    AUTOGENIE = "autogenie"

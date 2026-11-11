import os
import requests

SYSTEM_AGENT_KEY = os.getenv("SYSTEM_AGENT_KEY")
MAIN_SERVER_HOST = os.getenv("MAIN_SERVER_HOST")

def login_main_server(user_id):
    response = requests.post(
        f"http://{MAIN_SERVER_HOST}/server/user/login-by-system?user_id={user_id}",
        headers={"X-System-Agent-Key": SYSTEM_AGENT_KEY or ""})
    headers = {
        "token": response.json()["data"]
    }
    return headers

def query_chat_sub_task(system_task_id: int, tool_name: str, headers: dict) -> dict:
    response = requests.get(
        f"http://{MAIN_SERVER_HOST}/server/v3.0/chat/query-chat-sub-task?system_task_id={system_task_id}&tool_name={tool_name}",
        headers=headers
    )
    response.raise_for_status()
    result = response.json()
    if result.get("code") != 200:
        raise Exception(f"Failed to query chat sub task: {result}")
    return result.get("data")

def report_chat_tool_callback(chat_sub_task_id: int, callback_data: dict, headers: dict) -> None:
    json_data = callback_data
    response = requests.post(
        f"http://{MAIN_SERVER_HOST}/server/v3.0/chat/callback-chat-sub-task?chat_sub_task_id={chat_sub_task_id}",
        headers=headers,
        json=json_data
    )
    response.raise_for_status()
    result = response.json()
    if result.get("code") != 200:
        raise Exception(f"Failed to report chat tool callback: {result}")
    return result.get("data")


def copy_node(original_node_id: int, with_edges: bool, user_id: int) -> int:
    headers = login_main_server(user_id)
    response = requests.get(
        f"http://{MAIN_SERVER_HOST}/server/node/copy?node_id={original_node_id}&with_edges={1 if with_edges else 0}",
        headers=headers
    )
    response.raise_for_status()
    result = response.json()
    if result.get("code") != 200:
        raise Exception(f"Failed to copy node: {result}")
    return result.get("data")
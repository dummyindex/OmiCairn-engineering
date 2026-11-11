from constants import (
    GPT_WORKFLOW_SERVER_HOST,
    GPT_WORKFLOW_SERVER_PORT,
    PROXIES,
    GenerationMode
)
import json
import requests
from datetime import datetime
from exception.request.dynamic_status_code import DynamicStatusCode
from logger_factory import LoggerFactory
logger = LoggerFactory.get_logger("LlmInterface")


class LlmInterface:
    def __init__(self) -> None:
        pass

    def _check_response(self, response):
        if response.status_code != 200:
            response_json = response.json()
            raise DynamicStatusCode(
                response.status_code, response_json["message"])

    def init_chat(self, analysis_id, owner_id):
        params = {
            "owner_id": owner_id,
            "analysis_id": analysis_id,
            "user_id": owner_id,
        }
        response = requests.post(
            # url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/chat/init",
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/oldchat/init",
            params=params,
            proxies=PROXIES
        )
        return response

    def get_chat_history(self, analysis_id, owner_id):
        params = {
            "owner_id": owner_id,
            "analysis_id": analysis_id,
            "user_id": owner_id,
        }
        response = requests.get(
            # url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/chat/history",
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/oldchat/history",
            params=params,
            proxies=PROXIES
        )
        return response

    def send_message(self, analysis_id, owner_id, chat_id, message):
        params = {
            "owner_id": owner_id,
            "analysis_id": analysis_id,
            "chat_id": chat_id,
            "message": message,
            "user_id": owner_id,
        }
        response = requests.post(
            # url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/chat/",
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/oldchat/",
            params=params,
            proxies=PROXIES
        )
        return response

    def init_global_chat(self, analysis_id, user_id):
        params = {
            "owner_id": user_id,
            "analysis_id": analysis_id,
            "user_id": user_id,
        }
        response = requests.post(
            # url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/chat/init/global",
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/oldchat/init/global",
            params=params,
            proxies=PROXIES
        )
        return response

    def send_global_message(self, analysis_id, user_id, chat_id, message):
        params = {
            "owner_id": user_id,
            "analysis_id": analysis_id,
            "message": message,
            "chat_id": chat_id,
            "user_id": user_id,
        }
        response = requests.post(
            # url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/chat/global",
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/oldchat/global",
            params=params,
            proxies=PROXIES
        )
        return response

    def init_local_chat(self, analysis_id, node_id, owner_id):
        params = {
            "owner_id": owner_id,
            "analysis_id": analysis_id,
            "node_id": node_id,
            "user_id": owner_id,
        }
        response = requests.post(
            # url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/chat/init/local",
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/oldchat/init/local",
            params=params,
            proxies=PROXIES
        )
        return response

    def send_local_message(self, analysis_id, owner_id, chat_id, message):
        params = {
            "owner_id": owner_id,
            "analysis_id": analysis_id,
            "chat_id": chat_id,
            "message": message,
            "user_id": owner_id,
        }
        response = requests.post(
            # url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/chat/local",
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/oldchat/local",
            params=params,
            proxies=PROXIES
        )
        return response

    def get_complex_chat_list(self, analysis_id, owner_id):
        params = {
            "owner_id": owner_id,
            "analysis_id": analysis_id,
            "user_id": owner_id,
        }
        response = requests.get(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/chat/history/all",
            params=params,
            proxies=PROXIES,
        )
        return response

    def get_complex_chat_message_list(self, thread_id, user_id):
        params = {
            "thread_id": thread_id,
            "user_id": user_id,
        }
        response = requests.get(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/chat/history",
            params=params,
            proxies=PROXIES
        )
        return response

    def init_complex_chat(self, analysis_id, owner_id):
        params = {
            "owner_id": owner_id,
            "analysis_id": analysis_id,
            "user_id": owner_id,
        }
        response = requests.post(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/chat/init/analysis",
            params=params,
            proxies=PROXIES
        )
        return response

    def send_complex_message(self, analysis_id, owner_id, thread_id, message):
        params = {
            "owner_id": owner_id,
            "analysis_id": analysis_id,
            "thread_id": thread_id,
            "message": message,
            "user_id": owner_id,
        }
        response = requests.post(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/chat/analysis",
            params=params,
            proxies=PROXIES
        )
        return response

    # be used to passby the prompt of user to create a pipeline template
    def recommend_pipeline(self, user_request, user_id):
        params = {
            "user_request": user_request,
            "user_id": user_id,
        }
        response = requests.post(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/workflow",
            params=params,
            proxies=PROXIES
        )
        return response

    def get_similar_pipeline_template(self, user_request, user_id):
        params = {
            "user_request": user_request,
            "user_id": user_id,
        }
        response = requests.get(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/pipline/template/get",
            params=params,
            proxies=PROXIES
        )
        return response

    def create_workflow_report(self, node_ids, computation_details_list, analysis_id, uuid_str, user_id):
        response = requests.get(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/report/get",
            proxies=PROXIES,
            json={
                "ownerID": user_id,
                "analysisID": analysis_id,
                "uuid": uuid_str,
                "nodeIDs": node_ids,
                "currentNodeList": computation_details_list,
            }
        )
        return response

    def visualize(self, function_block, inputs, outputs, user_request, llm_model):
        json_data = {
            "original_function_block": function_block,
            "inputs": inputs,
            "outputs": outputs,
            "user_prompt": user_request,
            "model": llm_model
        }
        response = requests.post(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/visualizer/get",
            proxies=PROXIES,
            json=json_data
        )
        return response

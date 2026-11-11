from constants import (
    GPT_WORKFLOW_SERVER_HOST,
    GPT_WORKFLOW_SERVER_PORT,
    PROXIES,
    GenerationMode
)
import requests
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

    def dynamic_fb(self, user_request, node_id, history, user_id, llm_model, max_branch_count=2, generation_mode=GenerationMode.MIXED.value, file_ids=None):
        current_node = history[-1]
        json_data = {
            "nodeHistoryList": history,
            "currentNode": current_node,
            "user_request": user_request,
            "file_ids": file_ids
        }
        url = f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/dynamic_fb/get?user_id={user_id}&node_id={node_id}&max_branch_count={max_branch_count}&generation_mode={generation_mode}"
        if llm_model:
            url += f"&model={llm_model}"
        response = requests.post(
            url=url,
            proxies=PROXIES,
            json=json_data
        )
        return response

    def dynamic_fb_with_plan(self, user_request, llm_model, node_id, history, user_id, max_branch_count=2, generation_mode=GenerationMode.MIXED.value, file_ids=None, current_plan=None):
        current_node = history[-1]
        json_data = {
            "nodeHistoryList": history,
            "currentNode": current_node,
            "user_request": user_request,
            "file_ids": file_ids,
            "current_plan": current_plan
        }
        url = f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/dynamic_fb/get?user_id={user_id}&node_id={node_id}&max_branch_count={max_branch_count}&generation_mode={generation_mode}"
        logger.debug(f"handle_dynamic_generation/llm_interface.py: llm_model: {llm_model}, current_plan: {current_plan}")
        if llm_model is not None:
            url += f"&model={llm_model}"

        response = requests.post(
            url=url,
            proxies=PROXIES,
            json=json_data
        )

        return response

    def dynamic_fb_with_plan_v2(self, user_request, node_id, user_id, llm_model=None, max_branch_count=2, current_plan=None, finished_steps=None, inputs_structure=None, generation_mode=GenerationMode.ONLY_NEW.value, existing_fbvs_v2_str=None):
        """
        Call DynamicFbV2 API for generating function blocks.

        Args:
            user_request: User's analysis request
            node_id: Node identifier
            user_id: User identifier
            llm_model: LLM model to use (optional)
            max_branch_count: Maximum number of function blocks to generate (default: 2)
            current_plan: Current execution plan (optional)
            finished_steps: String describing completed computation steps (optional)
            inputs_structure: String describing the inputs directory structure (optional)

        Returns:
            Response from the API
        """
        json_data = {
            "user_request": user_request,
            "current_plan": current_plan if current_plan else "",
            "finished_steps": finished_steps if finished_steps else "",
            "inputs_structure": inputs_structure if inputs_structure else "",
            "existing_fbs_str": existing_fbvs_v2_str if existing_fbvs_v2_str else ""
        }

        url = f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/dynamic_fb_v2/generate?user_id={user_id}&node_id={node_id}&max_branch_count={max_branch_count}&generation_mode={generation_mode}"

        if llm_model is not None:
            url += f"&model={llm_model}"

        logger.info(f"[DynamicFbV2] URL: {url}, current_plan: {current_plan}, finished_steps: {finished_steps}, inputs_structure length: {len(inputs_structure) if inputs_structure else 0}")

        response = requests.post(
            url=url,
            proxies=PROXIES,
            json=json_data
        )

        return response

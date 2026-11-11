from constants.gpt_server import (
    GPT_SERVER_HOST,
    GPT_SERVER_PORT,
    GPT_WORKFLOW_SERVER_HOST,
    GPT_WORKFLOW_SERVER_PORT,
    PROXIES,
)
import requests
from log.logger_factory import LoggerFactory
logger = LoggerFactory.get_logger("LlmInterface")


class LlmInterface:
    def __init__(self) -> None:
        pass

    def apply_for_optimize_error_description(self, computation_id):
        try:
            url = f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/error/write"
            params = {
                "computation_id": computation_id
            }
            logger.info(
                f"Apply for optimize error description: {url}, params: {params}")
            response = requests.post(url, params=params, proxies=PROXIES)
            logger.info(
                f"Apply for optimize error description response status code: {response.status_code}")
            if response.status_code != 200:
                logger.error(
                    f"Apply for optimize error description failed: {response.content}")
            return response
        except Exception as e:
            logger.error(f"Apply for optimize error description failed: {e}")

    def upload_files_to_llm_server(self, file_infos):
        try:
            url = f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/dynamic_fb/upload-files"
            logger.info(f"Upload files to llm server: {file_infos}")
            response = requests.post(url, json={
                "files": file_infos
            })
            if response.status_code != 200:
                logger.error(
                    f"Upload files to llm server failed: {response.content}")
                return None
            return response.json()["data"]
        except Exception as e:
            logger.error(f"Upload files to llm server failed: {e}")
            return None

    def generate_initial_plan(self, user_id, node_id, user_request, llm_model, node_context, max_node, max_branch, file_list):
        url = f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/dynamic_fb_plan/generate-plan"

        payload = {
            "user_id": user_id,
            "node_id": node_id,
            "user_request": user_request,
            "node_context": node_context,
            "max_node": max_node,
            "max_branch": max_branch,
            "file_list": file_list
        }

        if llm_model:
            payload["llm_model"] = llm_model

        response = requests.post(
            url,
            json=payload,
            proxies=PROXIES
        )

        return response

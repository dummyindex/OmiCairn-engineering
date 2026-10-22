from constants.gpt import (
    GPT_WORKFLOW_SERVER_HOST,
    GPT_WORKFLOW_SERVER_PORT,
    PROXIES
)
import requests
from exception.request.dynamic_status_code import DynamicStatusCode
from log.logger_factory import logger_factory
logger = logger_factory.create_logger("gpt-helper")

class LlmInterface:
    def __init__(self) -> None:
        pass

    def _check_response(self, response):
        if response.status_code != 200:
            response_json = response.json()
            raise DynamicStatusCode(response.status_code, response_json["message"])

    def apply_for_optimize_error_description(self, computation_id, user_id):
        try:
            url = f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/error/write"
            params = {
                "computation_id": computation_id,
                "user_id": user_id
            }
            logger.info(f"Apply for optimize error description: {url}, params: {params}")
            response = requests.post(url, params=params, proxies=PROXIES)
            logger.info(f"Apply for optimize error description response status code: {response.status_code}")
            self._check_response(response)
        except Exception as e:
            logger.error(f"Apply for optimize error description failed: {e}")


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
            proxies=PROXIES
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

    def fill_params(self, node_id, param_dict, history: list, to_create_function, user_id):
        current_node = history.pop()
        json_data = {}
        if param_dict is not None:
            json_data["computationParamsToFix"] = param_dict
        json_data["nodeHistoryList"] = history
        json_data["currentNode"] = current_node
        response = requests.get(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/parameter/get?node_id={node_id}&user_id={user_id}&to_create_function={to_create_function}",
            json=json_data,
            proxies=PROXIES
        )
        return response
    
    def get_node_report(self, node_id, history: list, user_id):
        current_node = history.pop()
        json_data = {
            "nodeHistoryList": history,
            "currentNode": current_node,
        }
        response = requests.get(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/data/interpretation/get?node_id={node_id}&user_id={user_id}",
            json=json_data,
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

    def generate_branch_report(self, analysis_id, branch_nodes, node_histories, node_figures, report_uuid, report_node, user_id, model):
        response = requests.post(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/report/branch",
            proxies=PROXIES,
            json={
                "ownerID": user_id,
                "analysisID": analysis_id,
                "uuid": report_uuid,
                "branchNodes": branch_nodes,
                "nodeHistories": node_histories,
                "nodeFigures": node_figures,
                "reportNode": report_node,
                "model": model,
            }
        )
        return response
    
    def generate_branch_report_automated(self, analysis_id, branch_nodes, node_histories, node_figures, report_uuid, report_node, user_id, model):
        response = requests.post(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/report/branch-automated",
            proxies=PROXIES,
            json={
                "ownerID": user_id,
                "analysisID": analysis_id,
                "uuid": report_uuid,
                "branchNodes": branch_nodes,
                "nodeHistories": node_histories,
                "nodeFigures": node_figures,
                "reportNode": report_node,
                "model": model,
            }
        )
        return response
    
    def select_figures_automated(self, analysis_id, branch_nodes, node_histories, node_figures, user_id, model):
        response = requests.post(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/report/select-figures-automated",
            proxies=PROXIES,
            json={
                "ownerID": user_id,
                "analysisID": analysis_id,
                "branchNodes": branch_nodes,
                "nodeHistories": node_histories,
                "nodeFigures": node_figures,
                "model": model,
            }
        )
        return response
    
    def dynamic_fb(self, user_request, node_id, history):
        current_node = history.pop()
        json_data = {
            "nodeHistoryList": history,
            "currentNode": current_node,
        }
        response = requests.post(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/dynamic_fb?node_id={node_id}&user_request={user_request}",
            proxies=PROXIES,
            json=json_data
        )
        return response
    
    def generate_figure_description(self, figure_url, figure_uuid, figure_name, node_name=None, user_id=None):
        post_data = {
            "figure_url": figure_url,
            "figure_uuid": figure_uuid,
            "figure_name": figure_name,
            "owner_id": user_id,
        }
        if node_name:
            post_data["node_name"] = node_name
            
        response = requests.post(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/figure/generate-description",
            proxies=PROXIES,
            json=post_data
        )
        return response
    
    def batch_generate_figure_descriptions(self, figures, user_id):
        post_data = {
            "figures": figures,
            "owner_id": user_id,
        }
        response = requests.post(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/figure/batch-generate-descriptions",
            proxies=PROXIES,
            json=post_data
        )
        return response
    
    def capture_data(self, user_request, user_id):
        post_data = {
            "user_request_prompt": user_request,
            "user_id": user_id,
        }
        response = requests.get(
            url=f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/data_capture/get",
            proxies=PROXIES,
            json=post_data
        )
        response = response.json()
        return response

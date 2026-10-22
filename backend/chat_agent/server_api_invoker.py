import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
GPT_WORKFLOW_SERVER_HOST = os.getenv("GPT_WORKFLOW_SERVER_HOST")
GPT_WORKFLOW_SERVER_PORT = os.getenv("GPT_WORKFLOW_SERVER_PORT", "5000")
MAIN_SERVER_HOST = os.getenv("MAIN_SERVER_HOST")
COMPUTATION_SERVER_HOST = os.getenv("COMPUTATION_SERVER_HOST")
DATA_SERVER_HOST = os.getenv("DATA_SERVER_HOST")
NETWORK_PROXY_HOST = os.environ.get("NETWORK_PROXY_HOST")
NETWORK_PROXY_PORT = os.environ.get("NETWORK_PROXY_PORT")

if NETWORK_PROXY_HOST and NETWORK_PROXY_PORT:
    PROXIES={
        "http": f"http://{NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}",
        "https": f"http://{NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}"
    }
else:
    PROXIES = None

SYSTEM_AGENT_KEY = os.getenv("SYSTEM_AGENT_KEY")

class ServerAPIInvoker:
    """Server API invoker for ChatAgent to communicate with omicairn-backend server"""

    def __init__(self, user_id):
        self.user_id = user_id
        self._login()

    def _login(self):
        # The system key is sent in a header (not the URL) so it does not end up in access logs.
        response = requests.post(
            f"{MAIN_SERVER_HOST}/user/login-by-system",
            params={"user_id": self.user_id},
            headers={"X-System-Agent-Key": SYSTEM_AGENT_KEY or ""},
            timeout=30
        )
        response.raise_for_status()
        self.headers = {
            "token": response.json()["data"]
        }
        
    def get_chat_information(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get chat information"""
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/v3.0/chat/get-information",
                params={"chat_id": chat_id},
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data')
            return None
        except Exception as e:
            print(f"Error getting chat information: {str(e)}")
            return None
    
    def update_chat_information(self, chat_id: str, updated_chat_attrs: Dict[str, Any]) -> bool:
        """Update chat information"""
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/v3.0/chat/update-chat-information",
                json={
                    "chat_id": chat_id,
                    "updated_chat_attrs": updated_chat_attrs
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            return result.get('code') == 200
        except Exception as e:
            print(f"Error updating chat information: {str(e)}")
            return False
    
    def get_chat_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        """Get chat messages"""
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/v3.0/chat/get-messages",
                params={"chat_id": chat_id, "limit": 2000, "offset": 0},
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data', {}).get('messages', [])
            return []
        except Exception as e:
            print(f"Error getting chat messages: {str(e)}")
            return []
    
    def create_chat_message(self, chat_id: str, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new chat message"""
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/v3.0/chat/create-message",
                json={
                    "chat_id": chat_id,
                    "message": message
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data')
            return None
        except Exception as e:
            print(f"Error creating chat message: {str(e)}")
            return None
    
    def update_chat_message(self, chat_message_id: str, updated_message_attrs: Dict[str, Any]) -> bool:
        """Update chat message"""
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/v3.0/chat/update-message",
                json={
                    "chat_message_id": chat_message_id,
                    "updated_message_attrs": updated_message_attrs
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            return result.get('code') == 200
        except Exception as e:
            print(f"Error updating chat message: {str(e)}")
            return False
        
    def update_batch_chat_messages(self, chat_message_ids: List[str], updated_message_attrs: Dict[str, Any]) -> int:
        """Batch update chat messages"""
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/v3.0/chat/update-batch-messages",
                json={
                    "chat_message_ids": chat_message_ids,
                    "updated_message_attrs": updated_message_attrs
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data', {}).get('updatedCount', 0)
            return 0
        except Exception as e:
            print(f"Error batch updating chat messages: {str(e)}")
            return 0
    
    def create_chat_sub_task(self, chat_id: str, chat_sub_task_attrs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new chat sub task"""
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/v3.0/chat/create-chat-sub-task",
                json={
                    "chat_id": chat_id,
                    "chat_sub_task_attrs": chat_sub_task_attrs
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data')
            return None
        except Exception as e:
            print(f"Error creating chat sub task: {str(e)}")
            return None
    
    def update_chat_sub_task(self, chat_sub_task_id: str, updated_chat_sub_task_attrs: Dict[str, Any]) -> bool:
        """Update chat sub task"""
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/v3.0/chat/update-chat-sub-task",
                json={
                    "chat_sub_task_id": chat_sub_task_id,
                    "updated_chat_sub_task_attrs": updated_chat_sub_task_attrs
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            return result.get('code') == 200
        except Exception as e:
            print(f"Error updating chat sub task: {str(e)}")
            return False
    
    def get_chat_sub_task(self, chat_sub_task_id: str) -> Optional[Dict[str, Any]]:
        """Get chat sub task"""
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/v3.0/chat/get-chat-sub-task",
                params={"chat_sub_task_id": chat_sub_task_id},
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data')
            return None
        except Exception as e:
            print(f"Error getting chat sub task: {str(e)}")
            return None
    
    def chat_with_llm(self, messages: List[Dict[str, str]], tools, model: str = "gpt-4o-mini") -> tuple:
        """Chat with LLM via GPT server"""
        try:
            # Calls the LLM workflow/gateway service (GPT_WORKFLOW_SERVER_HOST);
            # default port is 5000, configurable via GPT_WORKFLOW_SERVER_PORT
            response = requests.post(
                f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/v3.0/chat",
                json={
                    "messages": messages,
                    "model": model,
                    "tools": tools
                },
                proxies=PROXIES,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 200:
                data = result.get('data', {})
                return (
                    data.get('message', ''),
                    data.get('token_consumptions', {}),
                    data.get('model_time', 0),
                    data.get('tool_calls', [])[:1] if "tool_calls" in data and len(data["tool_calls"]) > 0 else []
                )
            else:
                raise Exception(f"LLM server error: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"Error calling LLM: {str(e)}")
            # Return empty response on error
            return "", {}, 0, []
        
    def get_analysis_information(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis information"""
        try:
            info_response = requests.get(
                f"{MAIN_SERVER_HOST}/analysis/get-info?analysis_id={analysis_id}",
                timeout=30,
                headers=self.headers
            )
            info_response.raise_for_status()
            info_result = info_response.json()
            if info_result.get('code') == 200:
                info = info_result.get('data')
            else:
                info = None
            
            nodes_response = requests.get(
                f"{MAIN_SERVER_HOST}/node/list/get?analysis_id={analysis_id}",
                timeout=30,
                headers=self.headers
            )
            nodes_response.raise_for_status()
            nodes_result = nodes_response.json()
            if nodes_result.get('code') == 200:
                nodes = nodes_result.get('data')
            else:
                nodes = None

            edges_response = requests.get(
                f"{MAIN_SERVER_HOST}/edge/list/get?analysis_id={analysis_id}",
                timeout=30,
                headers=self.headers
            )
            edges_response.raise_for_status()
            edges_result = edges_response.json()
            if edges_result.get('code') == 200:
                edges = edges_result.get('data')
            else:
                edges = None

            public_datas_response = requests.get(
                f"{MAIN_SERVER_HOST}/data/list/get?mode=public",
                timeout=30,
                headers=self.headers
            )
            public_datas_response.raise_for_status()
            public_datas_result = public_datas_response.json()
            if public_datas_result.get('code') == 200:
                public_datas = public_datas_result.get('data', [])
            else:
                public_datas = []

            imported_datas_response = requests.get(
                f"{MAIN_SERVER_HOST}/data/list/get?mode=imported&analysis_id={analysis_id}",
                timeout=30,
                headers=self.headers
            )
            imported_datas_response.raise_for_status()
            imported_datas_result = imported_datas_response.json()
            if imported_datas_result.get('code') == 200:
                imported_datas = imported_datas_result.get('data', [])
            else:
                imported_datas = []

            def reduce_node(node):
                return {
                    "computationResourceConfigure": node.get("computationResourceConfigure"),
                    "dataId": node.get("dataId"),
                    "dynamicGenerationId": node.get("dynamicGenerationId"),
                    "dynamicGenerationLocked": node.get("dynamicGenerationLocked"),
                    "functionBlockCurrentVersionId": node.get("functionBlockCurrentVersionId"),
                    "functionBlockId": node.get("functionBlockId"),
                    "functionBlockName": node.get("functionBlockName"),
                    "functionBlockVersionId": node.get("functionBlockVersionId"),
                    "functionBlockVersionPlotOnly": node.get("functionBlockVersionPlotOnly"),
                    "functionBlockVersionProgramLanguage": node.get("functionBlockVersionProgramLanguage"),
                    "id": node.get("id"),
                    "locked": node.get("locked"),
                    "name": node.get("name"),
                    "reportUuid": node.get("reportUuid"),
                    "state": node.get("state"),
                    "systemEnv": node.get("systemEnv"),
                    "tag": node.get("tag"),
                    "type": node.get("type"),
                    "x": node.get("x"),
                    "y": node.get("y")
                }

            def reduce_data(data):
                return {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "description": data.get("description"),
                    "species": data.get("species"),
                }

            return {
                "analysis-info": info,
                "nodes": [reduce_node(n) for n in nodes] if nodes else [],
                "edges": edges,
                "avaliable-datas": {
                    "public-datas": [reduce_data(d) for d in public_datas],
                    "imported-datas": [reduce_data(d) for d in imported_datas]
                }
            }
        except Exception as e:
            print(f"Error getting analysis information: {str(e)}")
            return None
    
    def get_branch_nodes(self, node_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get branch nodes for a given node"""
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/node/get-previous-node-list?node_id={node_id}&with_self=1",
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data', [])
            return None
        except Exception as e:
            print(f"Error getting previous nodes: {str(e)}")
            return None
        
    def get_branch_path(self, node_id: str, with_self: bool = False) -> Optional[Dict[str, Any]]:
        """Get branch path (nodes and edges) for a given node"""
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/node/get-previous-path?node_id={node_id}&with_self={1 if with_self else 0}",
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data', {})
            return None
        except Exception as e:
            print(f"Error getting previous path: {str(e)}")
            return None
        
    def get_avaliable_datasets(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get available datasets for an analysis"""
        try:
            public_datas_response = requests.get(
                f"{MAIN_SERVER_HOST}/data/list/get?mode=public",
                timeout=30,
                headers=self.headers
            )
            public_datas_response.raise_for_status()
            public_datas_result = public_datas_response.json()
            if public_datas_result.get('code') == 200:
                public_datas = public_datas_result.get('data', [])
            else:
                public_datas = []

            imported_datas_response = requests.get(
                f"{MAIN_SERVER_HOST}/data/list/get?mode=imported&analysis_id={analysis_id}",
                timeout=30,
                headers=self.headers
            )
            imported_datas_response.raise_for_status()
            imported_datas_result = imported_datas_response.json()
            if imported_datas_result.get('code') == 200:
                imported_datas = imported_datas_result.get('data', [])
            else:
                imported_datas = []

            def reduce_data(data):
                return {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "description": data.get("description"),
                    "species": data.get("species"),
                }

            return {
                "public-datas": [reduce_data(d) for d in public_datas],
                "imported-datas": [reduce_data(d) for d in imported_datas]
            }
        except Exception as e:
            print(f"Error getting available datasets: {str(e)}")
            return None
    
    def get_available_imported_datasets(self, analysis_id: str) -> List[Dict[str, Any]]:
        """Get available imported datasets for an analysis"""
        try:
            imported_datas_response = requests.get(
                f"{MAIN_SERVER_HOST}/data/list/get?mode=imported&analysis_id={analysis_id}",
                timeout=30,
                headers=self.headers
            )
            imported_datas_response.raise_for_status()
            imported_datas_result = imported_datas_response.json()
            if imported_datas_result.get('code') == 200:
                imported_datas = imported_datas_result.get('data', [])
            else:
                imported_datas = []

            def reduce_data(data):
                return {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "description": data.get("description"),
                    "species": data.get("species"),
                }

            return [reduce_data(d) for d in imported_datas]
        except Exception as e:
            print(f"Error getting available imported datasets: {str(e)}")
            return []
        
    def get_node_information(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node information"""
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/node/get-info?node_id={node_id}",
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data')
            return None
        except Exception as e:
            print(f"Error getting node information: {str(e)}")
            return None
        
    def get_recommended_datasets(self, user_request: str) -> List[Dict[str, Any]]:
        """Get recommended datasets based on user request"""
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/gpt/capture-data?user_request={user_request}",
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data', [])
            return []
        except Exception as e:
            print(f"Error getting recommended datasets: {str(e)}")
            return []


    def plan_auto_genie_task(self, start_node_id: str, user_request: str, max_node:int, generate_mode: str, llm_model):
        """Launch AutoGenie for dynamic generation"""
        try:
            response = requests.post(
                f"{COMPUTATION_SERVER_HOST}/dynamic-generation/generate-plan",
                json={
                    "previous_node_id": start_node_id,
                    "max_node": max_node,
                    "max_branch": 1,
                    "user_request": user_request,
                    "computation_resource_configure": json.dumps({"ram":120,"vcpu":16,"timeout":21600,"gpu":0,"system_env":"server-local"}, indent=4),
                    "generation_mode": generate_mode,
                    "max_debug": 6,
                    "llm_model": llm_model,
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            if result.get('code') == 200:
                return result.get('data')
            return None
        except Exception as e:
            print(f"Error planning AutoGenie task: {str(e)}")
            return None

    def prepare_auto_genie(self, dynamic_generation_id: str, start_node_id: str) -> Optional[Dict[str, Any]]:
        """Launch dynamic generation"""
        try:
            response = requests.post(
                f"{COMPUTATION_SERVER_HOST}/dynamic-generation/create-with-plan",
                json={
                    "dynamic_generation_id": dynamic_generation_id,
                    "previous_node_id": start_node_id
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            return result.get('code') == 200, result.get('message')
        except Exception as e:
            print(f"Error planning AutoGenie task: {str(e)}")
            return False, str(e)
        
    def run_auto_genie(self, dynamic_generation_id: str) -> bool:
        """Run dynamic generation"""
        try:
            response = requests.post(
                f"{COMPUTATION_SERVER_HOST}/dynamic-generation/launch-with-plan?dynamic_generation_id={dynamic_generation_id}",
                timeout=30,
                headers=self.headers
            )
            print(response.text)
            response.raise_for_status()
            result = response.json()    
            return result.get('code') == 200, result.get('message')
        except Exception as e:
            print(f"Error running AutoGenie task: {str(e)}")
            return False, str(e)
        
    def get_data_info(self, data_id: str) -> Optional[Dict[str, Any]]:
        """Get data information"""
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/data/get-data-info?data_id={data_id}",
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            if result.get('code') == 200:
                return result.get('data')
            return None
        except Exception as e:
            print(f"Error getting data information: {str(e)}")
            return None
        
    def create_data_node(self, analysis_id: str, data_id: str, node_name: str) -> Optional[Dict[str, Any]]:
        """Create a new data node"""
        try: 
            data_id = int(data_id)
        except Exception:
            return False, f"Invalid data_id: {data_id}. You must use 'data_id' from analysis's available_datas, not 'id' from capture_data results.", None

        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/node/create",
                data={
                    "node_type": "data node",
                    "analysis_id": analysis_id,
                    "data_id": data_id,
                    "name": node_name,
                    "x": 0,
                    "y": 0,
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            return result.get('code') == 200, result.get('message'), result.get('data')
        except Exception as e:
            print(f"Error creating data node: {str(e)}")
            return False, str(e), None
        
    def get_computation_details(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get computation details for a node"""
        try:
            latest_computation_response = requests.get(
                f"{MAIN_SERVER_HOST}/computation/latest-by-node/get?node_id={node_id}",
                timeout=30,
                headers=self.headers
            )
            latest_computation_response.raise_for_status()
            latest_computation_result = latest_computation_response.json()
            if latest_computation_result.get('code') != 200:
                return None
            computation_basic_info = latest_computation_result.get('data', {})
        except Exception as e:
            print(f"Error getting computation details: {str(e)}")
            return None
        
        computation_id = latest_computation_result.get('data', {}).get('id')
        try:
            response = requests.get(
                f"{COMPUTATION_SERVER_HOST}/computation/get-logs?computation_id={computation_id}",
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            computation_logs = result.get('data', None)
        except Exception as e:
            print(f"Error getting computation logs: {str(e)}")
            computation_logs = None

        function_block_id = computation_basic_info.get('functionBlockId')
        function_block_version_id = computation_basic_info.get('functionBlockVersionId')
        if not function_block_id or not function_block_version_id:
            function_block_info = None
            function_block_version_info = None
        else:
            try:
                response = requests.get(
                    f"{MAIN_SERVER_HOST}/function-block-v1/get-information?function_block_id={function_block_id}",
                    timeout=30,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()    
                if result.get('code') == 200:
                    function_block_info = result.get('data', None)
                else:
                    function_block_info = None
            except Exception as e:
                print(f"Error getting function block info: {str(e)}")
                function_block_info = None

            try:
                response = requests.get(
                    f"{MAIN_SERVER_HOST}/function-block-v1/get-version-information?function_block_version_id={function_block_version_id}",
                    timeout=30,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()    
                if result.get('code') == 200:
                    function_block_version_info = result.get('data', None)
                else:
                    function_block_version_info = None

            except Exception as e:
                print(f"Error getting function block version info: {str(e)}")
                function_block_version_info = None
        return {
            "computation_basic_info": computation_basic_info,
            "computation_logs": computation_logs,
            "function_block_info": function_block_info,
            "function_block_version_info": function_block_version_info
        }

    def get_function_block_codes(self, function_block_id: str, function_block_version_id: str) -> Optional[Dict[str, Any]]:
        """Get function block codes"""
        if not function_block_id or not function_block_version_id:
            return None
        
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/function-block-v1/get-version-information?function_block_version_id={function_block_version_id}",
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            if result.get('code') == 200:
                function_block_version_info = result.get('data', None)
            else:
                function_block_version_info = None

        except Exception as e:
            print(f"Error getting function block version info: {str(e)}")
            return None
        
        fb_id = function_block_version_info.get('functionBlockId', None) if function_block_version_info else None
        if str(fb_id) != str(function_block_id):
            print(f"Function block ID mismatch: {fb_id} vs {function_block_id}")
            return None
        def get_file_names(program_language: str):
            if program_language.lower() == "python":
                return ["install.sh", "function_block.py", "static-config.json", "requirements.txt"]
            elif program_language.lower() == "r":
                return ["install.sh", "function_block.R", "static-config.json", "libs.R"]
            elif program_language.lower() == "bash":
                return ["install.sh", "function_block.sh", "static-config.json", "libs.sh"]
            else:
                print(f"Unsupported programming language: {program_language}")
                raise Exception(f"Unsupported programming language: {program_language}")
            
        def get_file_content(file_dict, fbv_id: str, file_name: str) -> Optional[str]:
            try:
                response = requests.get(
                    f"{MAIN_SERVER_HOST}/function-block-v1/get-version-content?function_block_version_id={fbv_id}&file={file_name}",
                    timeout=30,
                    headers=self.headers
                )
                response.raise_for_status()
                if response.status_code == 200:
                    file_dict[file_name] = response.json().get("data", None)
                else:
                    print(f"Empty file {file_name}: {response.status_code}")
                    file_dict[file_name] = None
            except Exception as e:
                print(f"Error fetching {file_name}: {str(e)}")
                file_dict[file_name] = None
        files_content = {}
        try:
            program_language = function_block_version_info.get('programLanguage')
            file_names = get_file_names(program_language)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(get_file_content, files_content, function_block_version_id, file_name) for file_name in file_names]
                concurrent.futures.wait(futures)
        except Exception as e:
            print(f"Error getting function block codes: {str(e)}")
            return None
        files_content = {k: v for k, v in files_content.items() if v is not None}
        return files_content
    
    def get_function_block_information(self, function_block_id: str) -> Optional[Dict[str, Any]]:
        """Get function block information"""
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/function-block-v1/get-information?function_block_id={function_block_id}",
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            if result.get('code') == 200:
                return result.get('data')
            return None
        except Exception as e:
            print(f"Error getting function block information: {str(e)}")
            return None

    def get_public_function_block_groups(self) -> Optional[List[Dict[str, Any]]]:
        """Get public function block groups"""
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/function-block-v1/get-public-group-list",
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            success = result.get('code') == 200
            message = result.get('message', '')
            fbs = result.get('data', [])
            if not success:
                fbs = []
                return success, message, fbs
            def reduce_fb(fb):
                return {
                    "currentVersionId": fb.get("currentVersionId"),
                    "id": fb.get("id"),
                    "name": fb.get("name")
                }
            def reduce_group(group):
                return {
                    "functionBlockList": [reduce_fb(fb) for fb in group.get("functionBlockList", [])],
                    "groupId": group.get("id"),
                    "name": group.get("name")
                }
            fbs = [reduce_group(g) for g in fbs]
            return success, message, fbs
        except Exception as e:
            print(f"Error getting public function block groups: {str(e)}")
            return False, str(e), []

    def create_computation_node(self, analysis_id: str, function_block_id: str, function_block_version_id: str, node_name: str, x: int=None, y: int=None) -> Optional[Dict[str, Any]]:
        """Create a new computation node"""
        try:
            if not function_block_id or not function_block_version_id:
                return False, "function_block_id and function_block_version_id are required", None
            else:
                function_block_id = int(function_block_id)
                function_block_version_id = int(function_block_version_id)
        except Exception:
            return False, f"Invalid function_block_id or function_block_version_id", None

        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/node/create",
                data={
                    "node_type": "computation node",
                    "analysis_id": analysis_id,
                    "function_block_id": function_block_id,
                    "function_block_version_id": function_block_version_id,
                    "name": node_name,
                    "x": x if x is not None else 0,
                    "y": y if y is not None else 0,
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            return result.get('code') == 200, result.get('message'), result.get('data')
        except Exception as e:
            print(f"Error creating computation node: {str(e)}")
            return False, str(e), None

    def create_report_node(self, analysis_id: str, node_name: str, x: int=None, y: int=None) -> Optional[Dict[str, Any]]:
        """Create a new report node"""
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/node/create",
                data={
                    "node_type": "report node",
                    "x": x if x is not None else 0,
                    "y": y if y is not None else 0,
                    "analysis_id": analysis_id,
                    "name": node_name,
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            return result.get('code') == 200, result.get('message'), result.get('data')
        except Exception as e:
            print(f"Error creating report node: {str(e)}")
            return False, str(e), None

        
    def create_edge(self, analysis_id: str, source_node_id: str, target_node_id: str) -> Optional[Dict[str, Any]]:
        """Create a new edge"""
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/edge/create",
                data={
                    "analysis_id": analysis_id,
                    "source_node_id": source_node_id,
                    "target_node_id": target_node_id,
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            return result.get('code') == 200, result.get('message'), result.get('data')
        except Exception as e:
            print(f"Error creating edge: {str(e)}")
            return False, str(e), None

    def create_report(self, analysis_id, branch_nodes, report_node, model) -> Optional[Dict[str, Any]]:
        """Create a new report"""
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/gpt/generate-branch-report",
                json={
                    "analysis_id": analysis_id,
                    "branch_nodes": branch_nodes,
                    "report_node": report_node,
                    "model": model,
                },
                timeout=600,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            return result.get('code') == 200, result.get('message'), result.get('data')
        except Exception as e:
            print(f"Error creating reporter: {str(e)}")
            return False, str(e), None
        
    def launch_computation(self, analysis_id, node_id_list, edge_id_list) -> bool:
        """Launch computation for a node"""
        try:
            response = requests.post(
                f"{COMPUTATION_SERVER_HOST}/task/dispatch",
                json={
                    "analysis_id": analysis_id,
                    "node_id_list": node_id_list,
                    "edge_id_list": edge_id_list
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            return result.get('code') == 200, result.get('message'), result.get('data')
        except Exception as e:
            print(f"Error launching computation: {str(e)}")
            return False, str(e), None

    def summary_history_messages(self, messages: List[dict], model: str = "gpt-4o-mini", max_tokens: int = 1024) -> Optional[Dict[str, Any]]:
        """Summarize history messages"""
        """ Returns:
        {
            "code": 200,
            "data": {
                "summary": "Summarized content",
                "token_consumptions": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50
                },
                "model_time": 1.5  # seconds
            }
        }"""
        try:
            response = requests.post(
                f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/v3.0/chat/summarize-messages",
                json={
                    "messages": messages,
                    "model": model,
                    "max_tokens": max_tokens
                },
                timeout=600,
                headers=self.headers,
                proxies=PROXIES
            )
            response.raise_for_status()
            result = response.json()

            return result.get('code') == 200, result.get("message"), result.get('data', {})
        except Exception as e:
            print(f"Error summarizing messages: {str(e)}")
            return False, str(e), None

    def list_files(self, prefix: str, analysis_id: str) -> Optional[List[Dict[str, Any]]]:
        """List files in storage using the /list API"""
        try:
            params = {"s3_prefix": prefix, "analysis_id": analysis_id}

            response = requests.get(
                f"{MAIN_SERVER_HOST}/file/list/get",
                params=params,
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data', {})
            return {}
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            return None
        
    def read_file_from_storage(self, file_key: str, analysis_id: str) -> Optional[bytes]:
        """Read file content from storage using the /content/get API"""
        try:
            params = {"file_key": file_key, "analysis_id": analysis_id}
            
            response = requests.get(
                f"{MAIN_SERVER_HOST}/file/content/get",
                params=params,
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Error reading file from storage: {str(e)}")
            return None

    def copy_files_between_s3_folders(self, file_name: str, source_key: str, destination_key: str) -> tuple[bool, str]:
        """Copy files between S3 folders using the /copy API"""
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/file/copy",
                json={
                    "file_name": file_name,
                    "source_key": source_key,
                    "destination_key": destination_key
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            success = result.get('code') == 200
            destination_key_result = result.get('data', {}).get('destination_key', '') if success else ''
            return success, destination_key_result
        except Exception as e:
            print(f"Error copying files between S3 folders: {str(e)}")
            return False, ''

    def rename_file_in_s3_storage(self, source_key: str, new_name: str) -> bool:
        """Rename file in S3 storage using the /rename API"""
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/file/rename",
                json={
                    "source_key": source_key,
                    "new_name": new_name
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            return result.get('code') == 200
        except Exception as e:
            print(f"Error renaming file in S3 storage: {str(e)}")
            return False

    def check_folder_exist_in_s3_storage(self, folder_key: str) -> bool:
        """Check if a folder exists in S3 storage using the /check-folder-exist API"""
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/file/check-folder-exist",
                params={"folder_key": folder_key},
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            return result.get('code') == 200 and result.get('data', {}).get('exists', False)
        except Exception as e:
            print(f"Error checking file existence in S3 storage: {str(e)}")
            return False
        
    def create_data_framework(self, name: str, data_from: str, upload_type: str, species: str, description: str) -> Optional[Dict[str, Any]]:
        """Create a new data framework for organizing bioinformatics data"""
        try:
            form_data = {
                'data_from': data_from,
                'upload_type': upload_type,
                'species': species,
                'description': description,
                'name': name
            }

            response = requests.post(
                f"{MAIN_SERVER_HOST}/data/framework/create",
                data=form_data,
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data')
            return None
        except Exception as e:
            print(f"Error creating data framework: {str(e)}")
            return None

    def assemble_data_components(self, data_frame_id: str) -> bool:
        """Assemble uploaded data components into a complete dataset"""
        try:
            response = requests.get(
                f"{DATA_SERVER_HOST}/pretreatment/confirm-data-components-upload",
                params={"data_id": data_frame_id},
                timeout=300,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            return result.get('code') == 200
        except Exception as e:
            print(f"Error assembling data components: {str(e)}")
            return False

    def import_data_to_analysis(self, analysis_id: str, data_ids: List[str]) -> bool:
        """Import assembled datasets into a specific analysis project"""
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/analysis/data/import",
                json={
                    "analysis_id": analysis_id,
                    "data_ids": data_ids
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            return result.get('code') == 200
        except Exception as e:
            print(f"Error importing data to analysis: {str(e)}")
            return False

    def update_function_block_version_is_v2(self, function_block_version_id: str, is_v2: bool) -> bool:
        """Update the is_v2 field of a function block version"""
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/function-block-v1/update-version-is-v2",
                json={
                    "function_block_version_id": function_block_version_id,
                    "is_v2": is_v2
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            return result.get('code') == 200
        except Exception as e:
            print(f"Error updating function block version is_v2: {str(e)}")
            return False
        
    def record_llm_consumption(self, llm_consumption):
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/gpt/record-consumption",
                json={
                    "consumption": llm_consumption
                },
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            print(f"Error recording LLM consumption: {str(e)}")
            return None
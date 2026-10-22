import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os


def ensure_url_scheme(url: str) -> str:
    """Ensure URL has http:// or https:// scheme prefix."""
    if not url:
        return url
    url = url.rstrip("/")
    if not url.startswith("http://") and not url.startswith("https://"):
        # Default to http:// for internal services
        url = f"http://{url}"
    return url


MAIN_SERVER_HOST = ensure_url_scheme(os.getenv("MAIN_SERVER_HOST", ""))
COMPUTATION_SERVER_HOST = ensure_url_scheme(os.getenv("COMPUTATION_SERVER_HOST", ""))

SYSTEM_AGENT_KEY = os.getenv("SYSTEM_AGENT_KEY")

class ServerAPIInvoker:

    def __init__(self, user_id):
        self.user_id = user_id
        self._login()

    def _login(self):
        if not MAIN_SERVER_HOST:
            raise ValueError("MAIN_SERVER_HOST environment variable is not set")
        if not SYSTEM_AGENT_KEY:
            raise ValueError("SYSTEM_AGENT_KEY environment variable is not set")

        url = f"{MAIN_SERVER_HOST}/server/user/login-by-system?user_id={self.user_id}"
        try:
            response = requests.post(url, headers={"X-System-Agent-Key": SYSTEM_AGENT_KEY}, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to server at {MAIN_SERVER_HOST}: {e}")

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            raise ValueError(f"Server returned invalid JSON. Status: {response.status_code}, Body: {response.text[:200]}")

        if "data" not in data:
            raise ValueError(f"Login response missing 'data' field. Response: {data}")

        self.headers = {
            "token": data["data"]
        }
        
    def get_branch_path(self, node_id: str, with_self: bool = False) -> Optional[Dict[str, Any]]:
        """Get branch path (nodes and edges) for a given node"""
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/server/node/get-previous-path?node_id={node_id}&with_self={1 if with_self else 0}",
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
        
    def get_node_information(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node information"""
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/server/node/get-info?node_id={node_id}",
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
        
    def get_computation_details(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get computation details for a node"""
        try:
            latest_computation_response = requests.get(
                f"{MAIN_SERVER_HOST}/server/computation/latest-by-node/get?node_id={node_id}",
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
                f"{COMPUTATION_SERVER_HOST}/computation-server/computation/get-logs?computation_id={computation_id}",
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
                    f"{MAIN_SERVER_HOST}/server/function-block-v1/get-information?function_block_id={function_block_id}",
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
                    f"{MAIN_SERVER_HOST}/server/function-block-v1/get-version-information?function_block_version_id={function_block_version_id}",
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

    def get_autogenie_task_information(self, generation_id: str) -> Optional[Dict[str, Any]]:
        """Get AutoGenie task information"""
        try:
            response = requests.get(
                f"{COMPUTATION_SERVER_HOST}/computation-server/dynamic-generation/get-info?dynamic_generation_id={generation_id}",
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            if result.get('code') == 200:
                return result.get('data')
            return None
        except Exception as e:
            print(f"Error getting AutoGenie task information: {str(e)}")
            return None
        
    def get_autogenie_plan(self, generation_id: str, node_id: str) -> Optional[Dict[str, Any]]:
        """Get AutoGenie plan for a given generation and node"""
        try:
            response = requests.get(
                f"{COMPUTATION_SERVER_HOST}/computation-server/dynamic-generation/get-plan?generation_id={generation_id}&previous_node_id={node_id}",
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            if result.get('code') == 200:
                return result.get('data')
            return None
        except Exception as e:
            print(f"Error getting AutoGenie plan: {str(e)}")
            return None
        
    def get_node_extra_files(self, node_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get extra files associated with a node"""
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/server/node/list-params-files?node_id={node_id}",
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            if result.get('code') == 200:
                return result.get('data', [])
            return None
        except Exception as e:
            print(f"Error getting node extra files: {str(e)}")
            return None
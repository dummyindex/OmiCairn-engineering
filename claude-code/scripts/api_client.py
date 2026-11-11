"""
API client for the claude-code executor scripts

Provides API calls to:
1. backend (MAIN_SERVER_HOST) - Node and FunctionBlock operations
2. worker (COMPUTATION_SERVER_HOST) - Computation operations
"""
import requests
import json
import os
import sys
from typing import Dict, Any, Optional


def _ensure_url_scheme(url: str) -> str:
    """Accept both "host:port" (as passed by the worker) and "http(s)://host:port"."""
    url = (url or "").rstrip("/")
    if url and not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    return url


MAIN_SERVER_HOST = _ensure_url_scheme(os.getenv("MAIN_SERVER_HOST", ""))
COMPUTATION_SERVER_HOST = _ensure_url_scheme(os.getenv("COMPUTATION_SERVER_HOST", ""))
SYSTEM_AGENT_KEY = os.getenv("SYSTEM_AGENT_KEY")


class APIClient:
    """API Client for server communications"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.headers = {}
        self._login()
    
    def _login(self):
        """Login to main server and get token"""
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/server/user/login-by-system",
                params={
                    "user_id": self.user_id
                },
                headers={"X-System-Agent-Key": SYSTEM_AGENT_KEY or ""},
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            if result.get('code') == 200:
                self.headers = {"token": result.get('data')}
            else:
                error_msg = f"Login failed with code {result.get('code')}: {result.get('message')}"
                raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            raise
        except Exception as e:
            raise
    
    def copy_node(self, node_id: str, with_edges: int = 1) -> Optional[Dict[str, Any]]:
        """
        Copy a node using /node/copy endpoint

        Args:
            node_id: ID of the node to copy
            with_edges: Whether to copy edges (1 = yes, 0 = no)

        Returns:
            Dict with new node information or None
        """
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/server/node/copy",
                params={
                    "node_id": node_id,
                    "with_edges": "1" if with_edges else "0"
                },
                headers=self.headers,
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            if result.get('code') == 200:
                new_node_id = result.get('data', {}).get('id')
                return result.get('data')
            else:
                error_msg = f"Failed to copy node with code {result.get('code')}: {result.get('message')}"
                return None
        except requests.exceptions.RequestException as e:
            return None
        except Exception as e:
            return None
    
    def edit_node(self, node_id: str, attrs: Dict[str, Any]) -> bool:
        """
        Edit a node using /node/edit endpoint

        Args:
            node_id: ID of the node to edit
            attrs: Dictionary of attributes to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure Content-Type is set
            request_headers = self.headers.copy()
            request_headers['Content-Type'] = 'application/json'

            response = requests.post(
                f"{MAIN_SERVER_HOST}/server/node/edit",
                params={"node_id": node_id},
                json=attrs,
                headers=request_headers,
                timeout=60
            )

            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return True
            else:
                error_msg = f"Failed to edit node with code {result.get('code')}: {result.get('message')}"
                return False
        except requests.exceptions.RequestException as e:
            return False
        except Exception as e:
            return False
    
    def create_function_block_version(
        self,
        function_block_id: str,
        version_name: str,
        file_size: int
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new function block version using /function-block-v1/create-version endpoint

        Args:
            function_block_id: ID of the function block
            version_name: Name for the new version
            file_size: Size of the zip file to upload

        Returns:
            Dict with version and s3Info or None
        """
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/server/function-block-v1/create-version",
                data={
                    "function_block_id": function_block_id,
                    "version_name": version_name,
                    "file_size": file_size
                },
                headers=self.headers,
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            if result.get('code') == 200:
                data = result.get('data', {})
                version_id = data.get('version', {}).get('id')
                return data
            else:
                error_msg = f"Failed to create version with code {result.get('code')}: {result.get('message')}"
                return None
        except requests.exceptions.RequestException as e:
            return None
        except Exception as e:
            return None

    def create_function_block(
        self,
        fb_name: str,
        fb_type: str,
        version_name: str,
        file_size: int,
        group_id: Optional[str] = None,
        fb_alt_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new function block using /function-block-v1/create endpoint

        Args:
            fb_name: display name of the function block
            fb_type: type string
            version_name: first version name
            file_size: size of the uploaded zip file
            group_id: optional group id
            fb_alt_name: optional alternate display name (sent as the `fb_alt_name` form field)

        Returns:
            dict with version and s3Info or None
        """
        try:
            data = {
                "fb_name": fb_name,
                "fb_type": fb_type,
                "version_name": version_name,
                "file_size": file_size
            }
            if group_id is not None:
                data["group_id"] = group_id
            if fb_alt_name is not None:
                data["fb_alt_name"] = fb_alt_name

            response = requests.post(
                f"{MAIN_SERVER_HOST}/server/function-block-v1/create",
                data=data,
                headers=self.headers,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data')
            else:
                return None
        except requests.exceptions.RequestException as e:
            return None
        except Exception as e:
            return None

    # Note: public create endpoint removed per project policy. If you need to
    # create public function blocks, call the server endpoint directly or
    # re-add a client wrapper here with appropriate access control.
    
    def create_computation(self, attrs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new computation using /computation/create endpoint

        Args:
            attrs: Dictionary of computation attributes

        Returns:
            Created computation dict or None
        """
        try:
            response = requests.post(
                f"{COMPUTATION_SERVER_HOST}/computation-server/computation/create",
                json=attrs,
                headers=self.headers,
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            if result.get('code') == 200:
                computation = result.get('data', {})
                comp_id = computation.get('id')
                return computation
            else:
                error_msg = f"Failed to create computation with code {result.get('code')}: {result.get('message')}"
                return None
        except requests.exceptions.RequestException as e:
            return None
        except Exception as e:
            return None
    
    def update_computation(
        self,
        computation_id: str,
        attrs: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a computation using /computation/update endpoint

        Args:
            computation_id: ID of the computation to update
            attrs: Dictionary of attributes to update

        Returns:
            Updated computation dict or None
        """
        try:
            response = requests.post(
                f"{COMPUTATION_SERVER_HOST}/computation-server/computation/update",
                params={"computation_id": computation_id},
                json=attrs,
                headers=self.headers,
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            if result.get('code') == 200:
                return result.get('data')
            else:
                error_msg = f"Failed to update computation with code {result.get('code')}: {result.get('message')}"
                return None
        except requests.exceptions.RequestException as e:
            return None
        except Exception as e:
            return None
    
    def upload_to_s3(self, s3_info: Dict[str, Any], file_path: str) -> bool:
        """
        Upload a file to S3 using presigned URL

        Args:
            s3_info: S3 upload information from API
            file_path: Path to the file to upload

        Returns:
            True if successful, False otherwise
        """
        try:
            # Handle different s3_info structures
            # New structure: {"presigned_url": {"url": "...", "fields": {...}}, ...}
            # Old structure: {"url": "...", "fields": {...}}
            if 'presigned_url' in s3_info:
                presigned = s3_info.get('presigned_url', {})
                upload_url = presigned.get('url')
                fields = presigned.get('fields', {})
            else:
                upload_url = s3_info.get('url')
                fields = s3_info.get('fields', {})

            if not upload_url:
                return False

            file_size = os.path.getsize(file_path)

            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    upload_url,
                    data=fields,
                    files=files,
                    timeout=600  # 10 minutes for large files
                )

                if response.status_code in [200, 204]:
                    return True
                else:
                    return False

        except requests.exceptions.RequestException as e:
            return False
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    
    def preprocess_function_block_version(self, function_block_version_id: str) -> bool:
        """
        Preprocess a function block version using /function-block-v1/preprocess-version endpoint

        Args:
            function_block_version_id: ID of the function block version to preprocess

        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/server/function-block-v1/preprocess-version",
                params={"function_block_version_id": function_block_version_id},
                headers=self.headers,
                timeout=300  # 5 minutes for preprocessing
            )

            response.raise_for_status()
            result = response.json()

            if result.get('code') == 200:
                return True
            else:
                error_msg = f"Failed to preprocess version with code {result.get('code')}: {result.get('message')}"
                return False
        except requests.exceptions.RequestException as e:
            return False
        except Exception as e:
            return False

    def get_group_list(self, owner_id: str, show_function_block_list: int = 1) -> Optional[list]:
        """
        Get function block group list for a given owner using /function-block-v1/get-group-list

        Args:
            owner_id: user id to fetch groups for
            show_function_block_list: 1 to include FB list inside groups, 0 otherwise

        Returns:
            list of groups or None
        """
        try:
            response = requests.get(
                f"{MAIN_SERVER_HOST}/server/function-block-v1/get-group-list",
                params={
                    "owner_id": owner_id,
                    "show_function_block_list": str(show_function_block_list)
                },
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data')
            else:
                return None
        except requests.exceptions.RequestException as e:
            return None
        except Exception as e:
            return None

    def create_group(self, name: str, alt_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create a function block group using /function-block-v1/create-group

        Args:
            name: group name
            alt_name: optional alternate display name (sent as the `alt_name` query parameter)

        Returns:
            created group dict or None
        """
        try:
            params = {"name": name}
            if alt_name is not None:
                params["alt_name"] = alt_name

            response = requests.post(
                f"{MAIN_SERVER_HOST}/server/function-block-v1/create-group",
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data')
            else:
                return None
        except requests.exceptions.RequestException as e:
            return None
        except Exception as e:
            return None

    def record_llm_consumption(
        self,
        consumption: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Record LLM consumption using /gpt/record-consumption endpoint

        Args:
            consumption: Dictionary with consumption data including:
                - promptTokens: int
                - completionTokens: int
                - reasoningTokens: int (optional)
                - totalTokens: int
                - cost: float (optional)
                - model: str
                - functionality: str
                - functionalityTaskId: int
                - nodeId: int

        Returns:
            Dict with consumption record including id, or None
        """
        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/server/gpt/record-consumption",
                json={"consumption": consumption},
                headers=self.headers,
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            if result.get('code') == 200:
                data = result.get('data', {})
                consumption_id = data.get('id')
                return data
            else:
                error_msg = f"Failed to record consumption with code {result.get('code')}: {result.get('message')}"
                return None
        except requests.exceptions.RequestException as e:
            return None
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None
    
    def create_agent_session(
        self,
        agent_type: str,
        status: str,
        current_node_id: Optional[int] = None,
        current_analysis_id: Optional[int] = None,
        current_computation_id: Optional[int] = None,
        consumption_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create an agent session record using /computation/create-agent-session endpoint

        Args:
            agent_type: Type of agent (e.g., 'code_agent', 'visualizer_agent', 'job_reviewer')
            status: Session status
            current_node_id: Optional node ID
            current_analysis_id: Optional analysis ID
            current_computation_id: Optional computation ID
            consumption_id: Optional LLM consumption ID

        Returns:
            Dict with session record including id, or None
        """
        try:
            request_data = {
                "agent_type": agent_type,
                "status": status
            }

            if current_node_id is not None:
                request_data["current_node_id"] = current_node_id
            if current_analysis_id is not None:
                request_data["current_analysis_id"] = current_analysis_id
            if current_computation_id is not None:
                request_data["current_computation_id"] = current_computation_id
            if consumption_id is not None:
                request_data["consumption_id"] = consumption_id

            response = requests.post(
                f"{COMPUTATION_SERVER_HOST}/computation-server/computation/create-agent-session",
                json=request_data,
                headers=self.headers,
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            if result.get('code') == 200:
                data = result.get('data', {})
                session_id = data.get('id')
                return data
            else:
                error_msg = f"Failed to create agent session with code {result.get('code')}: {result.get('message')}"
                return None
        except requests.exceptions.RequestException as e:
            return None
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None

    def upload_action_records(
        self,
        computation_id: str,
        actions: list
    ) -> bool:
        """
        Upload code agent action records to S3 using /code-agent-proxy/upload-action-records endpoint

        Args:
            computation_id: ID of the computation
            actions: List of action records from tool_call_records

        Returns:
            True if successful, False otherwise
        """
        try:
            request_data = {
                "computation_id": computation_id,
                "actions": actions
            }

            response = requests.post(
                f"{COMPUTATION_SERVER_HOST}/computation-server/code-agent-proxy/upload-action-records",
                json=request_data,
                headers=self.headers,
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            if result.get('code') == 200:
                return True
            else:
                error_msg = f"Failed to upload action records with code {result.get('code')}: {result.get('message')}"
                return False
        except requests.exceptions.RequestException as e:
            return False
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False


    def store_autogenie_plan(self, generation_id: str, node_id: str, plan: Dict[str, Any]) -> bool:
        """Store AutoGenie plan for a given generation and node"""
        try:
            response = requests.post(
                f"{COMPUTATION_SERVER_HOST}/computation-server/dynamic-generation/store-plan",
                json={
                    "dynamic_generation_id": generation_id,
                    "previous_node_id": node_id,
                    "plan": plan
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            return result.get('code') == 200
        except Exception as e:
            print(f"Error storing AutoGenie plan: {str(e)}")
            return False
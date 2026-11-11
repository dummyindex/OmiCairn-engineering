import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

def _with_scheme(host: Optional[str]) -> str:
    """Accept both "host:port" (worker convention) and "http(s)://host:port"."""
    host = (host or "").rstrip("/")
    if host and not host.startswith(("http://", "https://")):
        host = f"http://{host}"
    return host


# Main server (omicairn-backend) for user-related APIs; same value as the rest of the worker
MAIN_SERVER_HOST = _with_scheme(os.getenv("MAIN_SERVER_HOST"))

# Computation server (omicairn-worker) for computation-related APIs
COMPUTATION_SERVER_HOST = _with_scheme(os.getenv("COMPUTATION_SERVER_HOST"))
SYSTEM_AGENT_KEY = os.getenv("SYSTEM_AGENT_KEY")

NETWORK_PROXY_HOST = os.environ.get("NETWORK_PROXY_HOST")
NETWORK_PROXY_PORT = os.environ.get("NETWORK_PROXY_PORT")

GPT_WORKFLOW_SERVER_HOST = os.environ.get("GPT_WORKFLOW_SERVER_HOST")
GPT_WORKFLOW_SERVER_PORT = os.environ.get("GPT_WORKFLOW_SERVER_PORT")

# Optional outbound HTTP proxy; requests uses no proxy when unset.
PROXIES = {
    "http": f"http://{NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}",
    "https": f"http://{NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}"
} if NETWORK_PROXY_HOST and NETWORK_PROXY_PORT else None



class ServerAPIInvoker:
    """Server API invoker for AutoGenieAgent to communicate with omicairn-worker server"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._login()

    def _login(self):
        """Login to get authentication token"""
        response = requests.post(
            f"{MAIN_SERVER_HOST}/server/user/login-by-system?user_id={self.user_id}",
            headers={"X-System-Agent-Key": SYSTEM_AGENT_KEY or ""}
        )
        self.headers = {
            "token": response.json()["data"]
        }

    def get_dynamic_generation_info(self, dynamic_generation_id: str) -> Optional[Dict[str, Any]]:
        """Get dynamic generation information"""
        try:
            response = requests.get(
                f"{COMPUTATION_SERVER_HOST}/computation-server/dynamic-generation/get-info",
                params={"dynamic_generation_id": dynamic_generation_id},
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data')
            return None
        except Exception as e:
            print(f"Error getting dynamic generation info: {str(e)}")
            return None

    def update_dynamic_generation_info(self, dynamic_generation_id: str, updated_attrs: Dict[str, Any]) -> bool:
        """Update dynamic generation information"""
        try:
            response = requests.post(
                f"{COMPUTATION_SERVER_HOST}/computation-server/dynamic-generation/update-info",
                json={
                    "dynamic_generation_id": dynamic_generation_id,
                    "updated_attrs": updated_attrs
                },
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            return result.get('code') == 200
        except Exception as e:
            print(f"Error updating dynamic generation info: {str(e)}")
            return False

    def chat_with_llm(self, messages: List[Dict[str, str]], tools, model: str = "gpt-4o-mini") -> tuple:
        """Chat with LLM via GPT server"""
        try:
            # Calls the LLM gateway service (GPT_WORKFLOW_SERVER_HOST/PORT)
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

    def get_inputs_structure(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get inputs directory structure for a node"""
        try:
            response = requests.get(
                f"{COMPUTATION_SERVER_HOST}/computation-server/inputs/get-structure",
                params={"node_id": node_id},
                timeout=60,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data')
            return None
        except Exception as e:
            print(f"Error getting inputs structure: {str(e)}")
            return None

    def get_file_content(self, node_id: str, relative_path: str) -> Optional[Dict[str, Any]]:
        """Get file content from inputs directory"""
        try:
            response = requests.get(
                f"{COMPUTATION_SERVER_HOST}/computation-server/inputs/get-file-content",
                params={
                    "node_id": node_id,
                    "relative_path": relative_path
                },
                timeout=60,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data')
            return None
        except Exception as e:
            print(f"Error getting file content: {str(e)}")
            return None

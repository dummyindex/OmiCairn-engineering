import requests
from constants import MAIN_SERVER_HOST, SYSTEM_AGENT_KEY, COMPUTATION_SERVER_HOST
from logger_factory import LoggerFactory
import random
import time
import json

logger = LoggerFactory.get_logger("ServerAgent")


class ServerAgent:

    def __init__(self, user_id):
        response = requests.post(
            f"http://{MAIN_SERVER_HOST}/server/user/login-by-system?user_id={user_id}",
            headers={"X-System-Agent-Key": SYSTEM_AGENT_KEY or ""})
        self.headers = {
            "token": response.json()["data"]
        }

    def create_computation_node(self, node_type, analysis_id, x, y, name, function_block_id, function_block_version_id, dynamic_generation_id, system_env, dynamic_generation_session_id, computation_resource_configure, replan_source_id=None) -> dict:
        computation_resource_configure = json.dumps(computation_resource_configure) if type(
            computation_resource_configure) == dict else computation_resource_configure
        form = {
            "node_type": node_type,
            "analysis_id": analysis_id,
            "x": x,
            "y": y,
            "name": name,
            "function_block_id": function_block_id,
            "function_block_version_id": function_block_version_id,
            "dynamic_generation_id": dynamic_generation_id,
            "system_env": system_env,
            "dynamic_generation_session_id": dynamic_generation_session_id,
            "computation_resource_configure": computation_resource_configure,
            "replan_source_id": replan_source_id
        }

        # Send the request with the form data
        response = requests.post(
            f"http://{MAIN_SERVER_HOST}/server/node/create", data=form, headers=self.headers)
        result = response.json()
        logger.info(f"Create Computation Node Result: {result}")
        return result
    
    def create_notebook_node(self, node_type, analysis_id, x, y, name, function_block_id, function_block_version_id, dynamic_generation_id, system_env, dynamic_generation_session_id, computation_resource_configure) -> dict:
        computation_resource_configure = json.dumps(computation_resource_configure) if type(
            computation_resource_configure) == dict else computation_resource_configure
        form = {
            "node_type": node_type,
            "analysis_id": analysis_id,
            "x": x,
            "y": y,
            "name": name,
            "function_block_id": function_block_id,
            "function_block_version_id": function_block_version_id,
            "dynamic_generation_id": dynamic_generation_id,
            "system_env": system_env,
            "dynamic_generation_session_id": dynamic_generation_session_id,
            "computation_resource_configure": computation_resource_configure
        }

        # Send the request with the form data
        response = requests.post(
            f"http://{MAIN_SERVER_HOST}/server/node/create", data=form, headers=self.headers)
        result = response.json()
        logger.info(f"Create Notebook Node Result: {result}")
        return result

    def create_edge(self, analysis_id, source_node_id, target_node_id):
        form = {
            "analysis_id": analysis_id,
            "source_node_id": source_node_id,
            "target_node_id": target_node_id
        }

        # Send the request with the form data
        response = requests.post(
            f"http://{MAIN_SERVER_HOST}/server/edge/create", data=form, headers=self.headers)
        return response.json()

    def launch_task(self, analysis_id, node_id_list, edge_id_list):
        post_data = {
            'analysis_id': analysis_id,
            'node_id_list': node_id_list,
            'edge_id_list': edge_id_list
        }

        response = requests.post(
            f"http://{COMPUTATION_SERVER_HOST}/computation-server/task/dispatch",
            json=post_data,
            headers=self.headers
        )
        return response.json()

    def launch_code_agent(self, node_id, max_debug, model):
        response = requests.post(
            f"http://{COMPUTATION_SERVER_HOST}/computation-server/computation/invoke-code-agent?node_id={node_id}&max_debug={max_debug}&model={model}",
            headers=self.headers
        )
        return response.json()

    def report_dynamic_generation_branch_done(self, dynamic_generation_branch_id):
        logger.info(
            f"Report dynamic generation branch done: {dynamic_generation_branch_id}")
        response = requests.post(
            f"http://{COMPUTATION_SERVER_HOST}/computation-server/dynamic-generation/branch-done-report?dynamic_generation_branch_id={dynamic_generation_branch_id}"
        )
        interval = random.randint(1, 10) / 3
        time.sleep(interval)
        response = requests.post(
            f"http://{COMPUTATION_SERVER_HOST}/computation-server/dynamic-generation/branch-done-report?dynamic_generation_branch_id={dynamic_generation_branch_id}"
        )
        return response.json()

    def get_computation_history(self, node_id):
        response = requests.get(
            f"http://{MAIN_SERVER_HOST}/server/computation/get-former-history?node_id={node_id}",
            headers=self.headers
        )
        return response.json()

    def get_former_computation_steps(self, node_id):
        response = requests.get(
            f"http://{MAIN_SERVER_HOST}/server/computation/get-former-steps?node_id={node_id}",
            headers=self.headers
        )
        return response.json()

    def get_inputs_structure(self, node_id):
        """
        Get inputs directory structure for a node.
        Returns a hierarchical structure from computation-server.
        """
        response = requests.get(
            f"http://{COMPUTATION_SERVER_HOST}/computation-server/inputs/get-structure?node_id={node_id}",
            headers=self.headers
        )
        logger.warning(f"Inputs structure response: {response.text}")
        return response.json()

    @staticmethod
    def format_inputs_structure_to_text(structure_dict):
        """
        Convert inputs structure dictionary to readable text format.

        Args:
            structure_dict: Dictionary containing the hierarchical structure

        Returns:
            String representation of the directory structure
        """
        if not structure_dict or 'data' not in structure_dict:
            return "No inputs structure available"

        structure = structure_dict.get('data', {})

        def format_tree(node, indent=0, prefix=""):
            lines = []
            name = node.get('name', 'unknown')
            node_type = node.get('type', 'unknown')

            # Format current node
            if indent == 0:
                lines.append(f"{name}/")
            else:
                symbol = "├── " if prefix == "├── " else "└── "
                if node_type == 'directory':
                    lines.append(f"{' ' * (indent - 4)}{symbol}{name}/")
                else:
                    size = node.get('size', 0)
                    size_str = ServerAgent._format_file_size(size)
                    lines.append(f"{' ' * (indent - 4)}{symbol}{name} ({size_str})")

            # Format children
            children = node.get('children', [])
            for i, child in enumerate(children):
                is_last = (i == len(children) - 1)
                child_prefix = "└── " if is_last else "├── "
                child_indent = indent + 4
                lines.extend(format_tree(child, child_indent, child_prefix))

            return lines

        text_lines = format_tree(structure)
        return "\n".join(text_lines)

    @staticmethod
    def _format_file_size(size_bytes):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}PB"

    def find_all_previous_nodes(self, node_id):
        response = requests.get(
            f"http://{MAIN_SERVER_HOST}/server/node/get-previous-node-list?node_id={node_id}&with_self=1",
            headers=self.headers
        )
        return response.json()
    
    def find_branch_path(self, node_id):
        response = requests.get(
            f"http://{MAIN_SERVER_HOST}/server/node/get-previous-path?node_id={node_id}&with_self=1",
            headers=self.headers
        )
        return response.json()

    def edit_nodes(self, node_id_list, attrs):
        response = requests.post(
            f"http://{MAIN_SERVER_HOST}/server/node/batch-edit",
            json={"node_id_list": node_id_list, "attrs": attrs},
            headers=self.headers
        )
        return response.json()

    def record_llm_consumption(self, llm_consumption):
        response = requests.post(
            f"http://{MAIN_SERVER_HOST}/server/gpt/record-consumption",
            json={
                "consumption": llm_consumption
            },
            headers=self.headers
        )
        return response.json()

    def record_dynamic_generation_session(self, session):
        """
        Record a dynamic generation session in the database.
        :param session: DynamicGenerationSession object to be recorded.
        :return: The recorded session object.
        """
        try:
            response = requests.post(
                f"http://{COMPUTATION_SERVER_HOST}/computation-server/dynamic-generation/record-session",
                json={
                    "session": session
                },
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error recording dynamic generation session: {e}")
            return None

    def fetch_existing_fbvs_v2(self):
        response = requests.get(
            f"http://{MAIN_SERVER_HOST}/server/function-block-v1/get-public-v2-fbvs",
            headers=self.headers
        )
        return response.json()
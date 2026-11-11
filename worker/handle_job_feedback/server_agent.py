import requests
from constants import MAIN_SERVER_HOST, SYSTEM_AGENT_KEY, COMPUTATION_SERVER_HOST
from logger_factory import LoggerFactory
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

    def copy_node(self, node_id, with_edges=False):
        with_edges = 1 if with_edges else 0
        response = requests.get(
            f"http://{MAIN_SERVER_HOST}/server/node/copy?node_id={node_id}&with_edges={with_edges}",
            headers=self.headers
        )
        logger.debug(f"Copy node response: {response.text}")
        return response.json()

    def edit_node(self, node_id, updated_attrs):
        response = requests.post(
            f"http://{MAIN_SERVER_HOST}/server/node/edit?node_id={node_id}",
            json=updated_attrs,
            headers=self.headers
        )
        return response.json()

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

    def report_dynamic_generation_branch_done(self, dynamic_generation_branch_id):
        logger.info(
            f"Report dynamic generation branch done: {dynamic_generation_branch_id}")
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

    def get_computation_log(self, computation_id):
        response = requests.get(
            f"http://{COMPUTATION_SERVER_HOST}/computation-server/computation/get-logs?computation_id={computation_id}",
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

    def report_visualizer_step_done(self, visualizer_id, node_id, satisfied):
        satisfied = 1 if satisfied else 0
        response = requests.post(
            f"http://{COMPUTATION_SERVER_HOST}/computation-server/visualizer/report-step-done?visualizer_id={visualizer_id}&node_id={node_id}&satisfied={satisfied}",
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

    def record_bug_fixer_session(self, session):
        """
        Record a bug fixer session in the database.
        :param session: BugFixerSession object to be recorded.
        :return: The recorded session object.
        """
        try:
            response = requests.post(
                f"http://{COMPUTATION_SERVER_HOST}/computation-server/computation/record-bug-fixer-session",
                json={
                    "session": session
                },
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error recording bug fixer session: {e}")
            return None

    def create_dynamic_generation_branch(self, dynamic_generation_id, end_node_id):
        response = requests.post(
            f"http://{COMPUTATION_SERVER_HOST}/computation-server/dynamic-generation/create-branch?dynamic_generation_id={dynamic_generation_id}&end_node_id={end_node_id}",
            headers=self.headers
        )
        return response.json()

    def fetch_existing_fbvs_v2(self):
        response = requests.get(
            f"http://{MAIN_SERVER_HOST}/server/function-block-v1/get-public-v2-fbvs",
            headers=self.headers
        )
        return response.json()
    
    def optimize_error_message(self, computation_id):
        response = requests.get(
            f"http://{COMPUTATION_SERVER_HOST}/computation-server/computation/refresh-optimized-error-description?computation_id={computation_id}",
            headers=self.headers
        )
        return response.json()
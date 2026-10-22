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

    def copy_node(self, node_id, updated_attrs=None):
        response = requests.post(
            f"http://{MAIN_SERVER_HOST}/server/node/copy?node_id={node_id}",
            headers=self.headers,
            json=updated_attrs if updated_attrs else {}
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

    def find_all_previous_nodes(self, node_id):
        response = requests.get(
            f"http://{MAIN_SERVER_HOST}/server/node/get-previous-node-list?node_id={node_id}&with_self=1",
            headers=self.headers
        )
        return response.json()

    def find_parent_node(self, node_id):
        response = requests.get(
            f"http://{MAIN_SERVER_HOST}/server/node/get-parent-nodes?node_id={node_id}",
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

    def edit_visualizer(self, visualizer_id, attrs):
        response = requests.post(
            f"http://{COMPUTATION_SERVER_HOST}/computation-server/visualizer/edit?visualizer_id={visualizer_id}",
            json=attrs,
            headers=self.headers
        )
        return response.json()

    def report_visualizer_step_done(self, visualizer_id, node_id, satisfied):
        satisfied = 1 if satisfied else 0
        response = requests.post(
            f"http://{COMPUTATION_SERVER_HOST}/computation-server/visualizer/report-step-done?visualizer_id={visualizer_id}&node_id={node_id}&satisfied={satisfied}",
            headers=self.headers
        )
        return response.json()

    def get_figures(self, computation_id):
        response = requests.get(
            f"http://{COMPUTATION_SERVER_HOST}/computation-server/computation/get-figures?computation_id={computation_id}",
            headers=self.headers
        )
        return response.json()

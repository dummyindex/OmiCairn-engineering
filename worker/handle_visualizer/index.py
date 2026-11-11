from waiter.function_block_v1_waiter import FunctionBlockV1Waiter
from constants import (
    VISUALIZER_ID,
    USER_ID,
    CURRENT_NODE_ID,
    NodeState,
    NodeType,
    VisualizerState,
    Relation,
    Permission
)
from typing import (
    List,
    Dict,
    Any,
)
from datetime import datetime
import json
import time
import random
from server_agent import ServerAgent
from db import (
    Visualizer,
    FunctionBlockV1,
    FunctionBlockUserRelation,
    FunctionBlockGroup,
    FunctionBlockGroupUserRelation,
    FunctionBlockVersionV1,
    update_fb,
    find_visualizer_by_id,
    find_node_by_id,
    insert_fb,
    insert_fb_group,
    insert_fb_group_user_relation,
    insert_fb_user_relation,
    insert_fb_version,
    find_fb_group_by_owner_id_and_name,
    find_latest_computation_by_node_id,
    find_data_by_id,
    find_fb_v_by_id
)
from llm_interface import LlmInterface
from logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("VisualizerLauncher")


def lock_nodes(server_agent: ServerAgent, node_ids: List[str]):
    server_agent.edit_nodes(
        node_ids,
        {
            "visualizer_locked": True,
        }
    )


def unlock_nodes(server_agent: ServerAgent, node_ids: List[str]):
    server_agent.edit_nodes(
        node_ids,
        {
            "visualizer_locked": False,
        }
    )


def visualize(function_block: dict, inputs: dict, outputs: dict, user_prompt, llm_model):
    logger.error(outputs)
    particular_fb_group = find_fb_group_by_owner_id_and_name(
        USER_ID, "__visualizer_generated__"
    )
    if particular_fb_group is None:
        particular_fb_group = FunctionBlockGroup(
            name="__visualizer_generated__",
            created_time=datetime.now(),
            serial_number=-100,
            alt_name="__visualizer_generated__",
        )
        insert_fb_group(particular_fb_group)
        fb_group_user_relation = FunctionBlockGroupUserRelation(
            function_block_group_id=particular_fb_group.id,
            user_id=USER_ID,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        insert_fb_group_user_relation(fb_group_user_relation)

    llm_interface = LlmInterface()
    response = llm_interface.visualize(
        function_block=function_block,
        inputs=inputs,
        outputs=outputs,
        user_request=user_prompt,
        llm_model=llm_model
    )
    response_json = response.json()
    if response.status_code != 200:
        logger.error(
            f"Visualize failed: {response_json}, status_code: {response.status_code}")
        raise Exception(
            f"Visualize failed: {response_json}, status_code: {response.status_code}")
    logger.info(f"Visualize success: {response_json}")
    response = response_json.get("data", {})
    # TODO: save the response data to s3
    prompt = response.get("prompt", "")
    # TODO end
    llm_output = response.get("output")
    if llm_output is None:
        # No new node needs to be generated; return directly
        return None
    response_data = json.loads(llm_output)
    satisfied = response_data.get("satisfied", False)
    if satisfied:
        return None
    else:
        new_function_block = response_data.get("function_block", {})
        name = new_function_block.get("name", "")
        code = new_function_block.get("code", "")
        requirements = new_function_block.get("requirements", "")
        static_config = new_function_block.get("static_config", {})
        parameters = new_function_block.get("parameters", {})
        new_fb = FunctionBlockV1(
            name=name,
            group_id=particular_fb_group.id,
            current_version_id=None,
            created_time=datetime.now(),
            type="computation",
            occasion="flow",
            alt_name=None,
        )
        insert_fb(new_fb)
        new_fb_user_relation = FunctionBlockUserRelation(
            user_id=USER_ID,
            function_block_id=new_fb.id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        insert_fb_user_relation(new_fb_user_relation)
        args = static_config.get("args", [])
        tag = static_config.get("tag", "")
        document_url = static_config.get("document_url", "")
        description = static_config.get("description", "")
        source = static_config.get("source", "")
        preset_env = static_config.get("preset_env", "")
        new_fb_version = FunctionBlockVersionV1(
            name=name,
            function_block_id=new_fb.id,
            args=json.dumps(args),
            tag=tag,
            document_url=document_url,
            description=description,
            source=source,
            plot_only=False,
            runtime_version="3.9",
            created_time=datetime.now(),
            state="ok",
            program_language="Python",
            error_message=None,
            preset_env=preset_env
        )
        insert_fb_version(new_fb_version)
        update_fb(new_fb.id, {"current_version_id": new_fb_version.id})
        fb_waiter = FunctionBlockV1Waiter(
            new_fb_version.id, new_fb_version.program_language)
        fb_waiter.rewrite_core_code(code)
        fb_waiter.rewrite_requirement_file(requirements)
        fb_waiter.rewrite_static_config(static_config)
        return {
            "fb_id": new_fb.id,
            "fb_version_id": new_fb_version.id,
            "fb_name": name,
            "parameters": parameters,
        }


class VisualizerController:
    def __init__(self, visualizer: Visualizer, server_agent: ServerAgent):
        self.visualizer = visualizer
        self.server_agent = server_agent
        self.locked_nodes = []
        pass

    def collect_preivous_nodes(self):
        previous_nodes_response = self.server_agent.find_all_previous_nodes(
            CURRENT_NODE_ID)
        self.locked_nodes.extend(previous_nodes_response["data"])

    def lock_nodes(self):
        lock_nodes(self.server_agent, [node["id"]
                   for node in self.locked_nodes])

    def _check_excutable(self):
        if self.visualizer.state != VisualizerState.RUNNING.value or self.visualizer.rest_count <= 0:
            logger.info(
                f"Visualizer {self.visualizer.id} is not running, skip this step")
            return False
        return True

    def launch(self, current_node_id):
        excutable = self._check_excutable()
        if not excutable:
            self.server_agent.report_visualizer_step_done(
                self.visualizer.id, current_node_id, True
            )
            return
        current_node = find_node_by_id(current_node_id)
        self.server_agent.edit_nodes([current_node_id], {
            "state": NodeState.BEAUTIFYING.value
        })
        # Request the fb and fbv for the next node
        latest_computation = find_latest_computation_by_node_id(
            current_node_id)
        if latest_computation is None:
            logger.error(
                f"Cannot find latest computation for node {current_node_id}")
            return
        fb_v = find_fb_v_by_id(latest_computation.function_block_version_id)
        if fb_v is None:
            logger.error(
                f"Cannot find function block version for computation {latest_computation.id}")
            return
        original_fb_waiter = FunctionBlockV1Waiter(
            latest_computation.function_block_version_id, fb_v.program_language)
        original_code = original_fb_waiter.fetch_core_code()
        original_requirements = original_fb_waiter.fetch_requirement_content()
        original_static_config = original_fb_waiter.fetch_static_config()
        original_parameters = latest_computation.computation_params
        original_function_block = {
            "code": original_code,
            "requirements": original_requirements,
            "static_config": original_static_config,
            "parameters": original_parameters
        }
        result_data = find_data_by_id(latest_computation.result_data_id)
        summary = result_data.summary
        inputs = {
            "adata_summary": summary,
        }

        figure_urls_response = self.server_agent.get_figures(
            latest_computation.id)
        figure_urls = figure_urls_response["data"]
        outputs = {
            "figure_urls": figure_urls
        }

        new_fb = visualize(original_function_block, inputs,
                           outputs, self.visualizer.user_prompt, self.visualizer.llm_model)
        self.server_agent.edit_nodes([current_node_id], {
            "state": NodeState.FINISHED.value
        })
        if new_fb is None:
            self.server_agent.report_visualizer_step_done(
                self.visualizer.id, current_node_id, True
            )
            return
        # Create nodes
        self.server_agent.edit_visualizer(
            self.visualizer.id, {
                "rest_count": self.visualizer.rest_count - 1
            }
        )
        visualizer_computation_resource_configure = self.visualizer.computation_resource_configure
        if visualizer_computation_resource_configure is not None:
            visualizer_computation_resource_configure = json.loads(
                visualizer_computation_resource_configure)
            system_env = visualizer_computation_resource_configure.get(
                "system_env")
            del visualizer_computation_resource_configure["system_env"]
        else:
            system_env = None
        copy_node_response = self.server_agent.copy_node(
            node_id=current_node.id,
            updated_attrs={
                "visualizer_locked": False,
                "state": NodeState.ORIGINAL.value,
                "visualizer_id": self.visualizer.id,
                "visualizer_previous_node_id": current_node.id,
                "y": current_node.y + 200,
                "x": current_node.x
            }
        )

        new_node_id = copy_node_response["data"]["id"]

        self.server_agent.edit_nodes(
            [current_node_id], {
                "state": NodeState.FINISHED.value,
            }
        )

        self.server_agent.edit_nodes(
            [new_node_id], {
                "computation_params": json.dumps(new_fb["parameters"]),
                "visualizer_id": self.visualizer.id,
                "visualizer_previous_node_id": current_node.id,
                "function_block_id": new_fb["fb_id"],
                "function_block_version_id": new_fb["fb_version_id"],
                "system_env": system_env,
            }
        )

        parent_nodes_response = self.server_agent.find_parent_node(
            current_node_id)
        parent_nodes = parent_nodes_response["data"]
        # Create edges
        edge_ids = []
        for parent_node in parent_nodes:
            create_edge_response = self.server_agent.create_edge(
                analysis_id=self.visualizer.analysis_id,
                source_node_id=parent_node["id"],
                target_node_id=new_node_id
            )
            new_edge_id = create_edge_response["data"]["id"]
            edge_ids.append(new_edge_id)
        self.server_agent.launch_task(
            analysis_id=self.visualizer.analysis_id,
            node_id_list=[new_node_id],
            edge_id_list=[]
        )
        self.server_agent.report_visualizer_step_done(
            self.visualizer.id, current_node_id, False
        )


def main():
    visualizer = find_visualizer_by_id(VISUALIZER_ID)
    server_agent = ServerAgent(USER_ID)
    controller = VisualizerController(visualizer, server_agent)
    controller.collect_preivous_nodes()
    controller.lock_nodes()
    controller.launch(CURRENT_NODE_ID)


if __name__ == "__main__":
    main()

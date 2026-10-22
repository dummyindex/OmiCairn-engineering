from constants import DEFAULT_V2_FUNCTION_BLOCK_ID, DEFAULT_V2_FUNCTION_BLOCK_VERSION_ID
from db import (
    Node,
    DynamicGeneration,
    DynamicGenerationBranch,
    find_node_by_id,
    find_dynamic_generation_by_id,
    insert_dynamic_generation_branch,
    update_dynamic_generation,
    update_dynamic_generation_branch,
    update_dynamic_generation_plan_status,
    update_node
)
import json
from waiter.dynamic_generation_waiter import DynamicGenerationWaiter
from typing import List
from constants import NodeType, NodeState, PlanStatus, PREVIOUS_NODE_ID, DYNAMIC_GENERATION_ID, USER_ID, DYNAMIC_GENERATION_BRANCH_ID as FIRST_DYNAMIC_GENERATION_BRANCH_ID, REPLAN_SOURCE_ID
from utils import create_next_level_fbs_v2_with_plan, create_next_level_fbs_with_plan
from server_agent import ServerAgent
from logger_factory import LoggerFactory
from datetime import datetime

logger = LoggerFactory.get_logger("DynamicGeneration")


def lock_nodes(server_agent: ServerAgent, node_ids: List[str]):
    server_agent.edit_nodes(
        node_ids,
        {
            "dynamic_generation_locked": True,
        }
    )


def unlock_nodes(server_agent: ServerAgent, node_ids: List[str]):
    server_agent.edit_nodes(
        node_ids,
        {
            "dynamic_generation_locked": False,
        }
    )


class DynamicGenerationController:
    def __init__(self, dynamic_generation: DynamicGeneration, server_agent: ServerAgent):
        self._dynamic_generation = dynamic_generation
        self.rest_node_count = dynamic_generation.max_node
        self.rest_branch_count = dynamic_generation.max_branch
        self.node_id_to_listening_thread_dict = dict()
        self.previous_node = find_node_by_id(
            dynamic_generation.previous_node_id)
        self.analysis_id = self.previous_node.analysis_id
        self.server_agent = server_agent
        self.locked_nodes: List[dict] = []

    def collect_preivous_nodes(self):
        previous_nodes_response = self.server_agent.find_all_previous_nodes(
            self.previous_node.id)
        previous_nodes = previous_nodes_response["data"]
        self.locked_nodes.extend(previous_nodes)

    def lock_nodes(self):
        lock_nodes(self.server_agent, [node["id"]
                   for node in self.locked_nodes])

    def _check_excutable(self):
        _dynamic_generation = find_dynamic_generation_by_id(
            self._dynamic_generation.generation_id)
        if _dynamic_generation is None:
            return False, _dynamic_generation
        if _dynamic_generation.state == "stopped":
            return False, _dynamic_generation
        if _dynamic_generation.rest_node_count <= 0:
            return False, _dynamic_generation
        return True, _dynamic_generation

    def launch(self, current_node):
        now = datetime.now()

        update_node(current_node.id, {
            "state": NodeState.GENERATING.value
        })

        # Get the current plan
        dynamic_generation_waiter = DynamicGenerationWaiter(
            self._dynamic_generation.generation_id
        )
        current_plan = dynamic_generation_waiter.retrieve_plan(current_node.id)

        update_dynamic_generation_plan_status(
            self._dynamic_generation.generation_id, PlanStatus.EXECUTING.value
        )

        # Request the fb/fbv for the next node
        logger.debug(f"handle_dynamic_generation/index_with_plan.py: llm_model: {self._dynamic_generation.llm_model}, current_plan: {current_plan}")
        if current_node.type in [NodeType.COMPUTATION_NODE.value, NodeType.DATA_NODE.value]:
            fb_list = create_next_level_fbs_with_plan(
                USER_ID, current_node, self._dynamic_generation.generation_id,
                self._dynamic_generation.user_request,  self._dynamic_generation.llm_model, self._dynamic_generation.max_branch,
                self._dynamic_generation.generation_mode, current_plan=current_plan
            )
            new_node_type = NodeType.COMPUTATION_NODE.value
        elif current_node.type in [NodeType.COMPUTATION_NODE_V2.value, NodeType.DATA_NODE_V2.value]:
            fb_list = create_next_level_fbs_v2_with_plan(
                USER_ID, current_node, self._dynamic_generation.generation_id,
                self._dynamic_generation.user_request,  self._dynamic_generation.llm_model, self._dynamic_generation.max_branch,
                current_plan, self._dynamic_generation.generation_mode
            )
            new_node_type = NodeType.COMPUTATION_NODE_V2.value
        else:
            logger.error(
                f"Unsupported node type for dynamic generation: {current_node.type}")
            fb_list = []
            new_node_type = NodeType.COMPUTATION_NODE.value
        update_node(current_node.id, {
            "state": NodeState.FINISHED.value
        })

        if len(fb_list) == 0:
            logger.info("No FBs generated, reporting branch done.")
            self.server_agent.report_dynamic_generation_branch_done(
                FIRST_DYNAMIC_GENERATION_BRANCH_ID
            )
            return

        if len(fb_list) > self._dynamic_generation.max_branch:
            fb_list = fb_list[:self._dynamic_generation.max_branch]

        dynamic_generation_waiter = DynamicGenerationWaiter(
            self._dynamic_generation.generation_id
        )

        for fb_index in range(len(fb_list)):
            fb = fb_list[fb_index]

            # Create node
            excutable, _dynamic_generation = self._check_excutable()
            if not excutable:
                logger.warning(
                    "Dynamic generation is not executable, aborting.")
                return

            update_dynamic_generation(
                self._dynamic_generation.generation_id, {
                    "rest_node_count": _dynamic_generation.rest_node_count - 1
                }
            )

            generation_computation_resource_configure = self._dynamic_generation.computation_resource_configure
            if generation_computation_resource_configure is not None:
                generation_computation_resource_configure = json.loads(
                    generation_computation_resource_configure)
                system_env = generation_computation_resource_configure.get(
                    "system_env")
                del generation_computation_resource_configure["system_env"]
            else:
                system_env = None

            create_node_response = self.server_agent.create_computation_node(
                node_type=new_node_type,
                analysis_id=self.analysis_id,
                x=current_node.x + 200,
                y=current_node.y + 200 * (fb_index + 1),
                name=fb["fb_name"],
                function_block_id=fb["fb_id"],
                function_block_version_id=fb["fb_version_id"],
                dynamic_generation_id=self._dynamic_generation.generation_id,
                system_env=system_env,
                dynamic_generation_session_id=fb["session_id"],
                computation_resource_configure=generation_computation_resource_configure
            )

            new_node_id = create_node_response["data"]["id"]
            logger.debug(f"created fb: {fb}")
            current_plan = fb.get("current_plan", '') or ""
            dynamic_generation_waiter.store_plan(
                new_node_id, current_plan
            )
            lock_nodes(self.server_agent, [new_node_id])

            if fb_index == 0:
                update_dynamic_generation_branch(FIRST_DYNAMIC_GENERATION_BRANCH_ID, {
                    "end_node_id": new_node_id,
                    "updated_time": now
                })
            else:
                new_branch = DynamicGenerationBranch(
                    dynamic_generation_id=self._dynamic_generation.generation_id,
                    end_node_id=new_node_id,
                    state="running",
                    created_time=now,
                    updated_time=now
                )
                insert_dynamic_generation_branch(new_branch)

            self.locked_nodes.append(find_node_by_id(new_node_id).to_dict())

            # Create edge
            create_edge_response = self.server_agent.create_edge(
                analysis_id=self.analysis_id,
                source_node_id=current_node.id,
                target_node_id=new_node_id
            )
            new_edge_id = create_edge_response["data"]["id"]

            self.server_agent.launch_task(
                analysis_id=self.analysis_id,
                node_id_list=[new_node_id],
                edge_id_list=[]
            )

    def launch_v2(self, current_node):
        now = datetime.now()
        generation_computation_resource_configure = self._dynamic_generation.computation_resource_configure
        if generation_computation_resource_configure is not None:
            generation_computation_resource_configure = json.loads(
                generation_computation_resource_configure)
            system_env = generation_computation_resource_configure.get(
                "system_env")
            del generation_computation_resource_configure["system_env"]
        else:
            system_env = None
        waiter = DynamicGenerationWaiter(self._dynamic_generation.generation_id)
        plan = waiter.retrieve_plan(current_node.id)
        branch_path_response = self.server_agent.find_branch_path(current_node.id)
        branch_path = branch_path_response.get("data", {})
        nodes_path = branch_path.get("previousNodeList", [])
        start_ = -1
        for i, node in enumerate(nodes_path):
            if int(node.get("id")) == self._dynamic_generation.previous_node_id:
                start_ = i
                break
        if start_ == -1:
            raise ValueError("Previous node not found in branch path")
        nodes_path_in_auto_genie = nodes_path[start_ + 1:]

        create_node_response = self.server_agent.create_computation_node(
            node_type=NodeType.COMPUTATION_NODE_V2.value,
            analysis_id=self.analysis_id,
            x=current_node.x,
            y=current_node.y + 200,
            name=f"Step {len(nodes_path_in_auto_genie) + 1} Node",
            function_block_id=DEFAULT_V2_FUNCTION_BLOCK_ID,
            function_block_version_id=DEFAULT_V2_FUNCTION_BLOCK_VERSION_ID,
            dynamic_generation_id=self._dynamic_generation.generation_id,
            system_env=system_env,
            dynamic_generation_session_id=None,
            computation_resource_configure=generation_computation_resource_configure,
            replan_source_id=REPLAN_SOURCE_ID
        )

        new_node_id = create_node_response["data"]["id"]
        update_dynamic_generation_branch(FIRST_DYNAMIC_GENERATION_BRANCH_ID, {
            "end_node_id": new_node_id,
            "updated_time": now
        })

        update_dynamic_generation(self._dynamic_generation.generation_id, {
            "rest_node_count": self._dynamic_generation.rest_node_count - 1
        })

        # Create edge
        create_edge_response = self.server_agent.create_edge(
            analysis_id=self.analysis_id,
            source_node_id=current_node.id,
            target_node_id=new_node_id
        )
        new_edge_id = create_edge_response["data"]["id"]

        waiter.store_plan(new_node_id, plan)
        self.server_agent.launch_code_agent(
            node_id=new_node_id,
            max_debug=self._dynamic_generation.max_debug,
            model=self._dynamic_generation.llm_model
        )


    def launch_v3(self, current_node):
        now = datetime.now()
        generation_computation_resource_configure = self._dynamic_generation.computation_resource_configure
        if generation_computation_resource_configure is not None:
            generation_computation_resource_configure = json.loads(
                generation_computation_resource_configure)
            system_env = generation_computation_resource_configure.get(
                "system_env")
            del generation_computation_resource_configure["system_env"]
        else:
            system_env = None
        create_node_response = self.server_agent.create_notebook_node(
            node_type=NodeType.NOTEBOOK_NODE.value,
            analysis_id=self.analysis_id,
            x=current_node.x + 200,
            y=current_node.y + 200,
            name="Notebook Node",
            function_block_id=None,
            function_block_version_id=None,
            dynamic_generation_id=self._dynamic_generation.generation_id,
            system_env=system_env,
            dynamic_generation_session_id=None,
            computation_resource_configure=generation_computation_resource_configure
        )

        new_node_id = create_node_response["data"]["id"]

        update_dynamic_generation_branch(FIRST_DYNAMIC_GENERATION_BRANCH_ID, {
            "end_node_id": new_node_id,
            "updated_time": now
        })
        
        # Create edge
        create_edge_response = self.server_agent.create_edge(
            analysis_id=self.analysis_id,
            source_node_id=current_node.id,
            target_node_id=new_node_id
        )
        new_edge_id = create_edge_response["data"]["id"]
        self.server_agent.launch_task(
            analysis_id=self.analysis_id,
            node_id_list=[new_node_id],
            edge_id_list=[]
        )

def main():
    dynamic_generation = find_dynamic_generation_by_id(DYNAMIC_GENERATION_ID)
    server_agent = ServerAgent(USER_ID)
    controller = DynamicGenerationController(dynamic_generation, server_agent)
    controller.collect_preivous_nodes()
    controller.lock_nodes()
    current_node = find_node_by_id(PREVIOUS_NODE_ID)
    if dynamic_generation.version == "v3":
        controller.launch_v3(current_node)
    else:
        if current_node.type in [NodeType.COMPUTATION_NODE_V2.value, NodeType.DATA_NODE_V2.value]:
            controller.launch_v2(current_node)
        else:
            controller.launch(current_node)

if __name__ == "__main__":
    main()

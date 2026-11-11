from db import DynamicGeneration, Node, update_dynamic_generation
from utils import create_next_level_fbs, create_next_level_fbs_with_plan, create_next_level_fbs_v2_with_plan
from constants import NodeType, NodeState
from db import (
    lock_nodes_in_dynamic_generation,
    find_dynamic_generation_by_id,
    DynamicGenerationBranch,
    insert_dynamic_generation_branch,
    update_dynamic_generation_branch,
    find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id,
    update_node
)
import json
from waiter.dynamic_generation_waiter import DynamicGenerationWaiter
from server_agent import ServerAgent
from logger_factory import LoggerFactory
from datetime import datetime

logger = LoggerFactory.get_logger("DynamicGeneration In Job Feedback Handler")


class DynamicGenerationAgent:
    def __init__(self, user_id, current_node: Node, dynamic_generation: DynamicGeneration) -> None:
        self.current_node = current_node
        self.dynamic_generation = dynamic_generation
        self.user_id = user_id
        self.server_agent = ServerAgent(user_id)

    def _check_excutable(self):
        _dynamic_generation = find_dynamic_generation_by_id(
            self.dynamic_generation.generation_id)
        if _dynamic_generation is None:
            return False, _dynamic_generation
        if _dynamic_generation.state == "stopped":
            return False, _dynamic_generation
        if _dynamic_generation.rest_node_count <= 0:
            return False, _dynamic_generation
        return True, _dynamic_generation

    def handle(self) -> None:
        now = datetime.now()
        logger.info(
            f"[Dynamic Generation Agent] Start Handling: {self.dynamic_generation.generation_id}")
        excutable, _dynamic_generation = self._check_excutable()
        if not excutable:
            logger.info(
                f"[Dynamic Generation Agent] Stop: {self.dynamic_generation.generation_id}")
            if _dynamic_generation is not None and _dynamic_generation.state != "stopped":
                logger.info(
                    f"[Dynamic Generation Agent] Stop: {self.dynamic_generation.generation_id}: {_dynamic_generation.state}")
                branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
                    self.dynamic_generation.generation_id, self.current_node.id
                )
                if branch is not None:
                    logger.info(
                        f"[Dynamic Generation Agent] Done1: {self.dynamic_generation.generation_id}: {self.current_node.id} = {branch.id}")
                    self.server_agent.report_dynamic_generation_branch_done(
                        branch.id
                    )
            return
        logger.info(
            f"[Dynamic Generation Agent] Start Launching: {self.dynamic_generation.generation_id}")
        # Request the fb and fbv for the next node
        update_node(self.current_node.id, {
            "state": NodeState.GENERATING.value
        })
        fb_list = create_next_level_fbs(self.user_id, self.current_node, self.dynamic_generation.generation_id,
                                        self.dynamic_generation.max_branch, self.dynamic_generation.generation_mode, self.dynamic_generation.llm_model)
        logger.info(
            f"[Dynamic Generation Agent] FB List: {fb_list}")
        update_node(self.current_node.id, {
            "state": NodeState.FINISHED.value
        })
        if len(fb_list) == 0:
            logger.info(
                f"[Dynamic Generation Agent] Stop: {self.dynamic_generation.generation_id}")
            branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
                self.dynamic_generation.generation_id, self.current_node.id
            )
            logger.info(
                f"[Dynamic Generation Agent] Stop: {self.dynamic_generation.generation_id}: {self.current_node.id} = Branch: {branch}")
            if branch is not None:
                logger.info(
                    f"[Dynamic Generation Agent] Done2: {self.dynamic_generation.generation_id}: {self.current_node.id} = {branch.id}")
                self.server_agent.report_dynamic_generation_branch_done(
                    branch.id
                )
            return
        logger.info(
            f"[Dynamic Generation Agent] Start Creating Nodes: {self.dynamic_generation.generation_id}")

        dynamic_generation_waiter = DynamicGenerationWaiter(
            self.dynamic_generation.generation_id
        )
        if len(fb_list) > self.dynamic_generation.max_branch:
            fb_list = fb_list[:self.dynamic_generation.max_branch]
        for fb_index in range(len(fb_list)):
            fb = fb_list[fb_index]
            # Create nodes
            excutable, _dynamic_generation = self._check_excutable()
            logger.info(
                f"[Dynamic Generation Agent] Creating Node: {fb['fb_name']}")
            if not excutable:
                return
            logger.info(
                f"[Dynamic Generation Agent] Rest Node Count: {_dynamic_generation.rest_node_count}")
            update_dynamic_generation(
                self.dynamic_generation.generation_id, {
                    "rest_node_count": _dynamic_generation.rest_node_count - 1
                }
            )
            generation_computation_resource_configure = self.dynamic_generation.computation_resource_configure
            if generation_computation_resource_configure is not None:
                generation_computation_resource_configure = json.loads(
                    generation_computation_resource_configure)
                system_env = generation_computation_resource_configure["system_env"]
                del generation_computation_resource_configure["system_env"]
            else:
                system_env = None
            create_node_response = self.server_agent.create_computation_node(
                node_type=NodeType.COMPUTATION_NODE.value,
                analysis_id=self.current_node.analysis_id,
                x=self.current_node.x + 200,
                y=self.current_node.y + 200 * (fb_index + 1),
                name=fb["fb_name"],
                function_block_id=fb["fb_id"],
                function_block_version_id=fb["fb_version_id"],
                dynamic_generation_id=self.dynamic_generation.generation_id,
                system_env=system_env,
                dynamic_generation_session_id=fb["session_id"],
                computation_resource_configure=generation_computation_resource_configure
            )
            new_node_id = create_node_response["data"]["id"]
            rest_task = fb.get("remaining_tasks", '') or ""
            dynamic_generation_waiter.save_rest_task(new_node_id, rest_task)
            lock_nodes_in_dynamic_generation([new_node_id])
            if fb_index >= 1:
                branch = DynamicGenerationBranch(
                    dynamic_generation_id=self.dynamic_generation.generation_id,
                    end_node_id=new_node_id,
                    state="running",
                    created_time=now,
                    updated_time=now
                )
                insert_dynamic_generation_branch(branch)
            else:
                branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
                    self.dynamic_generation.generation_id, self.current_node.id
                )
                if branch is not None:
                    update_dynamic_generation_branch(
                        branch.id, {
                            "end_node_id": new_node_id,
                            "updated_time": now
                        }
                    )
            # Create edges
            create_edge_response = self.server_agent.create_edge(
                analysis_id=self.current_node.analysis_id,
                source_node_id=self.current_node.id,
                target_node_id=new_node_id
            )
            new_edge_id = create_edge_response["data"]["id"]
            logger.info(
                f"[Dynamic Generation Agent] Created Node: {new_node_id}")
            self.server_agent.launch_task(
                analysis_id=self.current_node.analysis_id,
                node_id_list=[new_node_id],
                edge_id_list=[]
            )

    def handle_with_plan(self) -> None:
        now = datetime.now()
        excutable, _dynamic_generation = self._check_excutable()
        if not excutable:
            logger.debug(
                f"[Dynamic Generation Agent] Not Excutable Anymore: {self.dynamic_generation.generation_id}")
            if _dynamic_generation is not None and _dynamic_generation.state != "stopped":
                branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
                    self.dynamic_generation.generation_id, self.current_node.id
                )
                if branch is not None:
                    self.server_agent.report_dynamic_generation_branch_done(
                        branch.id
                    )
            return
        # Request the fb and fbv for the next node
        update_node(self.current_node.id, {
            "state": NodeState.GENERATING.value
        })
        dynamic_generation_waiter = DynamicGenerationWaiter(
            self.dynamic_generation.generation_id
        )
        current_plan = dynamic_generation_waiter.retrieve_plan(
            self.current_node.id)
        
        if self.current_node.type in [NodeType.COMPUTATION_NODE_V2.value, NodeType.DATA_NODE_V2.value]:
            logger.debug(
                f"[Dynamic Generation Agent] Current Node is V2: {self.current_node.id}")
            fb_list = create_next_level_fbs_v2_with_plan(self.user_id, self.current_node, self.dynamic_generation.generation_id, self.dynamic_generation.user_request, self.dynamic_generation.llm_model,
                                                        self.dynamic_generation.max_branch, current_plan, self.dynamic_generation.generation_mode)
            new_node_type = NodeType.COMPUTATION_NODE_V2.value
        else:
            fb_list = create_next_level_fbs_with_plan(self.user_id, self.current_node, self.dynamic_generation.generation_id, self.dynamic_generation.user_request, self.dynamic_generation.llm_model,
                                                  self.dynamic_generation.max_branch, self.dynamic_generation.generation_mode, self.dynamic_generation.file_ids, current_plan)
            new_node_type = NodeType.COMPUTATION_NODE.value
        logger.debug(
            f"[Dynamic Generation Agent] FB List: {fb_list}")

        update_node(self.current_node.id, {
            "state": NodeState.FINISHED.value
        })

        if len(fb_list) == 0:
            branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
                self.dynamic_generation.generation_id, self.current_node.id
            )
            logger.debug(
                f"[Dynamic Generation Agent] No FB Generated, Stop Branch: {self.dynamic_generation.generation_id}: {self.current_node.id} = Branch: {branch}")
            if branch is not None:
                self.server_agent.report_dynamic_generation_branch_done(
                    branch.id
                )
                logger.debug(
                    f"[Dynamic Generation Agent] Done3: {self.dynamic_generation.generation_id}: {self.current_node.id} = {branch.id}")
            return

        dynamic_generation_waiter = DynamicGenerationWaiter(
            self.dynamic_generation.generation_id
        )
        if len(fb_list) > self.dynamic_generation.max_branch:
            fb_list = fb_list[:self.dynamic_generation.max_branch]
            logger.debug(
                f"[Dynamic Generation Agent] FB List Truncated: {fb_list}")
        logger.debug(
            f"[Dynamic Generation Agent] Creating Nodes for FBs")
        for fb_index in range(len(fb_list)):
            fb = fb_list[fb_index]
            # Create nodes
            excutable, _dynamic_generation = self._check_excutable()
            if not excutable:
                logger.debug(
                    f"[Dynamic Generation Agent] Not Excutable Anymore: {self.dynamic_generation.generation_id}")
                return
            logger.debug(
                f"[Dynamic Generation Agent] Rest Node Count: {_dynamic_generation.rest_node_count}")
            update_dynamic_generation(
                self.dynamic_generation.generation_id, {
                    "rest_node_count": _dynamic_generation.rest_node_count - 1
                }
            )
            logger.debug(
                f"[Dynamic Generation Agent] Creating Node for FB: {fb['fb_name']}")
            generation_computation_resource_configure = self.dynamic_generation.computation_resource_configure
            logger.debug(
                f"[Dynamic Generation Agent] Computation Resource Configure: {generation_computation_resource_configure}")
            if generation_computation_resource_configure is not None:
                generation_computation_resource_configure = json.loads(
                    generation_computation_resource_configure)
                system_env = generation_computation_resource_configure["system_env"]
                del generation_computation_resource_configure["system_env"]
            else:
                system_env = None
            logger.debug(
                f"[Dynamic Generation Agent] System Env: {system_env}")
            create_node_response = self.server_agent.create_computation_node(
                node_type=new_node_type,
                analysis_id=self.current_node.analysis_id,
                x=self.current_node.x + 200,
                y=self.current_node.y + 200 * (fb_index + 1),
                name=fb["fb_name"],
                function_block_id=fb["fb_id"],
                function_block_version_id=fb["fb_version_id"],
                dynamic_generation_id=self.dynamic_generation.generation_id,
                system_env=system_env,
                dynamic_generation_session_id=fb["session_id"],
                computation_resource_configure=generation_computation_resource_configure
            )
            logger.debug(
                f"[Dynamic Generation Agent] Created Node Response: {create_node_response}")
            new_node_id = create_node_response["data"]["id"]
            current_plan = fb.get("current_plan", '') or ""
            dynamic_generation_waiter.store_plan(
                new_node_id,current_plan
            )
            logger.debug(
                f"[Dynamic Generation Agent] Stored Plan for Node: {new_node_id}")
            lock_nodes_in_dynamic_generation([new_node_id])
            logger.debug(
                f"[Dynamic Generation Agent] Locked Node in Dynamic Generation: {new_node_id}")

            if fb_index >= 1:
                logger.debug(
                    f"[Dynamic Generation Agent] Inserting New Branch for Node: {new_node_id}")
                branch = DynamicGenerationBranch(
                    dynamic_generation_id=self.dynamic_generation.generation_id,
                    end_node_id=new_node_id,
                    state="running",
                    created_time=now,
                    updated_time=now
                )
                insert_dynamic_generation_branch(branch)
            else:
                logger.debug(
                    f"[Dynamic Generation Agent] Updating Existing Branch for Node: {new_node_id}")
                branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
                    self.dynamic_generation.generation_id, self.current_node.id
                )
                if branch is not None:
                    update_dynamic_generation_branch(
                        branch.id, {
                            "end_node_id": new_node_id,
                            "updated_time": now
                        }
                    )
            # Create edges
            create_edge_response = self.server_agent.create_edge(
                analysis_id=self.current_node.analysis_id,
                source_node_id=self.current_node.id,
                target_node_id=new_node_id
            )
            logger.debug(
                f"[Dynamic Generation Agent] Created Edge Response: {create_edge_response}")
            new_edge_id = create_edge_response["data"]["id"]
            logger.debug(
                f"[Dynamic Generation Agent] Created Node: {new_node_id}")
            self.server_agent.launch_task(
                analysis_id=self.current_node.analysis_id,
                node_id_list=[new_node_id],
                edge_id_list=[]
            )

    def handle_parent_node_dynamic_generation_with_plan(self, parent_node: Node, replan_source_id: str) -> str:
        now = datetime.now()

        excutable, _dynamic_generation = self._check_excutable()
        if not excutable:
            logger.debug(
                f"Current dynamic generation not excutable for node id: {parent_node.id}")
            # if _dynamic_generation is not None and _dynamic_generation.state != "stopped":
            #     branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
            #         self.dynamic_generation.generation_id, parent_node.id
            #     )
            #     if branch is not None:
            #         self.server_agent.report_dynamic_generation_branch_done(
            #             branch.id
            #         )
            return
        # Request the fb and fbv for the next node
        update_node(parent_node.id, {
            "state": NodeState.GENERATING.value
        })
        dynamic_generation_waiter = DynamicGenerationWaiter(
            self.dynamic_generation.generation_id
        )
        current_plan = dynamic_generation_waiter.retrieve_plan(
            parent_node.id)
        
        if parent_node.type in [NodeType.COMPUTATION_NODE_V2.value, NodeType.DATA_NODE_V2.value]:
            logger.debug(
                f"Current Node is V2: {parent_node.id}")
            fb_list = create_next_level_fbs_v2_with_plan(self.user_id, parent_node, self.dynamic_generation.generation_id, self.dynamic_generation.user_request, self.dynamic_generation.llm_model,
                                                        self.dynamic_generation.max_branch, current_plan, self.dynamic_generation.generation_mode)
            new_node_type = NodeType.COMPUTATION_NODE_V2.value
        else:
            fb_list = create_next_level_fbs_with_plan(self.user_id, parent_node, self.dynamic_generation.generation_id, self.dynamic_generation.user_request, self.dynamic_generation.llm_model,
                                                  1, self.dynamic_generation.generation_mode, self.dynamic_generation.file_ids, current_plan)
            new_node_type = NodeType.COMPUTATION_NODE.value

        logger.debug(f"Replan generated FB list: {fb_list}")
        update_node(parent_node.id, {
            "state": NodeState.FINISHED.value
        })
        if len(fb_list) == 0:
            # Keep the old branch; all new nodes go on a new branch
            return

        dynamic_generation_waiter = DynamicGenerationWaiter(
            self.dynamic_generation.generation_id
        )
        if len(fb_list) > self.dynamic_generation.max_branch:
            fb_list = fb_list[:self.dynamic_generation.max_branch]
        for fb_index in range(len(fb_list)):
            fb = fb_list[fb_index]
            # Create nodes
            excutable, _dynamic_generation = self._check_excutable()
            if not excutable:
                return
            update_dynamic_generation(
                self.dynamic_generation.generation_id, {
                    "rest_node_count": _dynamic_generation.rest_node_count - 1
                }
            )
            generation_computation_resource_configure = self.dynamic_generation.computation_resource_configure
            if generation_computation_resource_configure is not None:
                generation_computation_resource_configure = json.loads(
                    generation_computation_resource_configure)
                system_env = generation_computation_resource_configure["system_env"]
                del generation_computation_resource_configure["system_env"]
            else:
                system_env = None
            create_node_response = self.server_agent.create_computation_node(
                node_type=new_node_type,
                analysis_id=parent_node.analysis_id,
                x=parent_node.x + 200,
                y=parent_node.y + 200 * (fb_index + 1),
                name=fb["fb_name"],
                function_block_id=fb["fb_id"],
                function_block_version_id=fb["fb_version_id"],
                dynamic_generation_id=self.dynamic_generation.generation_id,
                system_env=system_env,
                dynamic_generation_session_id=fb["session_id"],
                computation_resource_configure=generation_computation_resource_configure,
                replan_source_id=replan_source_id
            )
            new_node_id = create_node_response["data"]["id"]
            current_plan = fb.get("current_plan", '') or ""
            dynamic_generation_waiter.store_plan(
                new_node_id, current_plan
            )
            lock_nodes_in_dynamic_generation([new_node_id])

            branch = DynamicGenerationBranch(
                dynamic_generation_id=self.dynamic_generation.generation_id,
                end_node_id=new_node_id,
                state="running",
                created_time=now,
                updated_time=now
            )
            insert_dynamic_generation_branch(branch)
            # Create edges
            create_edge_response = self.server_agent.create_edge(
                analysis_id=parent_node.analysis_id,
                source_node_id=parent_node.id,
                target_node_id=new_node_id
            )
            new_edge_id = create_edge_response["data"]["id"]

            self.server_agent.launch_task(
                analysis_id=parent_node.analysis_id,
                node_id_list=[new_node_id],
                edge_id_list=[]
            )

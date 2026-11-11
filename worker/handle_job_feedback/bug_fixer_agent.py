import os
from db import (
    ComputationRetryProcess,
    Node,
    NodeUserRelation,
    TaskNodeRelation,
    Edge,
    TaskEdgeRelation,
    Task,
    ComputationRetryProcess,
    Analysis,
    Computation,
    Inform,
    DynamicGeneration,
    insert_node,
    insert_node_user_relation,
    insert_task_node_relation,
    insert_edge,
    insert_task_edge_relation,
    update_dynamic_generation_branch,
    update_node,
    find_previous_node_by_node_id,
    update_computation_retry_process,
    insert_computation_retry_process,
    update_node_batch,
    delete_task_node_relations_by_task_id_and_node_id_list,
    delete_task_edge_relations_by_task_id_and_edge_id_list,
    insert_inform,
    find_task_node_relations_by_task_id_and_relation_type,
    find_all_after_edges,
    find_edges_by_target_node_id_list,
    find_node_by_id,
    find_dynamic_generation_by_id,
    find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id,
    find_visualizer_by_id,
    find_node_by_replan_source_id
)

from constants import (
    ComputationRetryProcessState,
    NodeState,
    Relation,
    Permission,
    TaskNodeRelationType,
    SpecialUserId,
    InformType,
    NodeType
)
from datetime import datetime
from waiter.retry_process_waiter import RetryProcessWaiter
from logger_factory import LoggerFactory
from utils import (
    launch_computation,
    fix_params,
    copy_and_rewrite_fb,
    handle_parent_node_replan,
)
import json
from server_agent import ServerAgent
from dynamic_generation_agent import DynamicGenerationAgent
from waiter.dynamic_generation_waiter import DynamicGenerationWaiter


logger = LoggerFactory.get_logger("BugFixerAgent")


def set_node_failed(node_id):
    update_node(
        node_id,
        {
            "state": NodeState.FAILED.value,
            "locked": False
        }
    )


def handle_launch_refused(node: Node | None, retry_process: ComputationRetryProcess | None):
    if retry_process:
        update_computation_retry_process(
            retry_process.id,
            {
                "state": ComputationRetryProcessState.STOPPED.value
            }
        )
    if node is not None:
        update_node(
            node.id,
            {
                "state": NodeState.FAILED.value,
                "locked": False
            }
        )


class BugFixerAgent:
    def __init__(self,
                 retry_process: ComputationRetryProcess,
                 node: Node,
                 task_owner_relation: NodeUserRelation,
                 task: Task,
                 analysis: Analysis,
                 computation: Computation,
                 error_description: str,
                 user_prompt: str = None,
                 dynamic_generation: DynamicGeneration = None,
                 llm_model: str = None,
                 max_debug: int = None
                 ):
        self.times_of_filling_params = 3
        self.retry_process = retry_process
        self.node = node
        self.task_owner_relation = task_owner_relation
        self.task = task
        self.analysis = analysis
        self.computation = computation
        self.error_description = error_description
        self.need_block_later_nodes = False
        self.user_prompt = user_prompt
        self.dynamic_generation = dynamic_generation
        self.llm_model = llm_model
        if retry_process is not None:
            self.llm_model = retry_process.llm_model
        else:
            self.llm_model = llm_model
        self.max_debug = max_debug

    def check_terminated(self):
        node = find_node_by_id(self.node.id)
        if node.state == NodeState.CANCELLED.value:
            return True
        return False

    def report_fault(self, node: Node = None):
        if node is None:
            node = self.node
        if node is None:
            logger.error("Node is None, cannot report fault.")
            return
        server_agent = ServerAgent(self.task_owner_relation.user_id)
        branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
            node.dynamic_generation_id, node.id
        )
        if branch is not None and branch.state == "running":
            logger.info(
                f"[Bug Fixer Agent] Start Updating Branch: {branch.id}")

            result = server_agent.report_dynamic_generation_branch_done(
                branch.id
            )
            logger.info(
                f"[Bug Fixer Agent] Done Reporting Branch: {branch.id} | {result}")
        if node.visualizer_id is not None:
            visualizer = find_visualizer_by_id(
                node.visualizer_id)
            if visualizer is not None and visualizer.state == "running":
                logger.info(
                    f"[Bug Fixer Agent] Start Updating Visualizer: {visualizer.id}")
                server_agent = ServerAgent(self.task_owner_relation.user_id)
                result = server_agent.report_visualizer_step_done(
                    visualizer.id, node.id, True
                )

    def check_if_in_dynamic_generation(self):
        dynamic_generation = find_dynamic_generation_by_id(
            self.node.dynamic_generation_id)
        if dynamic_generation is not None and dynamic_generation.state == "running":
            return True
        return False

    def block_later_nodes(self):

        # Find all nodes after the current node
        all_after_edge_list = find_all_after_edges(
            self.computation.node_id
        )
        all_after_node_id_set = {
            edge.target_node_id for edge in all_after_edge_list
        }
        node_task_relation_list = find_task_node_relations_by_task_id_and_relation_type(
            self.task.id, TaskNodeRelationType.BELONG_TO.value)
        all_task_node_id_set = {
            relation.node_id for relation in node_task_relation_list
        }
        node_id_list_after_this_node = list(
            all_after_node_id_set.intersection(all_task_node_id_set)
        )

        # Reset node states to their original state
        update_node_batch(
            node_id_list_after_this_node,
            {
                "state": NodeState.ORIGINAL.value,
                "locked": False
            }
        )

        # Delete the task-node and task-edge relations (automatically excludes downstream nodes from the task to avoid side effects)
        delete_task_node_relations_by_task_id_and_node_id_list(
            self.task.id,
            node_id_list_after_this_node
        )
        released_edge_list = find_edges_by_target_node_id_list(
            node_id_list_after_this_node)
        delete_task_edge_relations_by_task_id_and_edge_id_list(
            self.task.id,
            [edge.id for edge in released_edge_list]
        )

    def report_and_block_later_nodes_for_dynamic_generation_with_plan(self, node: Node, computation: Computation, task: Task):
        server_agent = ServerAgent(self.task_owner_relation.user_id)
        branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
            node.dynamic_generation_id, node.id
        )
        if branch is not None and branch.state == "running":
            logger.info(
                f"[Bug Fixer Agent] Start Updating Branch: {branch.id}")
            result = server_agent.report_dynamic_generation_branch_done(
                branch.id
            )
            logger.info(
                f"[Bug Fixer Agent] Done Reporting Branch: {branch.id} | {result}")

        if node.visualizer_id is not None:
            visualizer = find_visualizer_by_id(node.visualizer_id)
            if visualizer is not None and visualizer.state == "running":
                logger.info(
                    f"[Bug Fixer Agent] Start Updating Visualizer: {visualizer.id}")
                server_agent = ServerAgent(self.task_owner_relation.user_id)
                result = server_agent.report_visualizer_step_done(
                    visualizer.id, node.id, True
                )

        all_after_edge_list = find_all_after_edges(computation.node_id)
        all_after_node_id_set = {
            edge.target_node_id for edge in all_after_edge_list
        }

        node_task_relation_list = find_task_node_relations_by_task_id_and_relation_type(
            task.id, TaskNodeRelationType.BELONG_TO.value)
        all_task_node_id_set = {
            relation.node_id for relation in node_task_relation_list
        }

        node_id_list_after_this_node = list(
            all_after_node_id_set.intersection(all_task_node_id_set)
        )

        # Reset node states to their original state
        update_node_batch(
            node_id_list_after_this_node,
            {
                "state": NodeState.ORIGINAL.value,
                "locked": False
            }
        )

        # Delete the task-node and task-edge relations (automatically excludes downstream nodes from the task to avoid side effects)
        delete_task_node_relations_by_task_id_and_node_id_list(
            task.id,
            node_id_list_after_this_node
        )
        released_edge_list = find_edges_by_target_node_id_list(
            node_id_list_after_this_node)
        delete_task_edge_relations_by_task_id_and_edge_id_list(
            task.id,
            [edge.id for edge in released_edge_list]
        )

    def handle_parent_node_replan_and_execution(self, failed_to_fix_node, failed_to_fix_computation, failed_to_fix_task):
        parent_node = find_previous_node_by_node_id(self.node.id)
        dynamic_generation = find_dynamic_generation_by_id(
            self.node.dynamic_generation_id)
        replan_source_id = failed_to_fix_node.replan_source_id
        replaned_nodes = find_node_by_replan_source_id(replan_source_id)
        replan_count_limit = dynamic_generation.replan_count_limit if dynamic_generation is not None and dynamic_generation.replan_count_limit is not None else 0
        if len(replaned_nodes) >= replan_count_limit:
            logger.debug(
                f"[Bug Fixer Agent] Replan count limit reached for parent node {parent_node.id}, not replanning.")
            self.report_and_block_later_nodes_for_dynamic_generation_with_plan(
                failed_to_fix_node,
                failed_to_fix_computation,
                failed_to_fix_task
            )
            return
        replan_source_id = failed_to_fix_node.replan_source_id if failed_to_fix_node.replan_source_id is not None else failed_to_fix_node.id
        new_plan = handle_parent_node_replan(
            self.task_owner_relation.user_id,
            self.node.id,
            parent_node,
            dynamic_generation,
        )
        logger.debug(
            f"[Bug Fixer Agent] New Plan for Parent Node {parent_node.id}: {new_plan}")
        if new_plan:
            waiter = DynamicGenerationWaiter(
                dynamic_generation.generation_id
            )
            new_generated_plan = {
                "name": new_plan.get("name", "Untitled Plan"),
                "steps": new_plan.get("steps", ""),
            }
            waiter.store_plan(
                parent_node.id,
                new_generated_plan
            )
            dynamic_generation_agent = DynamicGenerationAgent(
                self.task_owner_relation.user_id,
                parent_node,
                dynamic_generation
            )
            dynamic_generation_agent.handle_parent_node_dynamic_generation_with_plan(
                parent_node,
                replan_source_id
            )
            self.report_and_block_later_nodes_for_dynamic_generation_with_plan(
                failed_to_fix_node,
                failed_to_fix_computation,
                failed_to_fix_task
            )
        else:
            logger.error(
                f"Failed to handle parent node replan for node {parent_node.id}, no new plan generated.")
            self.report_and_block_later_nodes_for_dynamic_generation_with_plan(
                failed_to_fix_node,
                failed_to_fix_computation,
                failed_to_fix_task
            )

    def handle_retry_stop(self):
        update_node(
            self.node.id,
            {
                "state": NodeState.FAILED.value,
                "locked": False
            }
        )
        self.report_fault(self.node)
        self.block_later_nodes()

    def handle_fixer_closed(self):
        update_computation_retry_process(
            self.retry_process.id,
            {
                "state": ComputationRetryProcessState.STOPPED.value
            }
        )
        update_node(
            self.node.id,
            {
                "state": NodeState.FAILED.value,
                "locked": False
            }
        )
        self.report_fault(self.node)
        self.block_later_nodes()

    def handle_no_retry_chance(self):
        logger.debug(
            f"[Bug Fixer Agent] No retry chance left for node {self.node.id}, marking as failed.")

        update_computation_retry_process(
            self.retry_process.id,
            {
                "state": ComputationRetryProcessState.STOPPED.value
            }
        )
        update_node(
            self.node.id,
            {
                "state": NodeState.FAILED.value,
                "locked": False,
                "dynamic_generation_locked": False,
                "visualizer_locked": False,
            }
        )
        failed_to_fix_node = self.node
        failed_to_fix_computation = self.computation
        failed_to_fix_task = self.task

        if self.dynamic_generation is not None and (self.dynamic_generation.plan_name or self.dynamic_generation.plan_status):
            parent_node = find_previous_node_by_node_id(self.node.id)
            if parent_node:
                self.handle_parent_node_replan_and_execution(
                    failed_to_fix_node, failed_to_fix_computation, failed_to_fix_task
                )
                branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
                    self.node.dynamic_generation_id, self.node.id
                )
                if branch is not None:
                    self.report_fault(self.node)
            else:
                self.report_and_block_later_nodes_for_dynamic_generation_with_plan(
                    failed_to_fix_node, failed_to_fix_computation, failed_to_fix_task
                )
        else:
            self.report_and_block_later_nodes_for_dynamic_generation_with_plan(
                failed_to_fix_node, failed_to_fix_computation, failed_to_fix_task
            )

    def fix_with_filling_params(self):
        if self.check_terminated():
            self.report_fault(self.node)
            return
        # Query the node's current state
        else:
            update_node(
                self.node.id,
                {
                    "state": NodeState.DEBUGGING.value,
                }
            )
            # Modify parameters
        fix_success = fix_params(self.node, self.task_owner_relation.user_id, self.llm_model,
                                 self.retry_process.id, self.retry_process.user_prompt)
        if not fix_success:
            logger.error(
                f"Failed to fix params for node {self.node.id}, reporting fault.")
            update_node(
                self.node.id,
                {
                    "state": NodeState.FAILED.value,
                    "locked": False
                }
            )
            self.report_fault(self.node)
            self.block_later_nodes()
            return
        if self.check_terminated():
            self.report_fault(self.node)
            return
        code = launch_computation(
            self.node.id,
            self.task_owner_relation.user_id,
            self.task.id,
            self.retry_process.id
        )
        if code == -1:
            handle_launch_refused(self.node, self.retry_process)
            self.report_fault(self.node)
            self.block_later_nodes()
        else:
            update_computation_retry_process(
                self.retry_process.id,
                {
                    "rest_retry": self.retry_process.rest_retry - 1
                }
            )

    def fix_with_new_node_and_fb(self):
        if self.check_terminated():
            self.report_fault(self.node)
            return
        now = datetime.now()
        # Create a node with the new fb; to avoid the user waiting too long to see the new node, first copy the node, then update fb_id and fb_version_id once the fb has been created
        # Copy the node and create the node-user relation
        server_agent = ServerAgent(self.task_owner_relation.user_id)
        copy_node_response = server_agent.copy_node(self.node.id)
        if copy_node_response["code"] != 200:
            logger.error(
                f"Copy Node Failed: {copy_node_response}")
            return
        new_node_entity = copy_node_response["data"]
        new_node_id = new_node_entity["id"]
        new_node = find_node_by_id(new_node_id)
        server_agent.edit_node(
            new_node_id,
            {
                "state": NodeState.DEBUGGING.value,
                "locked": True,
                "dynamic_generation_id": self.node.dynamic_generation_id,
                "dynamic_generation_locked": self.node.dynamic_generation_locked
            }
        )

        # Copy the node's plan to the new node and store a copy in S3
        if self.dynamic_generation is not None and (self.dynamic_generation.plan_name or self.dynamic_generation.plan_status):
            dynamic_generation_waiter = DynamicGenerationWaiter(
                self.node.dynamic_generation_id
            )
            current_plan = dynamic_generation_waiter.retrieve_plan(
                self.node.id)
            if current_plan:
                dynamic_generation_waiter.store_plan(
                    new_node_id, current_plan
                )

        if self.check_if_in_dynamic_generation():
            branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
                self.node.dynamic_generation_id,
                self.node.id
            )
            if branch is not None:
                update_dynamic_generation_branch(
                    branch.id, {
                        "end_node_id": new_node_id,
                        "updated_time": now
                    }
                )
        if self.check_terminated():
            self.report_fault(new_node)
            return

        # Create the relation between the new node and the task
        task_node_relation = TaskNodeRelation(
            task_id=self.task.id,
            node_id=new_node_id,
            created_time=now,
            is_root=False,
            is_leaf=True,
            relation_type=TaskNodeRelationType.BELONG_TO.value
        )
        insert_task_node_relation(task_node_relation)
        # Attach the new node as a sibling of the current node
        previous_node = find_previous_node_by_node_id(self.node.id)
        new_edge = Edge(
            created_time=now,
            analysis_id=self.node.analysis_id,
            source_node_id=previous_node.id,
            target_node_id=new_node_id
        )
        insert_edge(new_edge)
        task_edge_relation = TaskEdgeRelation(
            task_id=self.task.id,
            edge_id=new_edge.id,
            created_time=now
        )
        insert_task_edge_relation(task_edge_relation)
        # Set the current node state to failed and unlock it (unlocking this late because TaskUnlocker periodically scans all nodes of unfinished tasks; setting the state to failed earlier would make TaskUnlocker unlock prematurely)
        update_node(
            self.node.id,
            {
                "state": NodeState.FAILED.value,
                "locked": False,
                "dynamic_generation_locked": False,
                "visualizer_locked": False,
            }
        )
        self.block_later_nodes()
        # Send an fb generation request to the GPT server
        # Record the new node in the retry-process entity
        update_computation_retry_process(
            self.retry_process.id,
            {
                "new_node_id": new_node_id
            }
        )
        # Generate a new fb and fbv from the LLM response
        try:
            fix_success, new_fb, new_fbv, parameters = copy_and_rewrite_fb(
                self.node, self.task_owner_relation.user_id, self.llm_model, self.retry_process.id, self.retry_process.user_prompt)
            if not fix_success:
                raise Exception(
                    f"Failed to copy and rewrite FB for node {self.node.id}")
        except Exception as e:
            logger.error(f"Copy and Rewrite FB Failed: {e}")
            update_node(
                new_node_id,
                {
                    "state": NodeState.CANCELLED.value,
                    "locked": False,
                    "dynamic_generation_locked": False,
                    "visualizer_locked": False,
                }
            )
            self.report_fault(new_node)
            return
        # Replace the current node's fb
        update_node(
            new_node_id,
            {
                "function_block_id": new_fb.id,
                "function_block_version_id": new_fbv.id,
                "computation_params": parameters
            }
        )
        if self.check_terminated():
            self.report_fault(new_node)
            return
        # Start computation on the new node
        code = launch_computation(
            new_node_id,
            self.task_owner_relation.user_id,
            self.task.id,
            self.retry_process.id
        )

        if code == -1:
            new_node = find_node_by_id(new_node_id)
            handle_launch_refused(new_node, self.retry_process)
            self.report_fault(new_node)
        else:
            update_computation_retry_process(
                self.retry_process.id,
                {
                    "rest_retry": self.retry_process.rest_retry - 1
                }
            )

    def fix_with_new_fb(self):
        if self.check_terminated():
            self.report_fault(self.node)
            return
        # Set the current node state to debugging
        update_node(
            self.node.id,
            {
                "state": NodeState.DEBUGGING.value,
            }
        )
        # Send an fb generation request to the GPT server
        try:
            fix_success, new_fb, new_fbv, parameters = copy_and_rewrite_fb(
                self.node, self.task_owner_relation.user_id, self.llm_model, self.retry_process.id, self.retry_process.user_prompt)
            if not fix_success:
                raise Exception(
                    f"Failed to copy and rewrite FB for node {self.node.id}")
        except Exception as e:
            logger.error(f"Copy and Rewrite FB Failed: {e}")
            update_node(
                self.node.id,
                {
                    "state": NodeState.CANCELLED.value,
                    "locked": False,
                    "dynamic_generation_locked": False,
                    "visualizer_locked": False,
                }
            )
            self.report_fault(self.node)
            return
        # Replace the current node's fb
        update_node(
            self.node.id,
            {
                "function_block_id": new_fb.id,
                "function_block_version_id": new_fbv.id,
                "computation_params": parameters
            }
        )
        if self.check_terminated():
            self.report_fault(self.node)
            return
        # Restart computation
        code = launch_computation(
            self.node.id,
            self.task_owner_relation.user_id,
            self.task.id,
            self.retry_process.id
        )
        if code == -1:
            handle_launch_refused(self.node, self.retry_process)
            self.report_fault(self.node)
            self.block_later_nodes()
        else:
            update_computation_retry_process(
                self.retry_process.id,
                {
                    "rest_retry": self.retry_process.rest_retry - 1
                }
            )

    def handle_switch_off(self):
        self.report_fault(self.node)
        update_node(
            self.node.id,
            {
                "state": NodeState.FAILED.value,
                "locked": False
            }
        )
        self.block_later_nodes()

    def handle_launch_retry_from_analysis(self):
        if self.check_terminated():
            self.report_fault(self.node)
            return
        now = datetime.now()
        update_node(
            self.node.id,
            {
                "state": NodeState.DEBUGGING.value,
            }
        )
        if self.analysis.max_retry <= 0:
            update_node(
                self.node.id,
                {
                    "state": NodeState.FAILED.value,
                    "locked": False
                }
            )
            self.report_fault(self.node)
            self.block_later_nodes()
            return
        max_retry = self.analysis.max_retry if self.max_debug is None else self.max_debug
        # Create a new retry task
        new_retry_process = ComputationRetryProcess(
            node_id=self.node.id,
            task_id=self.task.id,
            analysis_id=self.node.analysis_id,
            state=ComputationRetryProcessState.RUNNING.value,
            max_retry=max_retry,
            rest_retry=max_retry,
            user_id=self.task_owner_relation.user_id,
            created_time=now,
            user_prompt=self.user_prompt,
            llm_model=self.llm_model
        )
        insert_computation_retry_process(new_retry_process)
        server_agent = ServerAgent(self.task_owner_relation.user_id)
        computation_logs_response = server_agent.get_computation_log(
            self.computation.id)
        retry_process_waiter = RetryProcessWaiter(
            new_retry_process.id)
        retry_process_waiter.save_result(
            self.computation.id,
            {
                "success": False,
                "error_description": self.error_description,
                "logs": computation_logs_response["data"]
            }
        )
        # Modify parameters
        fix_success = fix_params(self.node, self.task_owner_relation.user_id, self.llm_model,
                                 new_retry_process.id, new_retry_process.user_prompt)
        if not fix_success:
            logger.error(
                f"Failed to fix params for node {self.node.id} in analysis retry.")
            update_node(
                self.node.id,
                {
                    "state": NodeState.FAILED.value,
                    "locked": False
                }
            )
            self.report_fault(self.node)
            self.block_later_nodes()
            return
        # Start a new computation
        if self.check_terminated():
            self.report_fault(self.node)
            return
        code = launch_computation(
            self.node.id,
            self.task_owner_relation.user_id,
            self.task.id,
            new_retry_process.id
        )
        if code == -1:
            handle_launch_refused(self.node, new_retry_process)
            self.block_later_nodes()
        else:
            update_computation_retry_process(
                new_retry_process.id,
                {
                    "rest_retry": new_retry_process.rest_retry - 1
                }
            )

    def handle_launch_retry_from_dynamic_generation(self):
        if self.check_terminated():
            self.report_fault(self.node)
            return
        now = datetime.now()
        update_node(
            self.node.id,
            {
                "state": NodeState.DEBUGGING.value,
            }
        )
        if self.dynamic_generation.max_debug <= 0:
            update_node(
                self.node.id,
                {
                    "state": NodeState.FAILED.value,
                    "locked": False
                }
            )
            self.report_fault(self.node)
            self.block_later_nodes()
            return
        max_retry = self.dynamic_generation.max_debug
        # Create a new retry task
        new_retry_process = ComputationRetryProcess(
            node_id=self.node.id,
            task_id=self.task.id,
            analysis_id=self.node.analysis_id,
            state=ComputationRetryProcessState.RUNNING.value,
            max_retry=max_retry,
            rest_retry=max_retry,
            user_id=self.task_owner_relation.user_id,
            created_time=now,
            user_prompt=self.user_prompt,
            llm_model=self.llm_model
        )
        insert_computation_retry_process(new_retry_process)
        server_agent = ServerAgent(self.task_owner_relation.user_id)
        computation_logs_response = server_agent.get_computation_log(
            self.computation.id)
        retry_process_waiter = RetryProcessWaiter(
            new_retry_process.id)
        retry_process_waiter.save_result(
            self.computation.id,
            {
                "success": False,
                "error_description": self.error_description,
                "logs": computation_logs_response["data"]
            }
        )
        # Modify parameters
        fix_success = fix_params(self.node, self.task_owner_relation.user_id, self.llm_model,
                                 new_retry_process.id, new_retry_process.user_prompt)
        if not fix_success:
            logger.error(
                f"Failed to fix params for node {self.node.id} in dynamic generation retry.")
            update_node(
                self.node.id,
                {
                    "state": NodeState.FAILED.value,
                    "locked": False
                }
            )
            self.report_fault(self.node)
            self.block_later_nodes()
            return
        # Start a new computation
        if self.check_terminated():
            self.report_fault(self.node)
            return
        code = launch_computation(
            self.node.id,
            self.task_owner_relation.user_id,
            self.task.id,
            new_retry_process.id
        )
        if code == -1:
            handle_launch_refused(self.node, new_retry_process)
            self.block_later_nodes()
        else:
            update_computation_retry_process(
                new_retry_process.id,
                {
                    "rest_retry": new_retry_process.rest_retry - 1
                }
            )

    def handle(self, directly_start=False):
        # Computation failed within a retry task
        if self.retry_process is not None:
            server_agent = ServerAgent(self.task_owner_relation.user_id)
            computation_logs_response = server_agent.get_computation_log(
                self.computation.id)
            computation_logs = computation_logs_response["data"]
            retry_process_waiter = RetryProcessWaiter(
                self.retry_process.id)
            retry_process_waiter.save_result(
                self.computation.id,
                {
                    "success": False,
                    "error_description": self.error_description,
                    "logs": computation_logs
                }
            )
            # Retry task already stopped; stop directly
            if self.retry_process.state == ComputationRetryProcessState.STOPPED.value:
                self.handle_retry_stop()
            # The analysis retry switch is off; stop directly
            else:
                # Retry attempts exhausted; stop directly
                if self.retry_process.rest_retry <= 0:
                    self.handle_no_retry_chance()
                # For the first few retries, fix the parameters
                elif self.retry_process.max_retry - self.retry_process.rest_retry < self.times_of_filling_params:
                    self.fix_with_filling_params()
                # Parameter-fix attempts exhausted; create a new node with a new fb
                elif self.retry_process.max_retry - self.retry_process.rest_retry == self.times_of_filling_params:
                    self.fix_with_new_node_and_fb()
                # Subsequent retries stay on the new node and replace the current fb with a new fb
                else:
                    self.fix_with_new_fb()
        # First computation failure
        else:
            if self.dynamic_generation is not None and self.dynamic_generation.state == "running" and self.dynamic_generation.max_debug > 0:
                # In a dynamic-generation task with the dynamic-generation retry switch on: create and start a retry task
                self.handle_launch_retry_from_dynamic_generation()
            elif directly_start:
                # Create and start a retry task directly
                self.handle_launch_retry_from_analysis()
            elif self.analysis.bug_fixer_enabled and self.analysis.max_retry > 0:
                # In a retry task with the analysis retry switch on: create and start a retry task
                self.handle_launch_retry_from_analysis()
            else:
                # Stop directly
                self.handle_switch_off()

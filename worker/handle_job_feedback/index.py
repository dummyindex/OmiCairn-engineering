import os

from datetime import datetime
from constants import ComputationState, DataState, OPTIONS_PATH, TaskState, NodeType
import subprocess
from db import (
    Inform,
    Node,
    Computation,
    Task,
    Analysis,
    TaskUserRelation,
    DynamicGeneration,
    TaskNodeRelation,
    TaskEdgeRelation,
    ComputationFileSize,
    DynamicGenerationBranch,
    find_computation_by_id,
    find_dynamic_generation_by_id,
    find_node_by_replan_source_id,
    update_computation,
    find_task_by_id,
    update_data,
    find_analysis_by_id,
    find_node_by_id,
    find_task_owner_relation_by_task_id,
    find_computation_retry_process_by_id,
    update_node,
    find_next_edges_in_task,
    insert_inform,
    update_computation_retry_process,
    find_visualizer_by_id,
    find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id,
    find_all_after_edges,
    find_task_node_relations_by_task_id_and_relation_type,
    TaskNodeRelationType,
    update_node_batch,
    delete_task_node_relations_by_task_id_and_node_id_list,
    find_edges_by_target_node_id_list,
    delete_task_edge_relations_by_task_id_and_edge_id_list,
    insert_task_node_relation,
    insert_task_edge_relation,
    find_previous_node_by_node_id,
    insert_computation_file_size,
    insert_dynamic_generation_branch
)
import json
from dynamic_generation_agent import DynamicGenerationAgent
from llm_interface import LlmInterface
from logger_factory import LoggerFactory
from bug_fixer_agent import BugFixerAgent
from constants import (
    NodeState,
    InformType,
    ComputationRetryProcessState,
    SpecialUserId
)
from utils import launch_computation, handle_parent_node_replan
from server_agent import ServerAgent
from waiter.dynamic_generation_waiter import DynamicGenerationWaiter
from sss.porter_factory import PorterFactory


# Root of the worker code inside the container (configurable for local runs).
CODE_SPACE_ROOT = os.environ.get("OMICAIRN_CODE_SPACE", "/omicairn/code_space")


def _child_env(extra: dict) -> dict:
    """Environment for a child worker process: inherit ours, add non-None extras."""
    env = dict(os.environ)
    env.update({k: str(v) for k, v in extra.items() if v is not None})
    return env


logger = LoggerFactory.get_logger("handle_feedback main")


def optimize_error_description(computation_id, user_id):
    try:
        server_agent = ServerAgent(user_id)
        server_agent.optimize_error_message(computation_id)
    except Exception as e:
        logger.error(
            f"Failed to apply for optimize error description: {e}"
        )

def update_node_state_to_error(node_id, is_review_error=False):
    update_node(
        node_id,
        {
            "state": NodeState.FAILED.value,
            "locked": False,
            "is_review_error": is_review_error
        }
    )

def report_fault(node: Node = None, task_owner_relation: TaskUserRelation = None):
    if node is None:
        logger.error("Node is None, cannot report fault.")
        return
    server_agent = ServerAgent(task_owner_relation.user_id)
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
            server_agent = ServerAgent(task_owner_relation.user_id)
            result = server_agent.report_visualizer_step_done(
                visualizer.id, node.id, True
            )

def block_later_nodes(computation: Computation, task: Task):

    # Find all nodes after the current node
    all_after_edge_list = find_all_after_edges(
        computation.node_id
    )
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


def _handle_fixer(analysis: Analysis, dynamic_generation: DynamicGeneration, node: Node, computation: Computation, task_owner_relation: TaskUserRelation):
    if computation.enable_code_agent:
        logger.info("Computation already has code agent enabled, skip launching another one.")
        handle_parent_node_replan_and_execution(
            node, task_owner_relation, analysis)
        return
    need_fix = False
    server_agent = ServerAgent(task_owner_relation.user_id)
    model = "gpt-4o-mini"
    max_attempts = 10
    def _copy_node():
        copy_node_response = server_agent.copy_node(node.id, with_edges=True)
        new_node_entity = copy_node_response.get('data', None)
        if not new_node_entity:
            raise Exception("Failed to copy node for bug fixing")
        return new_node_entity
    if dynamic_generation is not None and dynamic_generation.state != "stopped" and dynamic_generation.max_debug > 0:
        new_node_entity = _copy_node()
        if not new_node_entity:
            raise Exception("Failed to copy node for dynamic generation debugging")
        logger.info(f"Created new node {new_node_entity.get('id')} for dynamic generation debugging")
        server_agent.create_dynamic_generation_branch(dynamic_generation_id=dynamic_generation.generation_id, end_node_id=new_node_entity.get('id'))
        need_fix = True
        old_branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(dynamic_generation.generation_id, node.id)
        max_attempts = dynamic_generation.max_debug
        model = dynamic_generation.llm_model
        if old_branch:
            server_agent.report_dynamic_generation_branch_done(old_branch.id)
        dynamic_generation_waiter = DynamicGenerationWaiter(dynamic_generation.generation_id)
        plan = dynamic_generation_waiter.retrieve_plan(node.id)
        dynamic_generation_waiter.store_plan(new_node_entity.get('id'), plan)
    elif analysis.bug_fixer_enabled:
        new_node_entity = _copy_node()
        if not new_node_entity:
            raise Exception("Failed to copy node for bug fixing")
        max_attempts = analysis.max_retry
        need_fix = True
        logger.info(f"Created new node {new_node_entity.get('id')} for bug fixing")
    if need_fix:
        task_edge_relation = TaskEdgeRelation(
            task_id=task_owner_relation.task_id,
            edge_id=new_node_entity.get("previousEdges")[0]["id"] if new_node_entity.get("previousEdges") else None,
            created_time=datetime.now(),
        )
        insert_task_edge_relation(task_edge_relation)
        task_node_relation = TaskNodeRelation(
            task_id=task_owner_relation.task_id,
            node_id=new_node_entity.get('id'),
            created_time=datetime.now(),
            is_root=False,
            is_leaf=True,
            relation_type=TaskNodeRelationType.BELONG_TO.value
        )
        insert_task_node_relation(task_node_relation)
        launch_computation(node_id=new_node_entity.get('id'), user_id=task_owner_relation.user_id, task_id=computation.task_id, code_agent_config={
            "enable": True,
            "model": model,
            "max_attempts": max_attempts
        })
    

def handle_parent_node_replan_and_execution(node: Node, task_owner_relation: TaskUserRelation, analysis: Analysis):
    dynamic_generation_branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
        node.dynamic_generation_id,
        node.id
    )
    dynamic_generation = find_dynamic_generation_by_id(node.dynamic_generation_id)
    if dynamic_generation.rest_node_count <= 0:
        server_agent = ServerAgent(task_owner_relation.user_id)
        server_agent.report_dynamic_generation_branch_done(dynamic_generation_branch.id)
        return
    parent_node = find_previous_node_by_node_id(node.id)
    replan_source_id = node.replan_source_id
    replaned_nodes = find_node_by_replan_source_id(replan_source_id)
    replan_count_limit = dynamic_generation.replan_count_limit if dynamic_generation is not None and dynamic_generation.replan_count_limit is not None else 0
    if len(replaned_nodes) >= replan_count_limit:
        server_agent = ServerAgent(task_owner_relation.user_id)
        server_agent.report_dynamic_generation_branch_done(dynamic_generation_branch.id)
        logger.debug(
            f"[Bug Fixer Agent] Replan count limit reached for parent node {parent_node.id}, not replanning.")
        return
    replan_source_id = node.replan_source_id if node.replan_source_id is not None else node.id
    new_plan = handle_parent_node_replan(
        task_owner_relation.user_id,
        node.id,
        parent_node,
        dynamic_generation,
    )
    now = datetime.now()
    new_branch = DynamicGenerationBranch(
        dynamic_generation_id=dynamic_generation.generation_id,
        end_node_id=parent_node.id,
        state="running",
        created_time=now,
        updated_time=now
    )
    insert_dynamic_generation_branch(new_branch)
    logger.debug(
        f"[Bug Fixer Agent] New Plan for Parent Node {parent_node.id}: {new_plan}")
    server_agent = ServerAgent(task_owner_relation.user_id)
    server_agent.report_dynamic_generation_branch_done(dynamic_generation_branch.id)
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
        
        subprocess.Popen(
            ["python3", 'index_with_plan.py'],
            cwd=os.path.join(CODE_SPACE_ROOT, 'handle_dynamic_generation'),
            env=_child_env({
                "PREVIOUS_NODE_ID": parent_node.id,
                "DYNAMIC_GENERATION_ID": dynamic_generation.generation_id,
                "DYNAMIC_GENERATION_BRANCH_ID": new_branch.id,
                "USER_ID": task_owner_relation.user_id,
                "REPLAN_SOURCE_ID": replan_source_id,
                "PORTER_TYPE": 's3-porter',
            })
        )
    else:
        logger.error(
            f"Failed to handle parent node replan for node {parent_node.id}, no new plan generated.")


def handle_failed(computation, error_description, need_optimize, node: Node, task, task_owner_relation, analysis, dynamic_generation=None, llm_model=None):
    logger.debug(f"Handle node failed: {node.id}")
    now = datetime.now()

    # If the computation has already been cancelled, nothing to do
    if computation.computation_state == ComputationState.CANCELLED.value:
        return

    error_description = error_description or "Computation failed"
    # Update computation state
    update_computation(computation.id, {
        "computation_state": ComputationState.FAILED.value,
        "duration": (now - computation.start_time).total_seconds() if computation.start_time is not None else 0,
        "error_description": error_description,
        "is_review_error": False
    })

    # Refine the error description
    try:
        if need_optimize:
            optimize_error_description(
                computation.id, task_owner_relation.user_id)
    except Exception as e:
        logger.error(
            f"Failed to optimize error description: {e}"
        )

    # Update data entity state
    if computation.result_data_id is not None:
        update_data(
            computation.result_data_id,
            {
                "state": DataState.ERROR.value,
                "error_message": "Computation failed"
            }
        )

    if node.type in [NodeType.COMPUTATION_NODE_V2.value, NodeType.DATA_NODE_V2.value]:
        _handle_fixer(analysis, dynamic_generation, node, computation, task_owner_relation)
        update_node_state_to_error(node.id, False)
        block_later_nodes(computation, task)
        report_fault(node, task_owner_relation=task_owner_relation)
    else:
        retry_process = find_computation_retry_process_by_id(
            computation.retry_process_id)
        bug_fixer_agent = BugFixerAgent(
            retry_process,
            node,
            task_owner_relation,
            task,
            analysis,
            computation,
            error_description,
            dynamic_generation=dynamic_generation,
            llm_model=llm_model
        )
        bug_fixer_agent.handle()


def retry_directly(computation: Computation, node, task: Task, task_owner_relation, analysis, user_prompt, llm_model=None, max_debug=None):
    bug_fixer_agent = BugFixerAgent(
        None,
        node,
        task_owner_relation,
        task,
        analysis,
        computation,
        computation.error_description,
        user_prompt,
        llm_model=llm_model,
        max_debug=max_debug
    )
    bug_fixer_agent.handle(True)


def handle_success(computation, node: Node, task, task_owner_relation, analysis, job_review_passed, review_error):
    now = datetime.now()
    if computation.computation_state == ComputationState.CANCELLED.value:
        return
    
    update_node(
        computation.node_id,
        {
            "state": NodeState.FINISHED.value,
            "is_review_error": not job_review_passed
        }
    )
    if computation is None:
        raise Exception(
            "Cannot find computation by id {}".format(computation.id))

    update_computation(computation.id, {
        "start_time": now,
        "computation_state": ComputationState.FINISHED.value,
        "duration": (now - computation.start_time).total_seconds() if computation.start_time is not None else 0,
        "is_review_error": not job_review_passed
    })

    # TODO: check whether the data exists
    # update data state
    update_data(
        computation.result_data_id,
        {
            "created_time": now,
            "state": DataState.OK.value,
            "error_message": None,
        }
    )
    next_edge_list = find_next_edges_in_task(
        computation.node_id,
        computation.task_id
    )
    for next_edge in next_edge_list:
        next_node = find_node_by_id(next_edge.target_node_id)
        # TODO: check whether all upstream nodes have completed
        launch_computation(
            node_id=next_node.id,
            user_id=task_owner_relation.user_id,
            task_id=computation.task_id
        )
    
    if node.visualizer_id is not None:
        subprocess.Popen(
            ["python3", 'index.py'],
            cwd=os.path.join(CODE_SPACE_ROOT, 'handle_visualizer'),
            env=_child_env({
                "VISUALIZER_ID": node.visualizer_id,
                "USER_ID": task_owner_relation.user_id,
                "CURRENT_NODE_ID": node.id,
                "PORTER_TYPE": 's3-porter',
            })
        )
        return
    if node.dynamic_generation_id is not None:
        logger.info(f"Handle node success: {node.id}")
        dynamic_generation = find_dynamic_generation_by_id(
            node.dynamic_generation_id)
        if dynamic_generation.version == "v3":
            dg_waiter = DynamicGenerationWaiter(node.dynamic_generation_id)
            plan = dg_waiter.retrieve_plan(node.id)
            if not plan.get("finished", False):
                dynamic_generation_branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
                    node.dynamic_generation_id,
                    node.id
                )
                subprocess.Popen(
                    ["python3", 'index_with_plan.py'],
                    cwd=os.path.join(CODE_SPACE_ROOT, 'handle_dynamic_generation'),
                    env=_child_env({
                        "PREVIOUS_NODE_ID": node.id,
                        "DYNAMIC_GENERATION_ID": dynamic_generation.generation_id,
                        "DYNAMIC_GENERATION_BRANCH_ID": dynamic_generation_branch.id,
                        "USER_ID": task_owner_relation.user_id,
                        "PORTER_TYPE": 's3-porter',
                    })
                )
            else:
                dynamic_generation_branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
                    node.dynamic_generation_id,
                    node.id
                )
                if dynamic_generation_branch is not None:
                    server_agent = ServerAgent(task_owner_relation.user_id)
                    server_agent.report_dynamic_generation_branch_done(
                        dynamic_generation_branch.id
                    )
        elif node.type == NodeType.COMPUTATION_NODE_V2.value:
            dg_waiter = DynamicGenerationWaiter(node.dynamic_generation_id)
            plan = dg_waiter.retrieve_plan(node.id)
            if not plan.get("finished", False) and dynamic_generation.rest_node_count > 0:
                dynamic_generation_branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
                    node.dynamic_generation_id,
                    node.id
                )
                subprocess.Popen(
                    ["python3", 'index_with_plan.py'],
                    cwd=os.path.join(CODE_SPACE_ROOT, 'handle_dynamic_generation'),
                    env=_child_env({
                        "PREVIOUS_NODE_ID": node.id,
                        "DYNAMIC_GENERATION_ID": dynamic_generation.generation_id,
                        "DYNAMIC_GENERATION_BRANCH_ID": dynamic_generation_branch.id,
                        "USER_ID": task_owner_relation.user_id,
                        "PORTER_TYPE": 's3-porter',
                    })
                )
            else:
                dynamic_generation_branch = find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(
                    node.dynamic_generation_id,
                    node.id
                )
                if dynamic_generation_branch is not None:
                    server_agent = ServerAgent(task_owner_relation.user_id)
                    server_agent.report_dynamic_generation_branch_done(
                        dynamic_generation_branch.id
                    )
        else:
            dynamic_generation_agent = DynamicGenerationAgent(
                task_owner_relation.user_id,
                node,
                dynamic_generation
            )

            if (dynamic_generation.plan_status or dynamic_generation.plan_name) is not None:
                dynamic_generation_agent.handle_with_plan()
            else:
                dynamic_generation_agent.handle()

    if computation.retry_process_id is not None:
        update_computation_retry_process(computation.retry_process_id, {
            "state": ComputationRetryProcessState.STOPPED.value
        })


def count_folder_size(folder_key):
    porter = PorterFactory.create_porter()
    porter.set_operation_target(folder_key)
    
    total_size = 0
    start_after = ''
    
    while True:
        response = porter.list_file_infos(start_after=start_after, max_keys=1000, recursive=True)
        
        # Sum the sizes of all files on the current page
        if 'Contents' in response:
            for obj in response['Contents']:
                total_size += obj.get('Size', 0)
        
        # Check whether more pages remain
        if response.get('IsTruncated', False):
            # Get the start position of the next page
            start_after = response.get('NextContinuationToken', '')
            if not start_after and 'Contents' in response and len(response['Contents']) > 0:
                # If there is no NextContinuationToken, use the last object's Key
                start_after = response['Contents'][-1]['Key']
        else:
            break
    
    return total_size

def count_computation(computation_id):
    porter = PorterFactory.create_porter()
    report_key = f"computation-report/report-{computation_id}.md"
    porter.set_operation_target(report_key)
    try:
        head = porter.get_head()
        report_size = head.get("ContentLength", 0)
    except Exception as e:
        report_size = 0
    log_key = f"computation_log/{computation_id}"
    porter.set_operation_target(log_key)
    try:
        head = porter.get_head()
        log_size = head.get("ContentLength", 0)
    except Exception as e:
        print(e)
        log_size = 0
    result_key = f"computation_result/{computation_id}"
    porter.set_operation_target(result_key)
    try:
        head = porter.get_head()
        result_size = head.get("ContentLength", 0)
    except Exception as e:
        result_size = 0
    review_error_key = f"computation_review_error/{computation_id}"
    porter.set_operation_target(review_error_key)
    try:
        head = porter.get_head()
        review_error_size = head.get("ContentLength", 0)
    except Exception as e:
        review_error_size = 0
    options_key = f"computation_options/{computation_id}"
    porter.set_operation_target(options_key)
    try:
        head = porter.get_head()
        options_size = head.get("ContentLength", 0)
    except Exception as e:
        options_size = 0
    output_prefix = f"computation_output_file/{computation_id}/"
    output_size = count_folder_size(output_prefix)
    return {
        "report_size": report_size,
        "log_size": log_size,
        "result_size": result_size,
        "review_error_size": review_error_size,
        "options_size": options_size,
        "output_size": output_size
    }

def count_data_size(data_id: str):
    porter = PorterFactory.create_porter()
    # h5ad
    h5ad_key = f"adata/{data_id}.h5ad"
    try:
        h5ad_size = porter.get_head(h5ad_key).get("ContentLength", 0)
    except Exception as e:
        h5ad_size = 0
    # components
    components_prefix = f"adata/{data_id}-"
    components_size = count_folder_size(components_prefix)

    return h5ad_size + components_size

def main():
    # Read the feedback-handling parameters provided by the server
    with open(OPTIONS_PATH, "r") as f:
        options = json.load(f)

    success = options.get("success", False)
    computation_id = options.get("computation_id", None)
    user_prompt = options.get("user_prompt", None)
    job_review_passed = options.get("job_review_passed", False)
    review_error = options.get("review_error", None)
    # Get the computation entity
    computation = find_computation_by_id(computation_id)

    # Get the computation's node, task, task owner and analysis
    logger.debug(f"Fetching related entities for computation {computation_id}")
    node = find_node_by_id(computation.node_id)
    task = find_task_by_id(computation.task_id)
    task_owner_relation = find_task_owner_relation_by_task_id(task.id)
    analysis = find_analysis_by_id(node.analysis_id)
    dynamic_generation = find_dynamic_generation_by_id(
        node.dynamic_generation_id
    ) or None
    if computation is None:
        raise Exception(
            "Cannot find computation by id {}".format(computation_id))
    if success:
        handle_success(computation, node, task, task_owner_relation, analysis, job_review_passed, review_error)
    else:
        error_description = options.get("error_description", "")
        need_optimize = options.get("need_optimize", False)
        directly_trigger = options.get("directly_trigger", False)
        llm_model = options.get("llm_model", None)
        max_debug = options.get("max_debug", None)
        if directly_trigger:
            retry_directly(computation, node, task,
                           task_owner_relation, analysis, user_prompt, llm_model, max_debug)
        else:
            handle_failed(computation, error_description, need_optimize,
                          node, task, task_owner_relation, analysis, dynamic_generation, llm_model=llm_model)
    count_result = count_computation(computation_id)

    computation_file_size = ComputationFileSize(
        computation_id=computation_id,
        created_time=datetime.now(),
        **count_result
    )
    insert_computation_file_size(computation_file_size)
    update_computation(computation_id, {"s3_size_recorded": True})

    data_size = count_data_size(computation.result_data_id)
    update_data(
        computation.result_data_id,
        {"data_size": data_size}
    )


if __name__ == "__main__":
    main()

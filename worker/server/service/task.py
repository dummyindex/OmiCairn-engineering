from datetime import datetime
import subprocess
import uuid
import threading
from flask import current_app
from dao.node import node_dao
from dao.task import task_dao
from dao.edge import edge_dao
from dao.analysis import analysis_dao
from model.task import Task
from model.task_edge_relation import TaskEdgeRelation
from model.task_node_relation import TaskNodeRelation
from model.computation import Computation
from model.node import Node
from model.data import Data
from model.data_user_relation import DataUserRelation
from model.computation_user_relation import ComputationUserRelation
from model.task_user_relation import TaskUserRelation
from dao.task_edge_relation import task_edge_relation_dao
from dao.task_node_relation import task_node_relation_dao
from dao.computation import computation_dao
from dao.function_block_v1 import function_block_v1_dao
from dao.edge import edge_dao
from dao.data import data_dao
from dao.inform import inform_dao
from constants.computation import ComputationState
from tool.computation_launcher import ComputationLauncher, sync_s3_data_to_claude_code_bucket, sync_plan_to_claude_code_bucket
from tool.flow import FlowTool
from constants.node import NodeType
from constants.node import NodeState
from constants.task import TaskState
from constants.data import CreatedFrom
from constants.common import DEPLOY_ENV
from constants.gpt_server import (
    GPT_WORKFLOW_SERVER_HOST,
    GPT_WORKFLOW_SERVER_PORT,
    NETWORK_PROXY_HOST,
    NETWORK_PROXY_PORT,
)
from constants.task_node_relation import TaskNodeRelationType
from constants.authority import Permission, Relation
from waiter.computation import ComputationWaiter
import json
import boto3
import os
import time
from log.logger_factory import LoggerFactory
from constants.computation import (
    ComputationState,
    R_JOB_DEFINITION,
    JOB_QUEUE,
    LOGS_GROUP_NAME,
    BASH_JOB_DEFINITION,
    PYTHON_JOB_DEFINITION_SCANPY,
    PYTHON_JOB_DEFINITION_DYN,
    PYTHON_JOB_DEFINITION_MEBOCOST,
    PYTHON_JOB_DEFINITION_SCVELO,
    PYTHON_JOB_DEFINITION_SCFATES,
    PYTHON_JOB_DEFINITION_DEFAULT
)
from db.config import (
    HOST,
    PORT,
    DATABASE,
    USERNAME,
    PASSWORD
)
from tool.batch_client import batch_client_factory
from constants.data import DataState
from exception.request.parameter_invalid import ParameterInvalidException
from datetime import datetime
from constants.sss import BUCKET_NAME
from constants.computation_retry_process import ComputationRetryProcessState
from constants.computation import SystemEnv as ComputationSystemEnv
from tool.task_picker import task_picker
from computation_logs.aws_cloudwatch_taker import AWSCloudwatchLogsTaker
from db import alchemy_db


# Root of the worker code inside the container (configurable for local runs).
CODE_SPACE_ROOT = os.environ.get("OMICAIRN_CODE_SPACE", "/omicairn/code_space")


def _child_env(extra: dict) -> dict:
    """Environment for a child worker process: inherit ours, add non-None extras."""
    env = dict(os.environ)
    env.update({k: str(v) for k, v in extra.items() if v is not None})
    return env

logger = LoggerFactory.get_logger("task_service")


class TaskService:
    def _launch_singularity_computation(
        self,
        node: Node,
        user_id,
        task_id,
        code_agent_config=None,
        visualizer_agent_config=None
    ):
        now = datetime.now()
        no_source = False
        # search source data list
        prev_edge_list = edge_dao.find_by_target_node_id(node.id)
        if len(prev_edge_list) == 0:
            no_source = True
        logger.info("Previous edge list: %s" % prev_edge_list)
        source_data_ids = []
        source_data_changed_history = {}
        previous_computation_id = -1
        for prev_edge in prev_edge_list:
            prev_node_id = prev_edge.source_node_id
            previous_node = node_dao.find_by_id(prev_node_id)
            if previous_node.type in [NodeType.DATA_NODE.value, NodeType.DATA_NODE_V2.value]:
                source_data_ids.append(previous_node.data_id)
                source_data_changed_history[previous_node.data_id] = data_dao.find_change_history_by_data_id(
                    previous_node.data_id)
            elif previous_node.type in [NodeType.COMPUTATION_NODE.value, NodeType.COMPUTATION_NODE_V2.value, NodeType.NOTEBOOK_NODE.value, NodeType.CLAUDE_CODE_NODE.value]:
                computation = computation_dao.find_latest_by_node_id(prev_node_id)
                source_data_ids.append(computation.result_data_id)
                source_data_changed_history[computation.result_data_id] = data_dao.find_change_history_by_data_id(
                    computation.result_data_id)
                previous_computation_id = computation.id
        if not no_source:
            source_data_ids_str = json.dumps(source_data_ids)
            first_data = data_dao.find_by_id(source_data_ids[0])
        else:
            source_data_ids_str = None
            first_data = None

        # create result data
        if no_source:
            result_data_id = None
        else:
            result_data = Data(
                created_time=now,
                created_from=CreatedFrom.COMPUTATION.value,
                collected=False,
                name=None,
                upload_type=None,
                species=first_data.species,
                description=first_data.description,
                state=DataState.UPLOADING.value,
                error_message=None
            )
            data_dao.insert(result_data)
            result_data_id = result_data.id
            data_user_relation = DataUserRelation(
                data_id=result_data_id,
                user_id=user_id,
                relation=Relation.BELONG_TO.value,
                permission=Permission.ADMIN.value
            )
            data_dao.insert_user_relation(data_user_relation)
        # create computation
        computation = Computation(
            node_id=node.id,
            source_data_ids=source_data_ids_str,
            result_data_id=result_data_id,
            computation_state=ComputationState.PENDING.value,
            created_time=now,
            computation_params=node.computation_params,
            function_block_id=node.function_block_id,
            function_block_version_id=node.function_block_version_id,
            task_id=task_id,
            system_env=node.system_env,
            computation_resource_configure=node.computation_resource_configure,
            start_time=now,
            duration=0,
            job_ident=None,
            enable_code_agent=code_agent_config.get("enable", False) if code_agent_config else False,
        )
        computation_dao.insert(computation)
        computation_user_relation = ComputationUserRelation(
            computation_id=computation.id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        computation_dao.insert_user_relation(computation_user_relation)
        node_dao.update(node.id, {'state': NodeState.RUNNING.value})

        function_block = function_block_v1_dao.find_by_id(
            computation.function_block_id)
        function_block_version = function_block_v1_dao.find_fb_version_by_id(
            computation.function_block_version_id)
        options = {}
        options["computation_params"] = json.loads(
            computation.computation_params or "\{\}")
        options["fb_id"] = computation.function_block_id
        options["fb_version_id"] = computation.function_block_version_id
        options["source_data_ids"] = json.loads(
            computation.source_data_ids or "[]")
        options["source_data_changed_history"] = source_data_changed_history
        options["result_data_id"] = computation.result_data_id
        options["fb_type"] = function_block.type
        options["node_id"] = computation.node_id
        options["analysis_id"] = node.analysis_id
        options["fb_name"] = function_block.name
        options["ploy_only"] = function_block_version.plot_only
        options["runtime_version"] = function_block_version.runtime_version
        options["preset_env"] = function_block_version.preset_env

        computation_options_waiter = ComputationWaiter(computation.id)
        computation_options_waiter.save_options(options)

        computation_resource_configure = json.loads(
            computation.computation_resource_configure)

        if node.system_env == ComputationSystemEnv.SERVER_LOCAL.value:
            if function_block_version.is_v2:
                job_id = ComputationLauncher.launch_local_computation_v2(
                    computation.id, previous_computation_id, function_block_version.program_language, function_block_version.preset_env, user_id, node.id, code_agent_config, visualizer_agent_config)
            else:
                job_id = ComputationLauncher.launch_local_computation(
                    computation.id, previous_computation_id, function_block_version.program_language, function_block_version.preset_env, user_id, node.id)

        elif node.system_env == ComputationSystemEnv.AWS_BATCH.value:
            if function_block_version.is_v2:
                job_id = ComputationLauncher.launch_aws_computation_v2(
                    computation.id, previous_computation_id, function_block_version.program_language, computation_resource_configure, function_block_version.preset_env, user_id, node.id, code_agent_config, visualizer_agent_config)
            else:
                job_id = ComputationLauncher.launch_aws_computation(
                    computation.id, previous_computation_id, function_block_version.program_language, computation_resource_configure, function_block_version.preset_env, user_id, node.id)

        computation_dao.update(computation.id, {
            "computation_state": ComputationState.QUEUING.value,
            "job_ident": job_id
        })
        return computation


    def _launch_notebook_computation(
        self,
        node_id,
        user_id,
        task_id
    ):
        now = datetime.now()
        logger.info("Create computation for notebook node %s" % node_id)
        node = node_dao.find_by_id(node_id)

        prev_edge_list = edge_dao.find_by_target_node_id(node.id)

        source_data_ids = []
        previous_computation_id = -1
        for prev_edge in prev_edge_list:
            prev_node_id = prev_edge.source_node_id
            previous_node = node_dao.find_by_id(prev_node_id)
            if previous_node.type in [NodeType.COMPUTATION_NODE.value, NodeType.COMPUTATION_NODE_V2.value, NodeType.NOTEBOOK_NODE.value, NodeType.CLAUDE_CODE_NODE.value]:
                computation = \
                    computation_dao.find_latest_by_node_id(prev_node_id)
                previous_computation_id = computation.id
                source_data_ids.append(computation.result_data_id)
            elif previous_node.type in [NodeType.DATA_NODE.value, NodeType.DATA_NODE_V2.value]:
                source_data_ids.append(previous_node.data_id)
            else:
                logger.warning("Unsupported previous node type for notebook computation: %s" % previous_node.type)
        source_data_ids_str = json.dumps(source_data_ids)

        result_data = Data(
            created_time=now,
            created_from=CreatedFrom.COMPUTATION.value,
            collected=False,
            name=None,
            upload_type=None,
            species=None,
            description=None,
            state=DataState.UPLOADING.value,
            error_message=None
        )
        data_dao.insert(result_data)
        result_data_id = result_data.id
        data_user_relation = DataUserRelation(
            data_id=result_data_id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        data_dao.insert_user_relation(data_user_relation)

        
        # create computation
        computation = Computation(
            node_id=node.id,
            source_data_ids=source_data_ids_str,
            result_data_id=result_data_id,
            computation_state=ComputationState.PENDING.value,
            created_time=now,
            computation_params=node.computation_params,
            function_block_id=node.function_block_id,
            function_block_version_id=node.function_block_version_id,
            task_id=task_id,
            system_env=node.system_env,
            computation_resource_configure=node.computation_resource_configure,
            start_time=now,
            duration=0,
            job_ident=None
        )
        computation_dao.insert(computation)
        computation_user_relation = ComputationUserRelation(
            computation_id=computation.id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        computation_dao.insert_user_relation(computation_user_relation)
        node_dao.update(node.id, {'state': NodeState.RUNNING.value})
        computation_resource_configure = json.loads(
            computation.computation_resource_configure)
        if node.system_env == ComputationSystemEnv.SERVER_LOCAL.value:
            job_id = ComputationLauncher.launch_local_notebook(
                computation.id, 
                previous_computation_id,
                program_language="Unknown",
                preset_env="Unknown",
                user_id=user_id,
                node_id=node_id,
            )
        elif node.system_env == ComputationSystemEnv.AWS_BATCH.value:
            job_id = ComputationLauncher.launch_aws_notebook(
                computation.id, 
                previous_computation_id,
                program_language="Unknown",
                computation_resource_configure=computation_resource_configure,
                preset_env="Unknown",
                user_id=user_id,
                node_id=node_id,
            )
        computation_dao.update(computation.id, {
            "computation_state": ComputationState.QUEUING.value,
            "job_ident": job_id
        })
        return computation

    def _launch_claude_code_computation(
        self,
        node_id,
        user_id,
        task_id
    ):
        """
        Launch a Claude Code computation using Claude Code CLI.
        """
        now = datetime.now()
        node = node_dao.find_by_id(node_id)

        prev_edge_list = edge_dao.find_by_target_node_id(node.id)

        previous_nodes, previous_edges = node_dao.find_branch_path(node.id)

        source_data_ids = []
        previous_computation_id = -1
        for prev_edge in prev_edge_list:
            prev_node_id = prev_edge.source_node_id
            previous_node = node_dao.find_by_id(prev_node_id)
            if previous_node.type in [NodeType.COMPUTATION_NODE.value, NodeType.COMPUTATION_NODE_V2.value, NodeType.NOTEBOOK_NODE.value, NodeType.CLAUDE_CODE_NODE.value]:
                computation = computation_dao.find_latest_by_node_id(prev_node_id)
                previous_computation_id = computation.id
                source_data_ids.append(computation.result_data_id)
            elif previous_node.type in [NodeType.DATA_NODE.value, NodeType.DATA_NODE_V2.value]:
                source_data_ids.append(previous_node.data_id)
            else:
                logger.warning("[claude code] Unsupported previous node type for claude_code computation: %s" % previous_node.type)
        source_data_ids_str = json.dumps(source_data_ids)

        result_data = Data(
            created_time=now,
            created_from=CreatedFrom.COMPUTATION.value,
            collected=False,
            name=None,
            upload_type=None,
            species=None,
            description=None,
            state=DataState.UPLOADING.value,
            error_message=None
        )
        data_dao.insert(result_data)
        result_data_id = result_data.id
        data_user_relation = DataUserRelation(
            data_id=result_data_id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        data_dao.insert_user_relation(data_user_relation)

        computation = Computation(
            node_id=node.id,
            source_data_ids=source_data_ids_str,
            result_data_id=result_data_id,
            computation_state=ComputationState.PENDING.value,
            created_time=now,
            computation_params=node.computation_params,
            function_block_id=node.function_block_id,
            function_block_version_id=node.function_block_version_id,
            task_id=task_id,
            system_env=node.system_env,
            computation_resource_configure=node.computation_resource_configure,
            start_time=now,
            duration=0,
            job_ident=None
        )
        computation_dao.insert(computation)
        computation_user_relation = ComputationUserRelation(
            computation_id=computation.id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        computation_dao.insert_user_relation(computation_user_relation)
        node_dao.update(node.id, {'state': NodeState.RUNNING.value})

        computation_resource_configure = json.loads(
            computation.computation_resource_configure)

        claude_model = "claude-sonnet-4-5-20250929"
        max_iterations = 100

        if node.dynamic_generation_id:
            try:
                from dao.dynamic_generation import dynamic_generation_dao
                dynamic_generation = dynamic_generation_dao.find_by_id(node.dynamic_generation_id)
                if dynamic_generation:
                    # Read Claude execution settings from dynamic_generation
                    if dynamic_generation.claude_execution_model:
                        claude_model = dynamic_generation.claude_execution_model
                    if dynamic_generation.claude_max_iterations:
                        max_iterations = dynamic_generation.claude_max_iterations
            except Exception as e:
                logger.warning(f"[claude code] Failed to retrieve Claude Code settings: {e}")

        if node.system_env != ComputationSystemEnv.AWS_BATCH.value:
            raise Exception("Claude Code mode only supports AWS Batch execution")

        app = current_app._get_current_object()

        computation_id = computation.id
        dynamic_generation_id = node.dynamic_generation_id
        
        # Extract node IDs before starting background thread to avoid session issues
        previous_node_ids = [prev_node.id for prev_node in previous_nodes]

        def copy_and_launch_job():
            """Background thread to copy S3 data and launch AWS Batch job."""
            # Wrap entire function in app context to ensure database session works
            with app.app_context():
                try:
                    # Re-query nodes in the new session to avoid detached instance errors
                    nodes_to_process = [node_dao.find_by_id(node_id) for node_id in previous_node_ids]
                    
                    # Copy branch path data
                    for previous_node in nodes_to_process:
                        sync_s3_data_to_claude_code_bucket(
                            f"node-space/{previous_node.id}/params-files/",
                            f"node-space/{previous_node.id}/params-files/",
                            uploading_key=f"node_extra_files_{previous_node.id}"
                        )
                        if previous_node.type == NodeType.DATA_NODE_V2.value:
                            logger.info(f"[claude code] Copying branch path data (data node v2) for {previous_node.id} to Claude Code bucket...")
                            sync_s3_data_to_claude_code_bucket(
                                f"adata/{previous_node.data_id}-general-s3-store/",
                                f"adata/{previous_node.data_id}-general-s3-store/",
                                uploading_key=f"data_{previous_node.data_id}"
                            )
                        elif previous_node.type in [
                            NodeType.COMPUTATION_NODE_V2.value, 
                            NodeType.CLAUDE_CODE_NODE.value, 
                            NodeType.NOTEBOOK_NODE.value
                        ]:
                            latest_computation = computation_dao.find_latest_by_node_id(previous_node.id)
                            if latest_computation:
                                logger.info(f"[claude code] Copying branch path data (computation node v2) for {previous_node.id} to Claude Code bucket...")
                                sync_s3_data_to_claude_code_bucket(
                                    f"adata/{latest_computation.result_data_id}-general-s3-store/",
                                    f"adata/{latest_computation.result_data_id}-general-s3-store/",
                                    uploading_key=f"data_{latest_computation.result_data_id}"
                                )

                    if dynamic_generation_id:
                        logger.info(f"[claude code] Copying plan to Claude Code bucket...")
                        sync_plan_to_claude_code_bucket(dynamic_generation_id, node_id)

                    # Launch AWS Batch job
                    compute_type = computation_resource_configure.get("compute_type", "fargate")
                    job_id = ComputationLauncher.launch_aws_claude_code(
                        computation_id,
                        previous_computation_id,
                        computation_resource_configure=computation_resource_configure,
                        user_id=user_id,
                        node_id=node_id,
                        dynamic_generation_id=dynamic_generation_id,
                        claude_model=claude_model,
                        max_iterations=max_iterations,
                        source_data_ids=source_data_ids_str,
                        compute_type=compute_type
                    )

                    # Update computation state in database
                    computation_dao.update(computation_id, {
                        "computation_state": ComputationState.QUEUING.value,
                        "job_ident": job_id
                    })
                    from db import alchemy_db
                    alchemy_db.session.commit()
                    logger.info(f"[claude code] Successfully launched job {job_id} for computation {computation_id}")

                except Exception as e:
                    logger.error(f"[claude code] Failed to copy data or launch job for computation {computation_id}: {e}")
                    computation_dao.update(computation_id, {
                        "computation_state": ComputationState.FAILED.value,
                        "error_description": f"Failed to copy data or launch job: {str(e)}"
                    })
                    from db import alchemy_db
                    alchemy_db.session.commit()

        # Start background thread for S3 copy and job launch
        thread = threading.Thread(target=copy_and_launch_job)
        thread.start()
        logger.info(f"[claude code] Started background thread for computation {computation_id}")

        return computation

    def launch_computation(
        self,
        node_id,
        user_id,
        task_id,
        code_agent_config=None,
        visualizer_agent_config=None
    ):
        logger.info("Create computation for node %s" % node_id)
        node = node_dao.find_by_id(node_id)
        if node.type == NodeType.COMPUTATION_NODE.value:
            computation = self._launch_singularity_computation(
                node,
                user_id,
                task_id,
                code_agent_config,
                visualizer_agent_config
            )
            return computation
        elif node.type == NodeType.COMPUTATION_NODE_V2.value:
            computation = self._launch_singularity_computation(
                node,
                user_id,
                task_id,
                code_agent_config,
                visualizer_agent_config
            )
            return computation
        elif node.type in [NodeType.NOTEBOOK_NODE.value]:
            computation = self._launch_notebook_computation(
                node_id,
                user_id,
                task_id
            )
            return computation
        elif node.type in [NodeType.CLAUDE_CODE_NODE.value]:
            computation = self._launch_claude_code_computation(
                node_id,
                user_id,
                task_id
            )
            return computation
        else:
            raise Exception("Unsupported node type for computation: %s" % node.type)
        
        
    def check_params(self, node_id_list):
        nodes = node_dao.find_by_id_list(node_id_list)
        fb_vids = list(set([node.function_block_version_id for node in nodes]))
        if len(fb_vids) == 0:
            return
        fb_versions = function_block_v1_dao.find_version_by_version_id_list(
            fb_vids)
        fb_version_dict = {
            fb_version.id: fb_version for fb_version in fb_versions}
        for node in nodes:
            current_params = json.loads(node.computation_params)
            fb_v = fb_version_dict.get(node.function_block_version_id)
            arg_rules = json.loads(fb_v.args)
            arg_rule_dict = {arg_rule.get(
                "name", "unamed"): arg_rule for arg_rule in arg_rules}
            for arg_name, arg_value in current_params.items():
                arg_rule = arg_rule_dict.get(arg_name)
                if arg_rule is None:
                    continue
                if not arg_rule.get("optional", True) and arg_value is None:
                    raise ParameterInvalidException(
                        f"Argument {arg_name} in node {node.id}:{node.name} is required but not provided")

    def create(
        self,
        analysis_id,
        node_id_list,
        edge_id_list,
        user_id,
        code_agent_config=None,
        visualizer_agent_config=None
    ):
        now = datetime.now()
        edge_list = edge_dao.find_by_id_list(edge_id_list)
        # root nodes
        root_node_ids = FlowTool.get_root_ids_by_edge_list(
            edge_list, node_id_list)
        # leaf nodes
        leaf_node_ids = FlowTool.get_leaf_ids_by_edge_list(
            edge_list, node_id_list)
        # previous nodes
        previous_node_ids = []
        for root_node_id in root_node_ids:
            previous_edges = edge_dao.find_all_front_edges(root_node_id)
            previous_node_ids += [edge.source_node_id for edge in previous_edges]
        # next nodes
        after_node_ids = []
        for leaf_node_id in leaf_node_ids:
            next_edges = edge_dao.find_all_after_edges(leaf_node_id)
            after_node_ids += [edge.target_node_id for edge in next_edges]
        # affected nodes
        affected_node_ids = set(previous_node_ids)

        # insert task record
        task = Task(
            analysis_id=analysis_id,
            created_time=now,
            state=TaskState.CREATING.value
        )
        task_dao.insert(task)

        task_user_relation = TaskUserRelation(
            task_id=task.id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        task_dao.insert_user_relation(task_user_relation)

        # insert node relations that belong to this task
        involved_node_relation_list = [
            TaskNodeRelation(
                task_id=task.id,
                node_id=node_id,
                created_time=now,
                is_root=(True if node_id in root_node_ids else False),
                is_leaf=(True if node_id in leaf_node_ids else False),
                relation_type=TaskNodeRelationType.BELONG_TO.value
            )
            for node_id in node_id_list
        ]
        task_node_relation_dao.insert_list(involved_node_relation_list)

        # insert node relations affected by this task
        affected_node_relation_list = [
            TaskNodeRelation(
                task_id=task.id,
                node_id=node_id,
                created_time=now,
                is_root=False,
                is_leaf=False,
                relation_type=TaskNodeRelationType.BE_AFFECTED.value
            )
            for node_id in affected_node_ids
        ]
        task_node_relation_dao.insert_list(affected_node_relation_list)

        # insert edge relations that belong to this task
        edge_relation_list = [
            TaskEdgeRelation(
                task_id=task.id,
                edge_id=edge_id,
                created_time=now
            )
            for edge_id in edge_id_list
        ]
        task_edge_relation_dao.insert_list(edge_relation_list)

        # lock all related nodes except after_node_ids
        if len(node_id_list) > 0:
            node_dao.update_by_id_list(
                node_id_list,
                {'locked': True}
            )
        if len(previous_node_ids) > 0:
            node_dao.update_by_id_list(
                previous_node_ids,
                {'locked': True}
            )
        # for node_id in affected_node_ids:
        #     node_dao.update(node_id, {'locked': True})

        # update all after nodes to original state
        node_dao.update_by_id_list(
            after_node_ids,
            {
                'state': NodeState.ORIGINAL.value
            }
        )

        # update all belonged nodes to pending state
        node_dao.update_by_id_list(
            node_id_list,
            {
                'state': NodeState.PENDING.value
            }
        )

        # create computations for root nodes
        for node_id in root_node_ids:
            # Enable code_agent depending on whether we are inside a dynamic_generation
            self.launch_computation(
                node_id=node_id,
                user_id=user_id,
                task_id=task.id,
                code_agent_config=code_agent_config,
                visualizer_agent_config=visualizer_agent_config
            )

        task_dao.update(task.id, {
            "state": TaskState.RUNNING.value
        })

    def extend(
        self,
        node_id_list: list,
        edge_id_list: list
    ):
        now = datetime.now()
        edge_list = edge_dao.find_by_id_list(edge_id_list)
        # leaf nodes
        leaf_node_ids = FlowTool.get_leaf_ids_by_edge_list(
            edge_list, node_id_list)
        # root nodes
        root_node_ids = FlowTool.get_root_ids_by_edge_list(
            edge_list, node_id_list)
        if len(root_node_ids) != 1:
            raise ParameterInvalidException("Only one root node is allowed.")
        root_node_id = root_node_ids[0]
        previous_edge_of_root_node_list = edge_dao.find_by_target_node_id(
            root_node_id)
        if len(previous_edge_of_root_node_list) != 1:
            raise ParameterInvalidException(
                "Only one previous edge of root node is allowed.")
        previous_edge_of_root = previous_edge_of_root_node_list[0]
        edge_id_list.append(previous_edge_of_root.id)
        previous_node_of_root_node = node_dao.find_by_id(
            previous_edge_of_root.source_node_id)
        if previous_node_of_root_node.state in (NodeState.ORIGINAL.value, NodeState.CANCELLED.value):
            # The preceding node is in its initial state or has been cancelled; cannot attach
            raise ParameterInvalidException(
                "Cannot extend to a node whose previous node is original or cancelled.")
        if previous_node_of_root_node.state == NodeState.FINISHED.value:
            # The preceding node has already finished; cannot attach
            raise ParameterInvalidException(
                "Cannot extend to a node whose previous node is finished.")
        if previous_node_of_root_node.state == NodeState.FAILED.value:
            root_node_id = previous_node_of_root_node.id
            node_id_list.append(previous_node_of_root_node.id)
        latest_task_node_relation = task_node_relation_dao.find_latest_by_node_id(
            previous_node_of_root_node.id)
        latest_task = task_dao.find_by_id(latest_task_node_relation.task_id)
        if latest_task.state != TaskState.RUNNING.value:
            # The task is not running; cannot attach
            raise ParameterInvalidException(
                "Cannot extend to a task which is not running.")
        task_node_relation_dao.update(latest_task_node_relation.id, {
            "is_leaf": False
        })
        new_task_node_relation_list = []
        for node_id in node_id_list:
            exists_relation = task_node_relation_dao.find_by_task_id_and_node_id(
                latest_task_node_relation.task_id, node_id)
            if exists_relation is None:
                new_task_node_relation = TaskNodeRelation(
                    task_id=latest_task_node_relation.task_id,
                    node_id=node_id,
                    created_time=now,
                    is_root=False,
                    is_leaf=(True if node_id in leaf_node_ids else False),
                    relation_type=TaskNodeRelationType.BELONG_TO.value
                )
                new_task_node_relation_list.append(new_task_node_relation)
            elif exists_relation.relation_type != TaskNodeRelationType.BELONG_TO.value:
                task_node_relation_dao.update(exists_relation.id, {
                    "relation_type": TaskNodeRelationType.BELONG_TO.value
                })
        task_node_relation_dao.insert_list(new_task_node_relation_list)

        new_task_edge_relation_list = []
        for edge_id in edge_id_list:
            exists_relation = task_edge_relation_dao.find_by_task_id_and_edge_id(
                latest_task_node_relation.task_id, edge_id)
            if exists_relation is None:
                new_task_edge_relation = TaskEdgeRelation(
                    task_id=latest_task_node_relation.task_id,
                    edge_id=edge_id,
                    created_time=now
                )
                new_task_edge_relation_list.append(new_task_edge_relation)
        task_edge_relation_dao.insert_list(new_task_edge_relation_list)

        node_dao.update_by_id_list(
            node_id_list,
            {
                'state': NodeState.PENDING.value,
                'locked': True
            }
        )

    def _handle_logs(self, computation_id, logs, review_error):
        logs = logs.split("\n")
        logs = [log for log in logs if log.strip() != ""]
        logs = [{
            "message": log
        } for log in logs]
        computation_waiter = ComputationWaiter(computation_id)
        logs = json.dumps(logs, indent=4)
        computation_waiter.save_log(logs)
        if review_error is not None:
            computation_waiter.save_review_error(review_error)

    def handle_running_report(self, computation_id):
        computation = computation_dao.find(computation_id)
        if computation is None:
            raise Exception(
                "Cannot find computation by id {}".format(computation_id))
        if computation.computation_state == ComputationState.CANCELLED.value:
            return
        computation_dao.update(computation_id, {
            "computation_state": ComputationState.RUNNING.value,
            "start_time": datetime.now()
        })

    def handle_finished_report(self, computation_id, logs, job_review_passed=True, review_error=None):

        self._handle_logs(computation_id, logs, review_error)

        random_str = uuid.uuid4().hex
        temp_path = f"/tmp/{random_str}.json"
        with open(temp_path, "w") as f:
            json.dump({
                "success": True,
                "computation_id": computation_id,
                "job_review_passed": job_review_passed,
                "review_error": review_error,
                "error_description": None,
                "need_optimize": None
            }, f)
        _log_file = open(f"/tmp/handle_finished_report_{computation_id}.log", "w")
        subprocess.Popen(
            ["python3", os.path.join(CODE_SPACE_ROOT, 'handle_job_feedback', 'index.py')],
            env=_child_env({
                "DB_HOST": HOST,
                "DB_PORT": PORT,
                "DB_NAME": DATABASE,
                "DB_USER": USERNAME,
                "DB_PASSWORD": PASSWORD,
                "PYTHON_JOB_DEFINITION_SCANPY": PYTHON_JOB_DEFINITION_SCANPY,
                "PYTHON_JOB_DEFINITION_DYN": PYTHON_JOB_DEFINITION_DYN,
                "PYTHON_JOB_DEFINITION_MEBOCOST": PYTHON_JOB_DEFINITION_MEBOCOST,
                "PYTHON_JOB_DEFINITION_SCVELO": PYTHON_JOB_DEFINITION_SCVELO,
                "PYTHON_JOB_DEFINITION_SCFATES": PYTHON_JOB_DEFINITION_SCFATES,
                "PYTHON_JOB_DEFINITION_DEFAULT": PYTHON_JOB_DEFINITION_DEFAULT,
                "R_JOB_DEFINITION": R_JOB_DEFINITION,
                "JOB_QUEUE": JOB_QUEUE,
                "BASH_JOB_DEFINITION": BASH_JOB_DEFINITION,
                "DEPLOY_ENV": DEPLOY_ENV,
                "OPTIONS_PATH": temp_path,
                "GPT_WORKFLOW_SERVER_HOST": GPT_WORKFLOW_SERVER_HOST,
                "GPT_WORKFLOW_SERVER_PORT": GPT_WORKFLOW_SERVER_PORT,
                "NETWORK_PROXY_HOST": NETWORK_PROXY_HOST,
                "NETWORK_PROXY_PORT": NETWORK_PROXY_PORT,
                "BUCKET_NAME": BUCKET_NAME,
            }),
            stdout=_log_file,
            stderr=subprocess.STDOUT
        )
        _log_file.close()

    def handle_failed_report(self, computation_id, error_description, logs, need_optimize=True):

        self._handle_logs(computation_id, logs, None)

        random_str = uuid.uuid4().hex
        temp_path = f"/tmp/{random_str}.json"
        with open(temp_path, "w") as f:
            json.dump({
                "success": False,
                "computation_id": computation_id,
                "error_description": error_description,
                "need_optimize": need_optimize
            }, f)
        _log_file = open(f"/tmp/handle_failed_report_{computation_id}.log", "w")
        subprocess.Popen(
            ["python3", os.path.join(CODE_SPACE_ROOT, 'handle_job_feedback', 'index.py')],
            env=_child_env({
                "DB_HOST": HOST,
                "DB_PORT": PORT,
                "DB_NAME": DATABASE,
                "DB_USER": USERNAME,
                "DB_PASSWORD": PASSWORD,
                "PYTHON_JOB_DEFINITION_SCANPY": PYTHON_JOB_DEFINITION_SCANPY,
                "PYTHON_JOB_DEFINITION_DYN": PYTHON_JOB_DEFINITION_DYN,
                "PYTHON_JOB_DEFINITION_MEBOCOST": PYTHON_JOB_DEFINITION_MEBOCOST,
                "PYTHON_JOB_DEFINITION_SCVELO": PYTHON_JOB_DEFINITION_SCVELO,
                "PYTHON_JOB_DEFINITION_SCFATES": PYTHON_JOB_DEFINITION_SCFATES,
                "PYTHON_JOB_DEFINITION_DEFAULT": PYTHON_JOB_DEFINITION_DEFAULT,
                "BASH_JOB_DEFINITION": BASH_JOB_DEFINITION,
                "R_JOB_DEFINITION": R_JOB_DEFINITION,
                "JOB_QUEUE": JOB_QUEUE,
                "DEPLOY_ENV": DEPLOY_ENV,
                "OPTIONS_PATH": temp_path,
                "GPT_WORKFLOW_SERVER_HOST": GPT_WORKFLOW_SERVER_HOST,
                "GPT_WORKFLOW_SERVER_PORT": GPT_WORKFLOW_SERVER_PORT,
                "NETWORK_PROXY_HOST": NETWORK_PROXY_HOST,
                "NETWORK_PROXY_PORT": NETWORK_PROXY_PORT,
                "BUCKET_NAME": BUCKET_NAME,
            }),
            stdout=_log_file,
            stderr=subprocess.STDOUT
        )
        _log_file.close()

    def cancel(self, task_id):
        retry_process_list = computation_dao.find_retry_process_by_task_id(
            task_id)
        for retry_process in retry_process_list:
            if retry_process.state == ComputationRetryProcessState.STOPPED.value:
                continue
            computation_dao.update_retry_process(retry_process.id, {
                "state": ComputationRetryProcessState.STOPPED.value
            })
        task = task_dao.find_by_id(task_id)
        node_task_relation_list = task_node_relation_dao.find_by_task_id_and_relation_type(
            task.id, TaskNodeRelationType.BELONG_TO.value)
        node_id_list_released = []
        for node_task_relation in node_task_relation_list:
            node_id = node_task_relation.node_id
            node = node_dao.find_by_id(node_id)
            if node is None:
                continue
            # # update node state to cancelled if it is running or pending
            if node.state in (NodeState.PENDING.value, NodeState.RUNNING.value, NodeState.DEBUGGING.value):
                node_dao.update(node_id, {
                    "state": NodeState.CANCELLED.value
                })
                # cancel computation if the latest computation of this node is running
                latest_computation = computation_dao.find_latest_by_node_id(
                    node_id)
                if latest_computation is None or latest_computation.computation_state not in [
                    ComputationState.PENDING.value,
                    ComputationState.QUEUING.value,
                    ComputationState.RUNNING.value
                ]:
                    continue
                node_id_list_released.append(node_id)
                try:
                    if latest_computation.system_env == ComputationSystemEnv.AWS_BATCH.value:
                        ComputationLauncher.cancel_aws_computation(
                            latest_computation.job_ident)
                    elif latest_computation.system_env == ComputationSystemEnv.SERVER_LOCAL.value:
                        ComputationLauncher.cancel_local_computation(
                            latest_computation.id)
                    else:
                        raise Exception(
                            "Unsupported system env {}".format(latest_computation.system_env))
                except Exception as e:
                    logger.error("Cancel computation failed: {}".format(e))
                    raise Exception("Cancel computation failed")
                # if 'jobSummary' not in cancel_result:
                #     raise Exception("Cancel computation failed")
                computation_dao.update(latest_computation.id, {
                    "computation_state": ComputationState.CANCELLED.value,
                    "duration": (datetime.now() - latest_computation.start_time).total_seconds() if latest_computation.start_time is not None else 0,
                })
            if node.state in (NodeState.GENERATING.value, NodeState.BEAUTIFYING.value):
                node_dao.update(node_id, {
                    "state": NodeState.FINISHED.value
                })
            if node.state == NodeState.DEBUGGING.value:
                node_dao.update(node_id, {
                    "state": NodeState.FAILED.value
                })
        edge_list_released = edge_dao.find_by_target_node_id_list(
            node_id_list_released)
        task_node_relation_dao.delete_by_task_id_and_node_id_list(
            task.id,
            node_id_list_released
        )
        task_edge_relation_dao.delete_by_task_id_and_edge_id_list(
            task.id,
            [edge.id for edge in edge_list_released]
        )

    def cancel_by_analysis(self, analysis_id):
        task_list = task_dao.find_by_analysis_id(analysis_id)
        for task in task_list:
            self.cancel(task.id)

    def cancel_all_running(self):
        task_list = task_dao.find_by_state(TaskState.RUNNING.value)
        for task in task_list:
            logger.info("Cancel task {}".format(task.id))
            self.cancel(task.id)

    def cancel_branch(self, terminated_node_id):
        client = batch_client_factory.create_batch_client()
        # First find the latest task for this node
        terminated_node = node_dao.find_by_id(terminated_node_id)
        if terminated_node is None:
            raise Exception(f"Cannot find node by id {terminated_node_id}")
        # Check the node status
        if terminated_node.state not in (NodeState.PENDING.value, NodeState.RUNNING.value, NodeState.DEBUGGING.value):
            raise Exception(
                f"Node {terminated_node.name} (id: {terminated_node_id}) is not in pending or running state")
        task_node_relation = task_node_relation_dao.find_latest_by_node_id(
            terminated_node_id)
        if task_node_relation is None:
            raise Exception(
                f"Cannot find task on node {terminated_node.name} (id: {terminated_node_id})")

        # Find the latest computation for this node
        latest_computation = computation_dao.find_latest_by_node_id(
            terminated_node_id)
        if latest_computation is not None:
            try:
                if latest_computation.system_env == ComputationSystemEnv.AWS_BATCH.value:
                    ComputationLauncher.cancel_aws_computation(
                        latest_computation.job_ident)
                elif latest_computation.system_env == ComputationSystemEnv.SERVER_LOCAL.value:
                    ComputationLauncher.cancel_local_computation(
                        latest_computation.id)
                else:
                    raise Exception(
                        "Unsupported system env {}".format(latest_computation.system_env))
            except Exception as e:
                logger.error("Cancel computation failed: {}".format(e))
                raise Exception("Cancel computation failed")
            # if 'jobSummary' not in cancel_result:
            #     raise Exception("Cancel computation failed")
            computation_dao.update(latest_computation.id, {
                "computation_state": ComputationState.CANCELLED.value,
                "duration": (datetime.now() - latest_computation.start_time).total_seconds() if latest_computation.start_time is not None else 0,
            })

        # Find all downstream nodes of this node within the task
        all_after_edge_list = edge_dao.find_all_after_edges(
            terminated_node_id
        )
        all_after_node_id_set = {
            edge.target_node_id for edge in all_after_edge_list
        }
        node_task_relation_list = task_node_relation_dao.find_by_task_id_and_relation_type(
            task_node_relation.task_id, TaskNodeRelationType.BELONG_TO.value)
        all_task_node_id_set = {
            relation.node_id for relation in node_task_relation_list
        }
        node_id_list_after_this_node = list(
            all_after_node_id_set.intersection(all_task_node_id_set)
        )
        cancelled_node_id_list = node_id_list_after_this_node + \
            [terminated_node_id]
        node_dao.update_by_id_list(
            cancelled_node_id_list,
            {
                "state": NodeState.CANCELLED.value,
                "locked": False
            }
        )
        task_node_relation_dao.delete_by_task_id_and_node_id_list(
            task_node_relation.task_id,
            cancelled_node_id_list
        )

        released_edge_list = edge_dao.find_by_target_node_id_list(
            cancelled_node_id_list)
        task_edge_relation_dao.delete_by_task_id_and_edge_id_list(
            task_node_relation.task_id,
            [edge.id for edge in released_edge_list]
        )

    def unlock_nodes_interval(self):
        task_picker.scan()

    def force_unlock_nodes_by_analysis_id(self, analysis_id):
        node_list = node_dao.find_by_analysis_id(analysis_id)
        node_id_list = [node.id for node in node_list]
        node_dao.update_by_id_list(
            node_id_list,
            {
                "locked": False,
                "dynamic_generation_locked": False,
                "visualizer_locked": False,
            }
        )

    def force_unlock_all_nodes(self):
        """
        Force-unlock all nodes; used for initialization after a server restart
        Resolves abnormal lock states
        """
        logger.info("Force unlocking all nodes to resolve lock anomalies")
        try:
            # Delegate database operations to the dao layer
            from dao.node import node_dao
            node_dao.force_unlock_all_nodes()
            from db import alchemy_db
            alchemy_db.session.commit()
            logger.info("Successfully unlocked all nodes via DAO")
        except Exception as e:
            logger.error(f"Failed to force unlock all nodes: {e}")
            from db import alchemy_db
            alchemy_db.session.rollback()
            raise e

    def invoke_code_agent(self, node_id: int, max_debug: int, model: str, user_id: int):
        node = node_dao.find_by_id(node_id)
        if node is None:
            raise Exception(f"Cannot find node by id {node_id}")
        now = datetime.now()
        task = Task(
            analysis_id=node.analysis_id,
            created_time=now,
            state=TaskState.CREATING.value
        )
        task_dao.insert(task)

        task_user_relation = TaskUserRelation(
            task_id=task.id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        task_dao.insert_user_relation(task_user_relation)

        task_node_relation = TaskNodeRelation(
            task_id=task.id,
            node_id=node.id,
            created_time=now,
            is_root=True,
            is_leaf=True,
            relation_type=TaskNodeRelationType.BELONG_TO.value
        )
        task_node_relation_dao.insert_list([task_node_relation])

        alchemy_db.session.commit()

        self.launch_computation(
            node_id=node.id,
            user_id=user_id,
            task_id=task.id,
            code_agent_config={
                "enable": True,
                "model": model,
                "max_attempts": max_debug
            }
        )

    def invoke_visualizer_agent(self, node_id: int, model: str, optional_figure_counts: int, visualizer_demand: str, user_id: int):
        node = node_dao.find_by_id(node_id)
        if node is None:
            raise Exception(f"Cannot find node by id {node_id}")
        now = datetime.now()
        task = Task(
            analysis_id=node.analysis_id,
            created_time=now,
            state=TaskState.CREATING.value
        )
        task_dao.insert(task)

        task_user_relation = TaskUserRelation(
            task_id=task.id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        task_dao.insert_user_relation(task_user_relation)

        task_node_relation = TaskNodeRelation(
            task_id=task.id,
            node_id=node.id,
            created_time=now,
            is_root=True,
            is_leaf=True,
            relation_type=TaskNodeRelationType.BELONG_TO.value
        )
        task_node_relation_dao.insert_list([task_node_relation])

        alchemy_db.session.commit()

        self.launch_computation(
            node_id=node.id,
            user_id=user_id,
            task_id=task.id,
            visualizer_agent_config={
                "enable": True,
                "model": model,
                "optional_figure_counts": optional_figure_counts,
                "visualizer_demand": visualizer_demand
            }
        )


task_service = TaskService()

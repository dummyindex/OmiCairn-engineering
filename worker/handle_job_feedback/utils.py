from typing import Dict, List
import re
from db import (
    Data,
    DataUserRelation,
    Node,
    DynamicGeneration,
    DynamicGenerationSession,
    LLMConsumption,
    Computation,
    ComputationUserRelation,
    FunctionBlockV1,
    FunctionBlockVersionV1,
    FunctionBlockGroup,
    FunctionBlockGroupUserRelation,
    FunctionBlockUserRelation,
    DataUserRelation,
    update_node,
    find_fb_by_id, find_fb_version_by_id,
    find_data_by_id,
    insert_computation,
    insert_computation_user_relation,
    update_computation,
    find_latest_computation_by_node_id,
    find_edges_by_target_node_id,
    find_node_by_id,
    find_previous_node_by_node_id,
    insert_data,
    find_latest_computation_by_retry_process_id,
    insert_data_user_relation,
    find_fb_group_by_owner_id_and_name,
    find_computation_by_retry_process_id,
    insert_fb_group,
    insert_fb_group_user_relation,
    insert_fb,
    insert_fb_user_relation,
    insert_fb_version,
    update_fb,
    insert_session,
    insert_consumption
)

from constants import (
    DataState,
    ComputationState,
    ComputationSystemEnv,
    CreatedFrom,
    NodeState,
    NodeType,
    Relation,
    Permission,
    FUNCTION_BLOCK_VERSION_PREFIX
)
from datetime import datetime
from computation_launcher import ComputationLauncher
from server_agent import ServerAgent
from waiter.computation_options import ComputationOptionsWaiter
from waiter.function_block_v1_waiter import FunctionBlockV1Waiter
from waiter.retry_process_waiter import RetryProcessWaiter
from waiter.dynamic_generation_waiter import DynamicGenerationWaiter
import json
from sss.porter_factory import PorterFactory
from llm_interface import LlmInterface

from logger_factory import LoggerFactory
import traceback
logger = LoggerFactory.get_logger(__name__)


def fetch_computation_history(user_id, node_id):
    server_agent = ServerAgent(user_id)
    response = server_agent.get_computation_history(node_id)
    computation_history = response["data"]
    logger.info(
        f"Computation history: {len(computation_history)}")
    return computation_history


def launch_computation(
    node_id: Node,
    user_id,
    task_id,
    retry_process_id=None,
    code_agent_config=None,
):
    now = datetime.now()
    node = find_node_by_id(node_id)
    logger.info("Create computation for node %s" % node.id)
    no_source = False
    # search source data list
    prev_edge_list = find_edges_by_target_node_id(node.id)
    if len(prev_edge_list) == 0:
        no_source = True
    logger.info("Previous edge list: %s" % prev_edge_list)
    source_data_ids = []
    previous_computation_id = -1
    for prev_edge in prev_edge_list:
        prev_node_id = prev_edge.source_node_id
        previous_node = find_node_by_id(prev_node_id)
        if previous_node.type in [NodeType.DATA_NODE.value, NodeType.DATA_NODE_V2.value]:
            source_data_ids.append(previous_node.data_id)
        elif previous_node.type in [NodeType.COMPUTATION_NODE.value, NodeType.COMPUTATION_NODE_V2.value]:
            computation = \
                find_latest_computation_by_node_id(prev_node_id)
            source_data_ids.append(computation.result_data_id)
            previous_computation_id = computation.id
    if not no_source:
        source_data_ids_str = json.dumps(source_data_ids)
        first_data = find_data_by_id(source_data_ids[0])
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
        insert_data(result_data)
        result_data_id = result_data.id
        data_user_relation = DataUserRelation(
            data_id=result_data_id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        insert_data_user_relation(data_user_relation)
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
        retry_process_id=retry_process_id,
        previous_computation_id=previous_computation_id,
        duration=0,
        job_ident=None,
        start_time=now,
        enable_code_agent=code_agent_config.get("enable", False) if code_agent_config else False,
    )
    insert_computation(computation)
    computation_user_relation = ComputationUserRelation(
        computation_id=computation.id,
        user_id=user_id,
        relation=Relation.BELONG_TO.value,
        permission=Permission.ADMIN.value
    )
    insert_computation_user_relation(computation_user_relation)
    update_node(node.id, {'state': NodeState.RUNNING.value})

    function_block = find_fb_by_id(
        computation.function_block_id)
    function_block_version = find_fb_version_by_id(
        computation.function_block_version_id)
    options = {}
    options["computation_params"] = json.loads(
        computation.computation_params or "{}")
    options["fb_id"] = computation.function_block_id
    options["fb_version_id"] = computation.function_block_version_id
    options["source_data_ids"] = json.loads(
        computation.source_data_ids or "[]")
    options["result_data_id"] = computation.result_data_id
    options["fb_type"] = function_block.type
    options["node_id"] = computation.node_id
    options["analysis_id"] = node.analysis_id
    options["fb_name"] = function_block.name
    options["ploy_only"] = function_block_version.plot_only
    options["runtime_version"] = function_block_version.runtime_version
    options["preset_env"] = function_block_version.preset_env

    computation_options_waiter = ComputationOptionsWaiter(computation.id)
    computation_options_waiter.save_computation_options(options)

    computation_resource_configure = json.loads(
        computation.computation_resource_configure)

    if node.system_env == ComputationSystemEnv.SERVER_LOCAL.value:
        if function_block_version.is_v2:
            job_id = ComputationLauncher.launch_local_computation_v2(
                computation.id, previous_computation_id, function_block_version.program_language, function_block_version.preset_env, user_id, node_id, code_agent_config)
        else:
            job_id = ComputationLauncher.launch_local_computation(
                computation.id, previous_computation_id, function_block_version.program_language, function_block_version.preset_env, user_id, node_id)

    elif node.system_env == ComputationSystemEnv.AWS_BATCH.value:
        if function_block_version.is_v2:
            job_id = ComputationLauncher.launch_aws_computation_v2(
                computation.id, previous_computation_id, function_block_version.program_language, computation_resource_configure, function_block_version.preset_env, user_id, node_id, code_agent_config)
        else:
            job_id = ComputationLauncher.launch_aws_computation(
                computation.id, previous_computation_id, function_block_version.program_language, computation_resource_configure, function_block_version.preset_env, user_id, node_id)
    update_computation(computation.id, {
        "computation_state": ComputationState.QUEUING.value,
        "job_ident": job_id
    })
    return 0  # success


def copy_fb(source_fb_id, source_fb_version_id, user_id, new_core_code=None):
    source_fb = find_fb_by_id(source_fb_id)
    source_fb_version = find_fb_version_by_id(source_fb_version_id)
    particular_fb_group = find_fb_group_by_owner_id_and_name(
        user_id, "__bug_fixer_generated__"
    )
    if particular_fb_group is None:
        particular_fb_group = FunctionBlockGroup(
            name="__bug_fixer_generated__",
            created_time=datetime.now(),
            serial_number=-100,
            alt_name="__bug_fixer_generated__",
        )
        insert_fb_group(particular_fb_group)
        fb_group_user_relation = FunctionBlockGroupUserRelation(
            function_block_group_id=particular_fb_group.id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        insert_fb_group_user_relation(fb_group_user_relation)
    new_fb = FunctionBlockV1(
        name=source_fb.name,
        group_id=particular_fb_group.id,
        current_version_id=None,
        created_time=datetime.now(),
        type=source_fb.type,
        occasion=source_fb.occasion,
        alt_name=source_fb.alt_name,
    )
    insert_fb(new_fb)
    new_fb_user_relation = FunctionBlockUserRelation(
        user_id=user_id,
        function_block_id=new_fb.id,
        relation=Relation.BELONG_TO.value,
        permission=Permission.ADMIN.value
    )
    insert_fb_user_relation(new_fb_user_relation)
    new_fb_version = FunctionBlockVersionV1(
        name=source_fb_version.name,
        function_block_id=new_fb.id,
        args=source_fb_version.args,
        tag=source_fb_version.tag,
        document_url=source_fb_version.document_url,
        description=source_fb_version.description,
        source=source_fb_version.source,
        plot_only=source_fb_version.plot_only,
        runtime_version=source_fb_version.runtime_version,
        created_time=datetime.now(),
        state=source_fb_version.state,
        program_language=source_fb_version.program_language,
        error_message=source_fb_version.error_message,
        preset_env=source_fb_version.preset_env,
        is_v2=source_fb_version.is_v2,
    )
    insert_fb_version(new_fb_version)
    update_fb(new_fb.id, {"current_version_id": new_fb_version.id})
    fb_waiter = FunctionBlockV1Waiter(
        new_fb_version.id, new_fb_version.program_language)
    fb_waiter.copy(source_fb_version_id)
    if new_core_code is not None:
        fb_waiter.rewrite_core_code(new_core_code)
    return new_fb, new_fb_version


def copy_and_rewrite_fb(node: Node, user_id, llm_model, retry_process_id=None, user_prompt: str = None):
    llm_interface = LlmInterface()
    computation_history = fetch_computation_history(user_id, node.id)
    logger.info(f"Node: {node.id}")
    current_computation = find_latest_computation_by_node_id(node.id)
    if retry_process_id is not None and len(computation_history) > 0:
        retry_process_waiter = RetryProcessWaiter(retry_process_id)
        retry_process_waiter.save_node_computation_information(
            current_computation.id, computation_history[-1]
        )
    new_fb, new_fbv = copy_fb(
        node.function_block_id, node.function_block_version_id, user_id, None)
    fixer_history_details = get_retry_process_history_details_str(
        retry_process_id)
    session_id = None
    max_retry = 5
    for i in range(max_retry):
        start_time = datetime.now()
        try:
            _computation_history = [item for item in computation_history]
            response = llm_interface.get_bug_advise(
                node.id, None, _computation_history, fixer_history_details, 1, user_id, llm_model, retry_process_id, current_computation.id, user_prompt)
            end_time = datetime.now()
            if response is None or response.status_code != 200:
                raise Exception(
                    f"Failed to get bug advise from LLM, response: {response}"
                )
        except Exception as e:
            end_time = datetime.now()
            logger.error(
                f"Failed to get bug advise from LLM for node {node.id}, attempt {i + 1} of {max_retry}")
            logger.error(e)
            logger.error(traceback.format_exc())
            session_id = record_session(
                user_id, node.id, retry_process_id, node.dynamic_generation_id, current_computation.id, None, "Code Fixer", is_valid=False, errors=str([traceback.format_exc()]), start_time=start_time, end_time=end_time)
            if i < max_retry - 1:
                logger.error(f"Retrying... ({i + 1}/{max_retry})")
                continue
            else:
                logger.error(
                    f"Failed to get bug advise after {max_retry} attempts")
                return False, None, None, "{}"

        response_data = response.json()
        result = response_data.get("data", {})
        consumption = response_data.get("consumption", "{}")

        consumption_id = record_consumption(
            user_id, node.id, retry_process_id, consumption)

        raw_response = response_data.get("message", "")
        is_valid, errors = validate_fixer_output_json(
            raw_response, "code")
        session_id = record_session(
            user_id, node.id, retry_process_id, node.dynamic_generation_id, current_computation.id, consumption_id, "Code Fixer", is_valid, str(errors), start_time=start_time, end_time=end_time)
        if not is_valid:
            logger.error(f"Invalid response from LLM: {errors}")
            if i < max_retry - 1:
                logger.error(f"Retrying... ({i + 1}/{max_retry})")
                continue
            else:
                logger.error(
                    f"Failed to get valid response after {max_retry} attempts")
                return False, None, None, "{}"
        prompt = result.get("prompt", "")
        if retry_process_id is not None:
            retry_process_waiter = RetryProcessWaiter(retry_process_id)
            retry_process_waiter.save_code_fix_solution(
                current_computation, response_data
            )
            retry_process_waiter.save_a_session(
                session_id, prompt, raw_response)
        try:
            program_language = result.get("programming_language", "Python")
            program_language = program_language.strip(
            ).capitalize() if program_language else "Python"
            fb_waiter = FunctionBlockV1Waiter(
                new_fbv.id, program_language)
            code = result.get("code", "")
            fb_waiter.rewrite_core_code(code)

            static_config = result.get("static_config", {})
            fb_waiter.rewrite_static_config(static_config)
            requirements_content = result.get("requirements", "")
            if type(requirements_content) is not str:
                requirements_content = str(
                    requirements_content) if requirements_content is not None else ""
            fb_waiter.rewrite_requirement_file(requirements_content)
            install_script = result.get("install_script", "")
            fb_waiter.rewrite_install_script(install_script)

            parameters = result.get("parameters", "{}")
            if type(parameters) is not str:
                parameters = json.dumps(parameters or {}, ensure_ascii=False)
            return True, new_fb, new_fbv, parameters
        except Exception as e:
            logger.error(f"Error while copying files: {e}")
            return False, None, None, "{}"



def record_dynamic_generation_consumption(
    server_agent: ServerAgent,
    consumption: dict,
    node_id: int,
    dynamic_generation_id: int
):
    consumption["node_id"] = node_id
    consumption["functionality"] = "Auto Genie"
    consumption["functionality_task_id"] = dynamic_generation_id
    llm_consumption_record_response = server_agent.record_llm_consumption(
        consumption)
    if llm_consumption_record_response is None:
        logger.warning("Failed to record consumption, returning None")
        return None
    consumption_id = llm_consumption_record_response["data"]["id"]
    return consumption_id


def record_dynamic_generation_session(
    server_agent: ServerAgent,
    dynamic_generation_id: int,
    source_node_id: int,
    consumption_id: int,
    is_valid: bool = True,
    errors: str = None,
    created_at: datetime = None,
    type: str = None,
    start_time: datetime = None,
    end_time: datetime = None
):
    # Convert datetime to timestamp if provided
    created_at_timestamp = None
    if created_at is not None:
        created_at_timestamp = created_at.timestamp() * 1000

    start_time_timestamp = None
    if start_time is not None:
        start_time_timestamp = start_time.timestamp() * 1000

    end_time_timestamp = None
    if end_time is not None:
        end_time_timestamp = end_time.timestamp() * 1000

    response = server_agent.record_dynamic_generation_session(
        {
            "dynamic_generation_id": dynamic_generation_id,
            "source_node_id": source_node_id,
            "consumption_id": consumption_id,
            "is_valid": is_valid,
            "errors": errors,
            "created_at": created_at_timestamp,
            "type": type,
            "start_time": start_time_timestamp,
            "end_time": end_time_timestamp
        }
    )
    if response is None:
        return None
    return response.get("data", {}).get("id", None)


def record_consumption(
    user_id: str,
    node_id: str,
    retry_process_id: str = None,
    consumption: Dict = None
) -> int:
    """
    Record the consumption of a computation.

    :param user_id: The ID of the user.
    :param node_id: The ID of the node.
    :param retry_process_id: The ID of the retry process, if applicable.
    :param consumption: A dictionary containing consumption details.
    :return: The ID of the recorded consumption.
    """
    server_agent = ServerAgent(user_id)
    if consumption is None:
        consumption = {}
    consumption["node_id"] = node_id
    consumption["functionality"] = "Bug Fixer"
    consumption["functionality_task_id"] = retry_process_id
    consumption_response = server_agent.record_llm_consumption(consumption)
    return consumption_response["data"]["id"]


def record_session(
    user_id: str,
    node_id: str,
    retry_process_id: str = None,
    dynamic_generation_id: int = None,
    fixed_computation_id: int = None,
    consumption_id: int = None,
    type: str = "Unknown",
    is_valid: bool = True,
    errors: str = None,
    start_time: datetime = None,
    end_time: datetime = None
):
    """
    Record a session for a computation.

    :param user_id: The ID of the user.
    :param node_id: The ID of the node.
    :param retry_process_id: The ID of the retry process, if applicable.
    :param fixed_computation_id: The ID of the computation that was fixed, if applicable.
    :return: The ID of the recorded session.
    """
    # Convert datetime to timestamp if provided
    start_time_timestamp = None
    if start_time is not None:
        start_time_timestamp = start_time.timestamp() * 1000
        
    end_time_timestamp = None
    if end_time is not None:
        end_time_timestamp = end_time.timestamp() * 1000
    
    server_agent = ServerAgent(user_id)
    session_response = server_agent.record_bug_fixer_session({
        "node_id": node_id,
        "retry_process_id": retry_process_id,
        "fixed_computation_id": fixed_computation_id,
        "dynamic_generation_id": dynamic_generation_id,
        "consumption_id": consumption_id,
        "type": type,
        "is_valid": is_valid,
        "errors": errors,
        "start_time": start_time_timestamp,
        "end_time": end_time_timestamp
    })
    return session_response["data"]["id"]


def fix_params(node: Node, user_id, llm_model, retry_process_id=None, user_prompt: str = None):
    llm_interface = LlmInterface()
    computation_history = fetch_computation_history(user_id, node.id)
    current_computation = find_latest_computation_by_node_id(node.id)
    args_values = json.loads(node.computation_params)
    if retry_process_id is not None and len(computation_history) > 0:
        retry_process_waiter = RetryProcessWaiter(retry_process_id)
        retry_process_waiter.save_node_computation_information(
            current_computation.id, computation_history[-1]
        )
    logger.info("-----------------------------------Launching llm interface")
    fixer_history_details = get_retry_process_history_details_str(
        retry_process_id)
    session_id = None
    max_retry = 5
    for i in range(max_retry):
        start_time = datetime.now()
        try:
            logger.info(f"Attempt {i + 1} to fix params for node {node.id}")
            response = llm_interface.get_bug_advise(
                node.id, args_values, computation_history, fixer_history_details, 0, user_id, llm_model, retry_process_id, current_computation.id, user_prompt)
            end_time = datetime.now()
            if response is None or response.status_code != 200:
                raise Exception(
                    f"Failed to get response from LLM interface for node {node.id}, status code")
        except Exception as e:
            end_time = datetime.now()
            logger.error(
                f"Failed to fix params for node {node.id}, attempt {i + 1} of {max_retry}")
            logger.error(e)
            traceback.print_exc()
            session_id = record_session(
                user_id, node.id, retry_process_id, node.dynamic_generation_id, current_computation.id, None, "Params Fixer", is_valid=False, errors=str(e), start_time=start_time, end_time=end_time)
            if i < max_retry - 1:
                logger.error(
                    f"Failed to get response from LLM interface for node {node.id}, retrying...")
                continue
            else:
                logger.error(
                    f"Failed to get response from LLM interface for node {node.id} after {max_retry} attempts")
                return False
        response_data = response.json()
        consumption = response_data.get("consumption", {})
        raw_response_text = response_data.get("message", "")

        is_valid, errors = validate_fixer_output_json(
            raw_response_text, "parameter")
        consumption_id = record_consumption(
            user_id, node.id, retry_process_id, consumption)
        session_id = record_session(
            user_id, node.id, retry_process_id, node.dynamic_generation_id, current_computation.id, consumption_id, "Params Fixer", is_valid=is_valid, errors=str(errors), start_time=start_time, end_time=end_time)
        if is_valid:
            logger.info(
                f"Successfully fixed params for node {node.id}")
            new_params_pack = response_data.get("data", {})

            raw_response = response_data.get("message", "")
            new_params = new_params_pack.get("extracted_result")
            raw_prompt = new_params_pack.get("prompt", "")
            if retry_process_id is not None:
                retry_process_waiter = RetryProcessWaiter(retry_process_id)
                retry_process_waiter.save_parameters_fix_solution(
                    current_computation.id, response_data
                )
                retry_process_waiter.save_a_session(
                    session_id, raw_prompt, raw_response
                )
            logger.info(
                f"Filled params for node {node.id}: {new_params}"
            )
            old_params = json.loads(node.computation_params)
            old_params.update(new_params)
            update_node(
                node.id,
                {
                    "computation_params": json.dumps(old_params)
                }
            )
            logger.info(
                f"Updated computation params for node {node.id}: {old_params}")
            return True
        elif i < max_retry - 1:
            logger.error(
                f"Invalid dynamic generation output: {errors}, retrying...")
        else:
            logger.error(
                f"Failed to fix params for node {node.id} after {max_retry} attempts")
            return False


def create_next_level_fbs(user_id, node: Node, generation_id, max_branch_count, generation_mode, llm_model, file_ids=None):
    particular_fb_group = find_fb_group_by_owner_id_and_name(
        user_id, "__dynamic_fb_generated__"
    )
    if particular_fb_group is None:
        particular_fb_group = FunctionBlockGroup(
            name="__dynamic_fb_generated__",
            created_time=datetime.now(),
            serial_number=-100,
            alt_name="__dynamic_fb_generated__",
        )
        insert_fb_group(particular_fb_group)
        fb_group_user_relation = FunctionBlockGroupUserRelation(
            function_block_group_id=particular_fb_group.id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        insert_fb_group_user_relation(fb_group_user_relation)
    dynamic_generation_waiter = DynamicGenerationWaiter(generation_id)
    rest_task = dynamic_generation_waiter.get_rest_task(node.id)

    llm_interface = LlmInterface()
    computation_history = fetch_computation_history(user_id, node.id)
    server_agent = ServerAgent(user_id)
    session_id = None
    max_retry = 5
    for i in range(max_retry):
        start_time = datetime.now()
        try:
            response = llm_interface.dynamic_fb(
                rest_task,
                node.id,
                computation_history,
                user_id,
                llm_model,
                max_branch_count,
                generation_mode,
                file_ids
            )
            end_time = datetime.now()
            if response is None or response.status_code != 200:
                raise Exception(
                    f"LLM interface returned an error: {response.status_code} - {response.text}"
                )

        except Exception as e:
            end_time = datetime.now()
            logger.error(e)
            record_dynamic_generation_session(
                server_agent,
                generation_id,
                node.id,
                None,
                is_valid=False,
                errors=str(e),
                created_at=datetime.now(),
                type="generation",
                start_time=start_time,
                end_time=end_time
            )
            if i < max_retry - 1:
                logger.error(
                    f"Failed to get response from LLM interface for node {node.id}, retrying...")
                continue
            else:
                logger.error(
                    f"Failed to get response from LLM interface for node {node.id} after {max_retry} attempts")
                return []
        response_json = response.json()
        consumption = response_json.get("consumption", {}) or {}
        consumption_id = record_dynamic_generation_consumption(
            server_agent, consumption, node.id, generation_id)

        # Handle case where consumption recording failed
        if consumption_id is None:
            logger.warning(
                f"Failed to record consumption for node {node.id}, continuing with None consumption_id")

        raw_response_text = response_json.get("message")
        is_valid, errors = validate_dynamic_generation_output_json(
            raw_response_text)
        session_id = record_dynamic_generation_session(
            server_agent,
            generation_id,
            node.id,
            consumption_id,
            is_valid=is_valid,
            errors=json.dumps(errors, ensure_ascii=False),
            created_at=datetime.now(),
            type="generation",
            start_time=start_time,
            end_time=end_time
        )
        if is_valid:
            break
        elif i < max_retry - 1:
            logger.error(
                f"Invalid dynamic generation output: {errors}, retrying...")
        else:
            logger.error(
                f"Invalid dynamic generation output after {max_retry} attempts: {errors}")
            return []
    result = response_json.get("data", {})
    satisfied = result.get("satisfied", False)
    prompt = result.get("prompt", "")
    if "prompt" in result:
        del result["prompt"]
    next_level_function_blocks = result.get("next_level_function_blocks", [])
    result_fb_list = []
    if satisfied:
        return result_fb_list
    for next_level_fb in next_level_function_blocks:
        logger.info(f"Creating function block: {next_level_fb}")
        remaining_tasks = next_level_fb.get("remaining_tasks", None)
        is_new_fb = next_level_fb.get("id", None) is None
        if not is_new_fb:
            id = next_level_fb.get("id", None)
            fb_id, fb_v_id = id.split("-")
            next_level_fb["fb_id"] = fb_id
            next_level_fb["fb_version_id"] = fb_v_id
            fb = find_fb_by_id(fb_id)
            fb_v = find_fb_version_by_id(fb_v_id)
            result_fb_list.append({
                "fb_id": fb_id,
                "fb_version_id": fb_v_id,
                "fb_name": fb.name,
                "fb_version_name": fb_v.name,
                "parameters": next_level_fb.get("parameters", "{}"),
                "remaining_tasks": remaining_tasks,
                "session_id": session_id
            })
        else:
            logger.info(f"Creating function block: {next_level_fb}")
            programming_language = next_level_fb.get(
                "programming_language", "Python")
            name = next_level_fb.get("name", "unamed")
            code_code = next_level_fb.get("function_block_code", "")
            parameters = next_level_fb.get("parameters", "{}")
            preset_env = next_level_fb.get("preset_env", None)
            static_config = next_level_fb.get(
                "static_config_file_content", {})
            static_config = fill_default_for_static_config(static_config)
            requirements_content = next_level_fb.get(
                "requirements_file_content", "")
            args = static_config.get("args", [])
            tag = static_config.get("tag", "")
            document_url = static_config.get("document_url", "")
            description = static_config.get("description", "")
            source = static_config.get("source", "")
            preset_env = static_config.get("preset_env", None)
            new_fb = FunctionBlockV1(
                name=name,
                group_id=particular_fb_group.id,
                current_version_id=None,
                created_time=datetime.now(),
                type="computation",
                occasion="flow",
                alt_name=name,
            )
            insert_fb(new_fb)
            new_fb_user_relation = FunctionBlockUserRelation(
                user_id=user_id,
                function_block_id=new_fb.id,
                relation=Relation.BELONG_TO.value,
                permission=Permission.ADMIN.value
            )
            insert_fb_user_relation(new_fb_user_relation)
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
                program_language=programming_language,
                error_message=None,
                preset_env=preset_env
            )
            insert_fb_version(new_fb_version)
            update_fb(new_fb.id, {"current_version_id": new_fb_version.id})
            next_level_fb["fb_id"] = new_fb.id
            next_level_fb["fb_version_id"] = new_fb_version.id
            fb_waiter = FunctionBlockV1Waiter(
                new_fb_version.id, new_fb_version.program_language)
            fb_waiter.rewrite_core_code(code_code)
            fb_waiter.rewrite_static_config(static_config)
            fb_waiter.rewrite_requirement_file(requirements_content)
            result_fb_list.append({
                "fb_id": new_fb.id,
                "fb_version_id": new_fb_version.id,
                "fb_name": name,
                "fb_version_name": name,
                "parameters": parameters,
                "remaining_tasks": remaining_tasks,
                "session_id": session_id
            })

        dynamic_generation_waiter.save_log(
            session_id, prompt, json.dumps(result, indent=4))
    return result_fb_list

def _create_fb_v2(user_id, next_level_fb, particular_fb_group: FunctionBlockGroup):
    current_plan = next_level_fb.get("current_plan", None)
    parameters = next_level_fb.get("parameters", "{}")
    static_config = next_level_fb.get("files", {}).get("static-config.json", "{}")
    static_config = json.loads(static_config)
    static_config = fill_default_for_static_config(static_config)
    programming_language = static_config.get(
        "programming_language", "Python")
    name = static_config.get("name", "unamed")
    args = static_config.get("args", [])
    tag = static_config.get("tag", "")
    document_url = static_config.get("document_url", "")
    description = static_config.get("description", "")
    source = static_config.get("source", "")
    preset_env = static_config.get("preset_env", None)

    # Create new function block
    new_fb = FunctionBlockV1(
        name=name,
        group_id=particular_fb_group.id,
        current_version_id=None,
        created_time=datetime.now(),
        type="computation",
        occasion="flow",
        alt_name=name,
    )
    insert_fb(new_fb)
    new_fb_user_relation = FunctionBlockUserRelation(
        user_id=user_id,
        function_block_id=new_fb.id,
        relation=Relation.BELONG_TO.value,
        permission=Permission.ADMIN.value
    )
    insert_fb_user_relation(new_fb_user_relation)

    # Create new function block version
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
        program_language=programming_language,
        error_message=None,
        preset_env=preset_env,
        is_v2=True,
    )
    insert_fb_version(new_fb_version)
    update_fb(new_fb.id, {"current_version_id": new_fb_version.id})

    # Initialize FB waiter for file operations
    fb_waiter = FunctionBlockV1Waiter(
        new_fb_version.id, new_fb_version.program_language)

    # Handle files field (v2 specific)
    files = next_level_fb.get("files", None)
    if files and isinstance(files, dict):
        for file_name, file_content in files.items():
            if file_content is not None:
                logger.info(f"Adding file {file_name} to FB {new_fb.id}")
                fb_waiter.add_file(file_name, file_content)

    return {
        "fb_id": new_fb.id,
        "fb_version_id": new_fb_version.id,
        "fb_name": name,
        "fb_version_name": name,
        "parameters": parameters,
        "current_plan": current_plan
    }

def _get_existing_fbvs_v2(server_agent: ServerAgent):
    fbvs_response = server_agent.fetch_existing_fbvs_v2()
    fbvs = fbvs_response.get("data", []) if fbvs_response else []
    existing_fbv_str = """
--- Existing Function Block Versions Start --- 
"""
    for fbv in fbvs:
        fb_name = fbv.get("fbName", "Unknown FB Name")
        fbv_name = fbv.get("fbvName", "Unknown FBV Name")
        fbv_id = fbv.get("fbVersionId", "Unknown FBV ID")
        fbv_description = fbv.get("fbvDescription", "No Description")
        fbv_programming_language = fbv.get("fbvProgrammingLanguage", None)
        fbv_args_definition = fbv.get("fbvArgs", "{}")
        existing_fbv_str += f"""
- fb_name: {fb_name}
- fbv_id: {fbv_id}
- fbv_description: {fbv_description}
- fbv_programming_language: {fbv_programming_language}
- fbv_args_definition: {fbv_args_definition}
------
"""
    existing_fbv_str += """
--- Existing Function Block Versions End ---
""" 
    return existing_fbv_str


def validate_v2_output_json(json_data_text):
    """
    Quickly check that the key fields of the structured_output JSON returned by GPT are present (v2)

    Args:
        json_data: parsed JSON data

    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    try:
        json_data = json.loads(json_data_text)
    except Exception as e:
        return False, [f"JSON decode error: {str(e)} - {json_data_text}"]

    errors = []

    json_data = json_data.get("data", {})

    try:
        # Check required top-level fields
        top_level_required = ['satisfied', 'next_level_function_blocks']
        for field in top_level_required:
            if field not in json_data:
                errors.append(f"Missing top-level required field '{field}'")

        # Check the next_level_function_blocks array
        if 'next_level_function_blocks' in json_data and isinstance(json_data['next_level_function_blocks'], list):
            for i, fb in enumerate(json_data['next_level_function_blocks']):
                if not isinstance(fb, dict):
                    errors.append(
                        f"Function block at index {i} is not an object")
                    continue

                # Check different required fields depending on the fbv_id value
                if 'fbv_id' not in fb or fb['fbv_id'] is None:
                    # Required fields for a new function block
                    new_fb_required = ['current_plan', 'files']
                    for field in new_fb_required:
                        if field not in fb:
                            errors.append(
                                f"Missing field '{field}' in new function block {i}")
                    # Check that the run.sh file exists
                    if 'files' in fb:
                        if not isinstance(fb['files'], dict):
                            errors.append(
                                f"'files' in function block {i} is not an object")
                        else:
                            if 'run.sh' not in fb['files']:
                                errors.append(
                                    f"Missing 'run.sh' file in 'files' of function block {i}")
                            if "static-config.json" not in fb['files']:
                                errors.append(
                                    f"Missing 'static-config.json' file in 'files' of function block {i}")
                else:
                    # fbv_id must be numeric
                    if not re.match(r'^\d+$', str(fb['fbv_id'])):
                        errors.append(
                            f"Invalid 'fbv_id' format in function block {i}. Expected format: 'number'.")
                    if not find_fb_version_by_id(fb['fbv_id']):
                        errors.append(
                            f"Function block version {fb['fbv_id']} not found.")

        return len(errors) == 0, errors

    except Exception as e:
        return False, [f"Validation error: {str(e)}"]

def create_next_level_fbs_v2_with_plan(user_id, node: Node, generation_id, user_request, llm_model, max_branch_count, current_plan, generation_mode):
    """
    Create next level function blocks with plan for v2 nodes.
    This function only handles v2_node logic and uses simplified computation steps.
    All function blocks in v2 are new, so no need to check for existing FBs.

    Note: generation_mode and file_ids parameters are ignored for v2 nodes as they are not needed.
    """
    particular_fb_group = find_fb_group_by_owner_id_and_name(
        user_id, "__dynamic_fb_generated__"
    )
    if particular_fb_group is None:
        particular_fb_group = FunctionBlockGroup(
            name="__dynamic_fb_generated__",
            created_time=datetime.now(),
            serial_number=-100,
            alt_name="__dynamic_fb_generated__",
        )
        insert_fb_group(particular_fb_group)
        fb_group_user_relation = FunctionBlockGroupUserRelation(
            function_block_group_id=particular_fb_group.id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        insert_fb_group_user_relation(fb_group_user_relation)
    dynamic_generation_waiter = DynamicGenerationWaiter(generation_id)

    llm_interface = LlmInterface()
    server_agent = ServerAgent(user_id)

    # For v2 nodes, get simplified computation steps
    computation_steps_response = server_agent.get_former_computation_steps(node.id)
    computation_steps = computation_steps_response.get("data", [])
    finished_steps = "\n".join([f"Node {index}: {step['description']}" for index, step in enumerate(computation_steps, start=1)])
    existing_fbvs_v2_str = _get_existing_fbvs_v2(server_agent)
    # Get inputs structure for v2 nodes
    try:
        inputs_structure_response = server_agent.get_inputs_structure(node.id)
        inputs_structure = ServerAgent.format_inputs_structure_to_text(inputs_structure_response)
    except Exception as e:
        inputs_structure = "No inputs structure available"

    session_id = None
    max_retry = 10
    for i in range(max_retry):
        start_time = datetime.now()
        try:
            # Use v2 API for v2 nodes
            response = llm_interface.dynamic_fb_with_plan_v2(
                user_request,
                node.id,
                user_id,
                llm_model,
                max_branch_count,
                current_plan,
                finished_steps,
                inputs_structure,
                generation_mode,
                existing_fbvs_v2_str
            )
            end_time = datetime.now()
            if response is None or response.status_code != 200:
                raise Exception(
                    f"LLM interface returned an error: {response.status_code} - {response.text}"
                )
            pass_validation, validation_errors = validate_v2_output_json(response.text)
            if not pass_validation:
                errors = json.dumps(validation_errors, ensure_ascii=False, indent=4)
                raise Exception(
                    f"LLM output VALIDATION failed: {errors}"
                )
            break
        except Exception as e:
            end_time = datetime.now()
            logger.error(e)
            record_dynamic_generation_session(
                server_agent,
                generation_id,
                node.id,
                None,
                is_valid=False,
                errors=str(e),
                created_at=datetime.now(),
                type="generation",
                start_time=start_time,
                end_time=end_time
            )
            if i < max_retry - 1:
                logger.error(
                    f"Failed to get response from LLM interface for node {node.id}, retrying...")
                continue
            else:
                logger.error(
                    f"Failed to get response from LLM interface for node {node.id} after {max_retry} attempts")
                return []

    response_json = response.json()
    consumption = response_json.get("consumption", {}) or {}
    consumption_id = record_dynamic_generation_consumption(
        server_agent, consumption, node.id, generation_id)

    # Handle case where consumption recording failed
    if consumption_id is None:
        logger.warning(
            f"Failed to record consumption for node {node.id}, continuing with None consumption_id")

    # Record session without validation for v2
    session_id = record_dynamic_generation_session(
        server_agent,
        generation_id,
        node.id,
        consumption_id,
        is_valid=True,
        errors=None,
        created_at=datetime.now(),
        type="generation",
        start_time=start_time,
        end_time=end_time
    )

    logger.info(f"LLM response for v2 node {node.id}: {response_json}")

    result = response_json.get("data", {})
    satisfied = result.get("satisfied", False)
    prompt = result.get("prompt", "")
    if "prompt" in result:
        del result["prompt"]
    next_level_function_blocks = result.get("next_level_function_blocks", [])
    result_fb_list = []
    if satisfied:
        return result_fb_list

    # In v2, all function blocks are new
    for next_level_fb in next_level_function_blocks:
        if not next_level_fb.get("fbv_id", None) is None:
            fbv = find_fb_version_by_id(next_level_fb.get("fbv_id"))
            if not fbv:
                logger.error(f"FB version not found for fbv_id: {next_level_fb.get('fbv_id')}")
                continue
            fb = find_fb_by_id(fbv.function_block_id)
            result_fb_list.append({
                "fb_id": fbv.function_block_id if fbv else None,
                "fb_version_id": next_level_fb.get("fbv_id"),
                "fb_name": fb.name if fb else None,
                "fb_version_name": fbv.name if fbv else None,
                "parameters": next_level_fb.get("parameters", "{}"),
                "current_plan": next_level_fb.get("current_plan", None),
                "session_id": session_id
            })
        elif next_level_fb.get("files", None) is not None:
            create_fb_v2_result = _create_fb_v2(user_id, next_level_fb, particular_fb_group)
            create_fb_v2_result["session_id"] = session_id
            result_fb_list.append(create_fb_v2_result)
        else:
            logger.error(f"Next level FB missing both fbv_id and files: {next_level_fb}")
            continue

    dynamic_generation_waiter.save_log(
        session_id, prompt, json.dumps(result, indent=4))
    return result_fb_list


def create_next_level_fbs_with_plan(user_id, node: Node, generation_id, user_request, llm_model, max_branch_count, generation_mode, file_ids, current_plan):
    """
    Create next level function blocks with plan for v1 nodes.
    This function only handles v1 node logic and uses full computation history.
    """
    particular_fb_group = find_fb_group_by_owner_id_and_name(
        user_id, "__dynamic_fb_generated__"
    )
    if particular_fb_group is None:
        particular_fb_group = FunctionBlockGroup(
            name="__dynamic_fb_generated__",
            created_time=datetime.now(),
            serial_number=-100,
            alt_name="__dynamic_fb_generated__",
        )
        insert_fb_group(particular_fb_group)
        fb_group_user_relation = FunctionBlockGroupUserRelation(
            function_block_group_id=particular_fb_group.id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        insert_fb_group_user_relation(fb_group_user_relation)
    dynamic_generation_waiter = DynamicGenerationWaiter(generation_id)

    llm_interface = LlmInterface()
    server_agent = ServerAgent(user_id)

    # For v1 nodes, get full computation history
    computation_history = fetch_computation_history(user_id, node.id)

    session_id = None
    max_retry = 5
    for i in range(max_retry):
        start_time = datetime.now()
        try:
            # Use v1 API for v1 nodes
            response = llm_interface.dynamic_fb_with_plan(
                user_request,
                llm_model,
                node.id,
                computation_history,
                user_id,
                max_branch_count,
                generation_mode=generation_mode,
                file_ids=file_ids,
                current_plan=current_plan
            )
            end_time = datetime.now()
            if response is None or response.status_code != 200:
                raise Exception(
                    f"LLM interface returned an error: {response.status_code} - {response.text}"
                )

        except Exception as e:
            end_time = datetime.now()
            logger.error(e)
            record_dynamic_generation_session(
                server_agent,
                generation_id,
                node.id,
                None,
                is_valid=False,
                errors=str(e),
                created_at=datetime.now(),
                type="generation",
                start_time=start_time,
                end_time=end_time
            )
            if i < max_retry - 1:
                logger.error(
                    f"Failed to get response from LLM interface for node {node.id}, retrying...")
                continue
            else:
                logger.error(
                    f"Failed to get response from LLM interface for node {node.id} after {max_retry} attempts")
                return []
        response_json = response.json()
        consumption = response_json.get("consumption", {}) or {}
        consumption_id = record_dynamic_generation_consumption(
            server_agent, consumption, node.id, generation_id)

        # Handle case where consumption recording failed
        if consumption_id is None:
            logger.warning(
                f"Failed to record consumption for node {node.id}, continuing with None consumption_id")

        raw_response_text = response_json.get("message")
        logger.debug(
            f"handle_job_feedback - Raw response text: {raw_response_text}")
        is_valid, errors = validate_dynamic_generation_output_json(
            raw_response_text)
        session_id = record_dynamic_generation_session(
            server_agent,
            generation_id,
            node.id,
            consumption_id,
            is_valid=is_valid,
            errors=json.dumps(errors, ensure_ascii=False),
            created_at=datetime.now(),
            type="generation",
            start_time=start_time,
            end_time=end_time
        )
        if is_valid:
            break
        elif i < max_retry - 1:
            logger.error(
                f"Invalid dynamic generation output: {errors}, retrying...")
        else:
            logger.error(
                f"Invalid dynamic generation output after {max_retry} attempts: {errors}")
            return []
    result = response_json.get("data", {})
    satisfied = result.get("satisfied", False)
    prompt = result.get("prompt", "")
    if "prompt" in result:
        del result["prompt"]
    next_level_function_blocks = result.get("next_level_function_blocks", [])
    result_fb_list = []
    if satisfied:
        return result_fb_list
    for next_level_fb in next_level_function_blocks:
        current_plan = next_level_fb.get("current_plan", None)
        is_new_fb = next_level_fb.get("id", None) is None
        if not is_new_fb:
            id = next_level_fb.get("id", None)
            if id is not None and "-" in id:
                fb_id, fb_v_id = id.split("-", 1)
            else:
                fb_id = id
                fb_v_id = None
            next_level_fb["fb_id"] = fb_id
            next_level_fb["fb_version_id"] = fb_v_id
            fb = find_fb_by_id(fb_id)
            fb_v = find_fb_version_by_id(fb_v_id)
            result_fb_list.append({
                "fb_id": fb_id,
                "fb_version_id": fb_v_id,
                "fb_name": fb.name if fb else "unamed",
                "fb_version_name": fb_v.name if fb_v else "unamed",
                "parameters": next_level_fb.get("parameters", "{}"),
                "current_plan": current_plan,
                "session_id": session_id
            })
        else:
            programming_language = next_level_fb.get(
                "programming_language", "Python")
            name = next_level_fb.get("name", "unamed")
            code_code = next_level_fb.get("function_block_code", "")
            parameters = next_level_fb.get("parameters", "{}")
            preset_env = next_level_fb.get("preset_env", None)
            static_config = next_level_fb.get(
                "static_config_file_content", {})
            static_config = fill_default_for_static_config(static_config)
            requirements_content = next_level_fb.get(
                "requirements_file_content", "")
            args = static_config.get("args", [])
            tag = static_config.get("tag", "")
            document_url = static_config.get("document_url", "")
            description = static_config.get("description", "")
            source = static_config.get("source", "")
            preset_env = static_config.get("preset_env", None)
            new_fb = FunctionBlockV1(
                name=name,
                group_id=particular_fb_group.id,
                current_version_id=None,
                created_time=datetime.now(),
                type="computation",
                occasion="flow",
                alt_name=name,
            )
            insert_fb(new_fb)
            new_fb_user_relation = FunctionBlockUserRelation(
                user_id=user_id,
                function_block_id=new_fb.id,
                relation=Relation.BELONG_TO.value,
                permission=Permission.ADMIN.value
            )
            insert_fb_user_relation(new_fb_user_relation)
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
                program_language=programming_language,
                error_message=None,
                preset_env=preset_env
            )
            insert_fb_version(new_fb_version)
            update_fb(new_fb.id, {"current_version_id": new_fb_version.id})
            next_level_fb["fb_id"] = new_fb.id
            next_level_fb["fb_version_id"] = new_fb_version.id
            fb_waiter = FunctionBlockV1Waiter(
                new_fb_version.id, new_fb_version.program_language)
            fb_waiter.rewrite_core_code(code_code)
            fb_waiter.rewrite_static_config(static_config)
            fb_waiter.rewrite_requirement_file(requirements_content)
            result_fb_list.append({
                "fb_id": new_fb.id,
                "fb_version_id": new_fb_version.id,
                "fb_name": name,
                "fb_version_name": name,
                "parameters": parameters,
                "current_plan": current_plan,
                "session_id": session_id
            })

        dynamic_generation_waiter.save_log(
            session_id, prompt, json.dumps(result, indent=4))
    return result_fb_list


def get_retry_process_history_details(retry_process_id):
    fixer_computation_list = find_computation_by_retry_process_id(
        retry_process_id)
    fixer_history_details = []
    retry_process_waiter = RetryProcessWaiter(retry_process_id)
    for computation in fixer_computation_list:
        node_computation_information, input_prompt, parameters_fix_solution, code_fix_solution, result = retry_process_waiter.get_one_stage_details(
            computation.id)
        fixer_history_details.append({
            "computation": computation,
            "node_computation_information": node_computation_information,
            "input_prompt": input_prompt,
            "parameters_fix_solution": parameters_fix_solution,
            "code_fix_solution": code_fix_solution,
            "result": result
        })


def get_retry_process_history_details_str(retry_process_id):
    fixer_computation_list = find_computation_by_retry_process_id(
        retry_process_id)
    fixer_history_details_str = ""
    retry_process_waiter = RetryProcessWaiter(retry_process_id)
    # for computation_index in range(len(fixer_computation_list)):
    #     computation = fixer_computation_list[computation_index]
    #     fixer_history_details_str += f"########################### No. {computation_index + 1} Start ###########################\n"
    #     node_computation_information, input_prompt, parameters_fix_solution, code_fix_solution, result = retry_process_waiter.get_one_stage_details(
    #         computation.id)
    #     fixer_history_details_str += f"Computation: {computation}\n"
    #     fixer_history_details_str += f"Node Computation Information: {node_computation_information}\n"
    #     fixer_history_details_str += f"Input Prompt: {input_prompt}\n"
    #     fixer_history_details_str += f"Parameters Fix Solution: {parameters_fix_solution}\n"
    #     fixer_history_details_str += f"Code Fix Solution: {code_fix_solution}\n"
    #     fixer_history_details_str += f"Result: {result}\n"
    #     fixer_history_details_str += f"########################### No. {computation_index + 1} End ###########################\n\n"
    # return fixer_history_details_str
    if len(fixer_computation_list) == 0:
        return fixer_history_details_str
    computation = fixer_computation_list[-1]
    node_computation_information, input_prompt, parameters_fix_solution, code_fix_solution, result = retry_process_waiter.get_one_stage_details(
        computation.id)
    fixer_history_details_str += f"Computation: {computation}\n"
    fixer_history_details_str += f"Node Computation Information: {node_computation_information}\n"
    # fixer_history_details_str += f"Input Prompt: {input_prompt}\n"
    fixer_history_details_str += f"Parameters Fix Solution: {parameters_fix_solution}\n"
    fixer_history_details_str += f"Code Fix Solution: {code_fix_solution}\n"
    fixer_history_details_str += f"Result: {result}\n"
    return fixer_history_details_str


def _build_node_context(node_id):
    context = ""

    # Build previous node context
    previous_node = find_previous_node_by_node_id(node_id)
    if previous_node:
        context += "=== Previous Node Context ===\n"
        context += f"Node ID: {previous_node.id}\n"
        context += f"Name: {previous_node.name}\n"
        context += f"Type: {previous_node.type}\n"
        context += f"State: {previous_node.state}\n"

        if previous_node.computation_params:
            context += f"Computation Parameters: {previous_node.computation_params}\n"

        if previous_node.data_id:
            context += f"Data ID: {previous_node.data_id}\n"
            try:
                data = find_data_by_id(previous_node.data_id)
                if data and hasattr(data, 'stats'):
                    stats = data.stats or {}
                    context += "Dataset Statistics:\n"
                    context += f"  Sparsity: {stats.get('sparsity', 'N/A')}\n"
                    context += f"  Observations: {stats.get('obs', 'N/A')}\n"
                    context += f"  Observation metadata: {stats.get('obsm', 'N/A')}\n"
                    context += f"  Variables: {stats.get('var', 'N/A')}\n"
                    context += f"  Unstructured: {stats.get('uns', 'N/A')}\n"
                    context += f"  Layers: {stats.get('layers', 'N/A')}\n"
            except Exception:
                pass
        context += "\n"

 # Build latest computation context
    latest_computation = find_latest_computation_by_node_id(node_id)
    if latest_computation:
        context += f"Latest Computation State: {latest_computation.computation_state}\n"
        if latest_computation.computation_params:
            context += f"Computation Parameters: {latest_computation.computation_params}\n"

    return context


def handle_parent_node_replan(user_id, node_id, parent_node: Node, dynamic_generation: DynamicGeneration):
    user_request = dynamic_generation.user_request
    model = dynamic_generation.llm_model
    parent_node_context = _build_node_context(parent_node.id)
    dynamic_generation_waiter = DynamicGenerationWaiter(
        dynamic_generation.generation_id)
    parent_node_latest_plan = dynamic_generation_waiter.retrieve_plan(
        parent_node.id)
    failed_node_latest_computation = find_latest_computation_by_node_id(
        node_id)
    if failed_node_latest_computation is not None:
        error_description = failed_node_latest_computation.error_description

    llm_interface = LlmInterface()

    refer_files = dynamic_generation_waiter.get_files()

    max_retry = 10
    for i in range(max_retry):
        try:
            plan_result = llm_interface.dynamic_fb_replan(
                user_id,
                parent_node.id,
                user_request,
                parent_node_context,
                error_description,
                parent_node_latest_plan,
                llm_model=model,
                file_list=refer_files
            )
            logger.debug(
                f"handle_job_feedback - Plan result: {plan_result}")
            if plan_result is None or plan_result.status_code != 200:
                raise Exception(
                    f"LLM interface returned an error: {plan_result.status_code} - {plan_result.text}"
                )

        except Exception as e:
            logger.error(e)
            session = DynamicGenerationSession(
                dynamic_generation_id=dynamic_generation.generation_id,
                source_node_id=parent_node.id,
                consumption_id=None,
                is_valid=False,
                errors=str(e),
                created_at=datetime.now(),
                type="plan"
            )
            insert_session(session)
            if i < max_retry - 1:
                logger.error(
                    f"Failed to get response from LLM interface for node {parent_node.id}, retrying...")
                continue
            else:
                logger.error(
                    f"Failed to get response from LLM interface for node {parent_node.id} after {max_retry} attempts")
                return []
        response_json = plan_result.json()
        consumption = response_json.get("consumption", {}) or {}
        consumption["user_id"] = user_id
        consumption["node_id"] = parent_node.id
        consumption["functionality"] = "Auto Genie"
        consumption["functionality_task_id"] = dynamic_generation.generation_id
        consumption["created_at"] = datetime.now()
        consumption["model"] = dynamic_generation.llm_model
        consump = LLMConsumption(**consumption)
        consump = insert_consumption(consump)
        raw_response_text = response_json.get("message")
        is_valid, errors = validate_dynamic_generation_plan_output_json(
            raw_response_text)
        session = DynamicGenerationSession(
            dynamic_generation_id=dynamic_generation.generation_id,
            source_node_id=parent_node.id,
            consumption_id=consump.id,
            is_valid=is_valid,
            errors=json.dumps(errors, ensure_ascii=False),
            created_at=datetime.now(),
            type="plan"
        )
        insert_session(session)
        if is_valid:
            break
        elif i < max_retry - 1:
            logger.error(
                f"Invalid dynamic generation output: {errors}, retrying...")
        else:
            logger.error(
                f"Failed to get valid dynamic generation output for node {parent_node.id} after {max_retry} attempts")
            return []

    result_data = None
    if "data" in response_json and isinstance(response_json["data"], dict):
        result_data = response_json["data"]
    elif "message" in response_json:
        try:
            result_data = json.loads(response_json["message"])
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse result from message field: {e}")
            result_data = {}
    else:
        result_data = {}

    return result_data


def validate_dynamic_generation_output_json(json_data_text):
    """
    Quickly check that the key fields of the structured_output JSON returned by GPT are present

    Args:
        json_data: parsed JSON data
        generation_mode: generation mode, used to determine which model to validate against

    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    try:
        json_data = json.loads(json_data_text)
    except Exception as e:
        return False, [f"Invalid JSON format: {str(e)}, JSON: {json_data_text}"]
    errors = []

    # Fields that do not require strict checking
    skip_fields = {'url_citations', 'reasoning'}

    try:
        # Check required top-level fields
        top_level_required = ['satisfied', 'next_level_function_blocks']
        for field in top_level_required:
            if field not in json_data:
                errors.append(f"Missing top-level required field '{field}'")

        # Check the next_level_function_blocks array
        if 'next_level_function_blocks' in json_data and isinstance(json_data['next_level_function_blocks'], list):
            for i, fb in enumerate(json_data['next_level_function_blocks']):
                if not isinstance(fb, dict):
                    errors.append(
                        f"Function block at index {i} is not an object")
                    continue

                # Check different required fields depending on the 'new' field value
                if 'id' not in fb or fb['id'] is None:
                    # Required fields for a new function block
                    new_fb_required = ['programming_language', 'function_block_code',
                                       'requirements_file_content', 'static_config_file_content']
                    for field in new_fb_required:
                        if field not in fb:
                            errors.append(
                                f"Missing field '{field}' in new function block {i}")

                    # Check required fields of static_config_file_content
                    if 'static_config_file_content' in fb:
                        if not isinstance(fb['static_config_file_content'], dict):
                            errors.append(
                                f"static_config_file_content of function block {i} is not an object")
                        else:
                            static_config = fb['static_config_file_content']
                            static_required = ['args']
                            for field in static_required:
                                if field not in static_config:
                                    errors.append(
                                        f"Missing field '{field}' in static_config of function block {i}")

                            # Check the basic structure of the args array
                            if 'args' in static_config and isinstance(static_config['args'], list):
                                for j, arg in enumerate(static_config['args']):
                                    if isinstance(arg, dict):
                                        arg_required = ['render_type']
                                        for field in arg_required:
                                            if field not in arg:
                                                errors.append(
                                                    f"Missing field '{field}' in arg {j} of function block {i}")
                    if "requirements_file_content" in fb:
                        if not isinstance(fb["requirements_file_content"], str):
                            errors.append(
                                f"'requirements_file_content' must be a string in function block {i}")
                else:
                    # id must be in `number-number` format
                    if not re.match(r'^\d+-\d+$', fb['id']):
                        errors.append(
                            f"Invalid 'id' format in function block {i}. Expected format: 'number-number'.")

        return len(errors) == 0, errors

    except Exception as e:
        return False, [f"Validation error: {str(e)}"]


def validate_dynamic_generation_plan_output_json(json_data_text):
    """
    Parse-level check of the LLM plan response.

    NOTE: this only verifies that the response is a JSON object; it does not
    validate the plan schema. `is_valid` recorded in session logs therefore
    means "parseable JSON object", not "schema-valid plan".

    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    try:
        json_data = json.loads(json_data_text)
    except Exception as e:
        return False, [f"JSON decode error: {str(e)} - {json_data_text}"]

    if not isinstance(json_data, dict):
        return False, ["Plan response is not a JSON object"]
    return True, []


def validate_fixer_output_json(json_data_text, response_type):
    """
    Quickly check that the key fields of the structured_output JSON returned by FixerAI are present

    Args:
        json_data: parsed JSON data
        response_type: response type, 'parameter' or 'code'

    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    try:
        json_data = json.loads(json_data_text)
    except Exception as e:
        return False, [f"Invalid JSON format: {str(e)}, JSON: {json_data_text}"]
    errors = []

    # Fields that do not need checking
    skip_fields = {'url_citations', 'reasoning'}

    try:
        if response_type == 'parameter':
            # Required fields of ParameterFixerResponse
            required_fields = ['data']
            for field in required_fields:
                if field not in skip_fields and field not in json_data:
                    errors.append(
                        f"Missing required field '{field}' in ParameterFixerResponse")

        elif response_type == 'code':
            # Required fields of CodeFixerResponse
            required_fields = ['programming_language',
                               'code', 'static_config', 'parameters']
            for field in required_fields:
                if field not in skip_fields and field not in json_data:
                    errors.append(
                        f"Missing required field '{field}' in CodeFixerResponse")

            # Check required fields of static_config
            if 'static_config' in json_data and isinstance(json_data['static_config'], dict):
                static_config = json_data['static_config']
                static_required = ['args']
                for field in static_required:
                    if field not in static_config:
                        errors.append(
                            f"Missing field '{field}' in static_config")

                # Check the basic structure of the args array
                if 'args' in static_config and isinstance(static_config['args'], list):
                    for i, arg in enumerate(static_config['args']):
                        if isinstance(arg, dict):
                            arg_required = ['render_type']
                            for field in arg_required:
                                if field not in arg:
                                    errors.append(
                                        f"Missing field '{field}' in arg {i} of static_config")

            # Check that requirements is a string
            if 'requirements' in json_data:
                if not isinstance(json_data['requirements'], str):
                    errors.append(
                        "Field 'requirements' must be a string in CodeFixerResponse")
            # Check that parameters is a dict or a string
            if 'parameters' in json_data:
                if not isinstance(json_data['parameters'], dict) and not isinstance(json_data['parameters'], str):
                    errors.append(
                        "Field 'parameters' must be a dictionary in CodeFixerResponse")
        return len(errors) == 0, errors

    except Exception as e:
        return False, [f"Validation error: {str(e)}"]


def fill_default_for_static_config(static_config: dict):
    """
    Fill default values into the static config to ensure completeness and consistency

    Args:
        static_config (dict): static config dictionary
    """
    # Fill defaults for top-level fields
    static_config.setdefault('description', 'No description provided')
    static_config.setdefault('tag', 'No-tag')
    static_config.setdefault('document_url', '#')
    static_config.setdefault('source', '.')
    static_config.setdefault('preset_env', None)
    static_config.setdefault('args', [])
    static_config.setdefault('name', 'Unnamed Function Block')

    # Process the args array
    if 'args' in static_config and isinstance(static_config['args'], list):
        for i, arg in enumerate(static_config['args']):
            if not isinstance(arg, dict):
                continue

            # Fill defaults for each arg
            arg.setdefault('name', f'arg_{i}')
            arg.setdefault('value_type', 'str')
            arg.setdefault('description', '')
            arg.setdefault('optional', False)
            arg.setdefault('default_value', None)
            arg.setdefault('render_type', 'str-input')
            arg.setdefault('options', [])

    return static_config

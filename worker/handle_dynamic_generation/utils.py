from datetime import datetime
from db import insert_fb, insert_fb_version, insert_fb_group, insert_fb_user_relation, insert_fb_group_user_relation, find_fb_group_by_owner_id_and_name, update_fb, find_fb_version_by_id, find_fb_by_id
from db import FunctionBlockGroup, FunctionBlockV1, FunctionBlockUserRelation, FunctionBlockGroupUserRelation, FunctionBlockVersionV1, Node
from constants import Relation, Permission, GenerationMode
from server_agent import ServerAgent
from waiter.function_block_v1_waiter import FunctionBlockV1Waiter
from llm_interface import LlmInterface
import json
import re
from waiter.dynamic_generation_waiter import DynamicGenerationWaiter
from logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("DynamicGeneration")


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


def create_next_level_fbs(user_id, node: Node, dynamic_generation_id, user_request, llm_model, max_branch_count=2, generation_mode=GenerationMode.MIXED.value, file_ids=None):
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
    llm_interface = LlmInterface()
    server_agent = ServerAgent(user_id)
    computation_history_response = server_agent.get_computation_history(
        node.id)
    computation_history = computation_history_response["data"]
    session_id = None
    max_retry = 5
    for i in range(max_retry):
        start_time = datetime.now()
        try:
            response = llm_interface.dynamic_fb(
                user_request,
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
                dynamic_generation_id,
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
            server_agent, consumption, node.id, dynamic_generation_id)
        raw_response_text = response_json.get("message")
        is_valid, errors = validate_dynamic_generation_output_json(
            raw_response_text)
        session_id = record_dynamic_generation_session(
            server_agent,
            dynamic_generation_id,
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
            fb = find_fb_by_id(fb_id)
            fb_v = find_fb_version_by_id(fb_v_id)
            next_level_fb["fb_id"] = fb_id
            next_level_fb["fb_version_id"] = fb_v_id
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
        dynamic_generation_waiter = DynamicGenerationWaiter(
            dynamic_generation_id)
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
        is_v2=True
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
        json_data: the parsed JSON data

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

def create_next_level_fbs_v2_with_plan(user_id, node: Node, dynamic_generation_id, user_request, llm_model, max_branch_count, current_plan, generation_mode=GenerationMode.ONLY_NEW.value):
    """
    Create next level function blocks with plan for v2 nodes.
    This function only handles v2_node logic and uses simplified computation steps.
    All function blocks in v2 are new, so no need to check for existing FBs.

    Note: generation_mode and file_ids parameters are not needed for v2 nodes.
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
    llm_interface = LlmInterface()
    server_agent = ServerAgent(user_id)

    # For v2 nodes, get simplified computation steps
    computation_steps_response = server_agent.get_former_computation_steps(node.id)
    computation_steps = computation_steps_response.get("data", [])
    finished_steps = "\n".join([f"Node {index}: {step['description']}" for index, step in enumerate(computation_steps, start=1)])
    existing_fbvs_str = _get_existing_fbvs_v2(server_agent)

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
            logger.debug(
                f"handle_dynamic_generation - Requesting LLM for node {node.id} model {llm_model} with plan: {current_plan}")

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
                existing_fbvs_str
            )
            logger.debug(f"LLM response for v2 node {node.id}: {response.text if response is not None else None}")
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
                dynamic_generation_id,
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
        server_agent, consumption, node.id, dynamic_generation_id)

    # Record session without validation for v2
    session_id = record_dynamic_generation_session(
        server_agent,
        dynamic_generation_id,
        node.id,
        consumption_id,
        is_valid=True,
        errors=None,
        created_at=datetime.now(),
        type="generation",
        start_time=start_time,
        end_time=end_time
    )

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
    dynamic_generation_waiter = DynamicGenerationWaiter(
        dynamic_generation_id)
    dynamic_generation_waiter.save_log(
        session_id, prompt, json.dumps(result, indent=4))
    return result_fb_list


def create_next_level_fbs_with_plan(user_id, node: Node, dynamic_generation_id, user_request, llm_model, max_branch_count=2, generation_mode=GenerationMode.MIXED.value, file_ids=None, current_plan=None):
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
    llm_interface = LlmInterface()
    server_agent = ServerAgent(user_id)

    # For v1 nodes, get full computation history
    computation_history_response = server_agent.get_computation_history(node.id)
    computation_history = computation_history_response["data"]

    session_id = None
    max_retry = 5
    for i in range(max_retry):
        start_time = datetime.now()
        try:
            logger.debug(
                f"handle_dynamic_generation - Requesting LLM for node {node.id} model {llm_model} with plan: {current_plan}")

            # Use v1 API for v1 nodes
            response = llm_interface.dynamic_fb_with_plan(
                user_request,
                llm_model,
                node.id,
                computation_history,
                user_id,
                max_branch_count,
                generation_mode,
                file_ids,
                current_plan,
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
                dynamic_generation_id,
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
            server_agent, consumption, node.id, dynamic_generation_id)
        raw_response_text = response_json.get("message")
        logger.debug(
            f"handle_dynamic_generation - Raw response text: {raw_response_text}")
        is_valid, errors = validate_dynamic_generation_output_json(
            raw_response_text)
        session_id = record_dynamic_generation_session(
            server_agent,
            dynamic_generation_id,
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
    response_json = response.json()
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
            if not id or "-" not in id:
                logger.error(f"Invalid id format for function block: {id}")
                continue
            fb_id, fb_v_id = id.split("-", 1)
            fb = find_fb_by_id(fb_id)
            fb_v = find_fb_version_by_id(fb_v_id)
            next_level_fb["fb_id"] = fb_id
            next_level_fb["fb_version_id"] = fb_v_id
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
        dynamic_generation_waiter = DynamicGenerationWaiter(
            dynamic_generation_id)
        dynamic_generation_waiter.save_log(
            session_id, prompt, json.dumps(result, indent=4))
    return result_fb_list


def validate_dynamic_generation_output_json(json_data_text):
    """
    Quickly check that the key fields of the structured_output JSON returned by GPT are present

    Args:
        json_data: the parsed JSON data

    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    try:
        json_data = json.loads(json_data_text)
    except Exception as e:
        return False, [f"JSON decode error: {str(e)} - {json_data_text}"]

    errors = []

    # Fields that do not need strict checking
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

                # Check different required fields depending on whether the block is new
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
                                f"static_config_file_content in function block {i} is not an object")
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

                    # Check that requirements is a string
                    if 'requirements_file_content' in fb:
                        if not isinstance(fb['requirements_file_content'], str):
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

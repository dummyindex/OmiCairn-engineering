from typing import Dict
from dao.dynamic_generation import dynamic_generation_dao
from dao.llm import llm_dao
from model.llm_consumption import LLMConsumption
from tool.common_validator import CommonValidator
from tool.conn_to_main_server import report_chat_tool_callback,query_chat_sub_task, login_main_server
from model.dynamic_generation import DynamicGeneration
from model.dynamic_generation_branch import DynamicGenerationBranch
from model.node import Node
from datetime import datetime
from constants.dynamic_generation import DynamicGenerationState, PlanStatus
from dao.node import node_dao
from dao.edge import edge_dao
from dao.figure import figure_dao
from dao.computation import computation_dao
from dao.analysis import analysis_dao
from db import alchemy_db as db
from model.dynamic_generation_session import DynamicGenerationSession
from sss.porter_factory import PorterFactory
from waiter.dynamic_generation_waiter import DynamicGenerationWaiter
import os
from tool.llm_interface import LlmInterface
from log.logger_factory import LoggerFactory
import json
from tool.common_converter import convert_model_to_dict
from tool.computation_launcher import ComputationLauncher
from authority.guardian_factory import AuthorityGuardianFactory
from constants.authority import AuthorityCarrier
from tool.performance_timer import timer_stage, log_timings
logger = LoggerFactory.get_logger("DynamicGenerationService")


class DynamicGenerationService:

    def _build_node_context(self, previous_node_id, computation):
        context = ""

        # Build previous node context
        previous_node = node_dao.find_by_id(previous_node_id)
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
                    from dao.data import data_dao
                    data = data_dao.find_by_id(previous_node.data_id)
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
        if computation:
            context += f"Latest Computation State: {computation.computation_state}\n"
            if computation.computation_params:
                context += f"Computation Parameters: {computation.computation_params}\n"
            if computation.error_description:
                context += f"Latest Error: {computation.error_description}\n"
            if computation.duration:
                context += f"Execution Duration: {computation.duration}s\n"
            context += "\n"

        return context

    def generate_initial_plan(self, user_id, previous_node_id, max_node, max_branch, user_request,
                              computation_resource_configure, generation_mode, max_debug, llm_model, version, replan_count_limit, file_list, claude_execution_model=None, claude_max_iterations=100):
        timings = {}

        with timer_stage("W3_db_record_creation", timings):
            now = datetime.now()

            node = node_dao.find_by_id(previous_node_id)
            if not node:
                raise Exception("Node not found")

            latest_computation = computation_dao.find_latest_by_node_id(
                previous_node_id)

            dynamic_generation = DynamicGeneration(
                analysis_id=node.analysis_id,
                previous_node_id=previous_node_id,
                previous_computation_id=latest_computation.id if latest_computation else None,
                max_node=max_node,
                rest_node_count=max_node,
                max_branch=max_branch,
                user_request=user_request,
                created_time=now,
                state=None,
                computation_resource_configure=computation_resource_configure,
                generation_mode=generation_mode,
                max_debug=max_debug,
                llm_model=llm_model,
                version=version,
                replan_count_limit=replan_count_limit,
                claude_execution_model=claude_execution_model,
                claude_max_iterations=claude_max_iterations
            )
            dynamic_generation_dao.insert(dynamic_generation)

            waiter = DynamicGenerationWaiter(dynamic_generation.generation_id)
            waiter.catch_files(file_list)
            llm_interface = LlmInterface()

        with timer_stage("W4_context_building", timings):
            node_context = self._build_node_context(
                previous_node_id, latest_computation)
            if not node_context:
                node_context = "No context available for this node."

        with timer_stage("W5_llm_interface_call", timings):
            refer_files = waiter.get_files()
            max_retry = 10
            plan_json = None
            for i in range(max_retry):
                try:
                    plan_result = llm_interface.generate_initial_plan(
                        user_id=user_id,
                        node_id=previous_node_id,
                        user_request=user_request,
                        llm_model=llm_model,
                        node_context=node_context,
                        max_node=max_node,
                        max_branch=max_branch,
                        file_list=refer_files
                    )
                    if plan_result is None or plan_result.status_code != 200:
                        raise Exception(
                            f"LLM interface returned an error: {plan_result.status_code} - {plan_result.text}"
                        )
                except Exception as e:
                    logger.error(e)
                    dynamic_generation_dao.insert_session(
                        DynamicGenerationSession(
                            dynamic_generation_id=dynamic_generation.generation_id,
                            source_node_id=previous_node_id,
                            consumption_id=None,
                            is_valid=False,
                            errors=str(e),
                            created_at=datetime.now(),
                            type="plan",
                        )
                    )
                    if i < max_retry - 1:
                        logger.error(
                            f"Failed to get response from LLM interface for node {node.id}, retrying...")
                        continue
                    else:
                        logger.error(
                            f"Failed to get response from LLM interface for node {node.id} after {max_retry} attempts")
                        log_timings("generate_initial_plan_service", timings)
                        return []
                plan_json = plan_result.json()
                consumption = plan_json.get("consumption", {}) or {}
                consumption["user_id"] = user_id
                consumption["node_id"] = previous_node_id
                consumption["functionality"] = "Auto Genie"
                consumption["functionality_task_id"] = dynamic_generation.generation_id
                consumption["created_at"] = datetime.now()
                consumption["model"] = llm_model
                consump = LLMConsumption(**consumption)
                consump = llm_dao.insert_consumption(consump)
                raw_response_text = plan_json.get("message")
                is_valid, errors = CommonValidator.validate_dynamic_generation_plan_output_json(
                    raw_response_text)
                dynamic_generation_dao.insert_session(
                    DynamicGenerationSession(
                        dynamic_generation_id=dynamic_generation.generation_id,
                        source_node_id=previous_node_id,
                        consumption_id=consump.id,
                        is_valid=is_valid,
                        errors=json.dumps(errors, ensure_ascii=False),
                        created_at=datetime.now(),
                        type="plan",
                    )
                )
                if is_valid:
                    break
                elif i < max_retry - 1:
                    logger.error(
                        f"Invalid dynamic generation output: {errors}, retrying...")
                else:
                    logger.error(
                        f"Invalid dynamic generation output after {max_retry} attempts: {errors}")
                    log_timings("generate_initial_plan_service", timings)
                    return []

        with timer_stage("W6_plan_storage", timings):
            plan_data = None
            if "data" in plan_json and isinstance(plan_json["data"], dict):
                plan_data = plan_json["data"]
            elif "message" in plan_json:
                try:
                    plan_data = json.loads(plan_json["message"])
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Failed to parse plan from message field: {e}")
                    plan_data = {}
            else:
                plan_data = {}

            generated_plan = {
                "name": plan_data.get("name", "Untitled Plan"),
                "steps": plan_data.get("steps", "")
            }
            waiter.store_plan(previous_node_id, generated_plan)
            dynamic_generation_dao.update(dynamic_generation.generation_id, {
                "plan_name": generated_plan.get('name', 'Untitled Plan'),
                "plan_status": PlanStatus.GENERATED.value,
            })

        log_timings("generate_initial_plan_service", timings)

        return {
            "generation_id": dynamic_generation.generation_id,
            "node_id": previous_node_id,
            "plan": generated_plan,
            "_service_timing": timings,
        }

    def get_plan(self, previous_node_id, generation_id):
        try:
            waiter = DynamicGenerationWaiter(generation_id)
            plan_url = waiter.retrieve_plan_url(previous_node_id)
            return plan_url
        except Exception as e:
            logger.error(
                f"Failed to get plan for generation {generation_id}: {e}")
            return None

    def update_plan(self, previous_node_id, generation_id, attrs: dict):
        try:
            waiter = DynamicGenerationWaiter(generation_id)
            current_plan = waiter.retrieve_plan(previous_node_id)

            for key, value in attrs.items():
                current_plan[key] = value

            waiter.store_plan(previous_node_id, current_plan)
            return current_plan

        except Exception as e:
            logger.error(
                f"Failed to update plan for generation {generation_id}: {e}")
            return None
        
    def store_plan(self, previous_node_id, generation_id, plan_data):
        try:
            waiter = DynamicGenerationWaiter(generation_id)
            waiter.store_plan(previous_node_id, plan_data)
            return plan_data
        except Exception as e:
            logger.error(
                f"Failed to store plan for generation {generation_id}: {e}")
            return None

    def delete_plan(self, generation_id, previous_node_id):
        """Delete a generated or generation_failed plan and its associated S3 files"""
        dynamic_generation = dynamic_generation_dao.find_by_id(generation_id)
        if not dynamic_generation:
            return {"error": "Plan not found", "code": 404}

        if dynamic_generation.plan_status not in [
            PlanStatus.GENERATED.value,
            PlanStatus.GENERATION_FAILED.value
        ]:
            return {"error": "Only plans with status 'generated' or 'generation_failed' can be deleted", "code": 400}

        # Delete S3 plan file
        try:
            waiter = DynamicGenerationWaiter(generation_id)
            waiter.delete_plan(previous_node_id)
        except Exception as e:
            logger.warning(f"Failed to delete S3 plan file for generation {generation_id}: {e}")

        # Delete database record
        try:
            dynamic_generation_dao.delete(generation_id)
            return {"success": True, "message": "Plan deleted successfully"}
        except Exception as e:
            logger.error(f"Failed to delete plan {generation_id}: {e}")
            return {"error": str(e), "code": 500}

    def create_custom_plan(self, user_id, previous_node_id, max_node, max_branch,
                           user_request, computation_resource_configure, generation_mode,
                           max_debug, llm_model, version, replan_count_limit,
                           plan_name, plan_steps,
                           claude_execution_model=None, claude_max_iterations=100):
        """Create a custom plan without LLM generation."""
        now = datetime.now()

        node = node_dao.find_by_id(previous_node_id)
        if not node:
            raise Exception("Node not found")

        latest_computation = computation_dao.find_latest_by_node_id(previous_node_id)

        dynamic_generation = DynamicGeneration(
            analysis_id=node.analysis_id,
            previous_node_id=previous_node_id,
            previous_computation_id=latest_computation.id if latest_computation else None,
            max_node=max_node,
            rest_node_count=max_node,
            max_branch=max_branch,
            user_request=user_request,
            created_time=now,
            state=None,
            computation_resource_configure=computation_resource_configure,
            generation_mode=generation_mode,
            max_debug=max_debug,
            llm_model=llm_model,
            version=version,
            replan_count_limit=replan_count_limit,
            plan_name=plan_name,
            plan_status=PlanStatus.GENERATED.value,
            claude_execution_model=claude_execution_model,
            claude_max_iterations=claude_max_iterations,
        )
        dynamic_generation_dao.insert(dynamic_generation)

        # Store the plan
        waiter = DynamicGenerationWaiter(dynamic_generation.generation_id)
        plan_data = {
            "name": plan_name,
            "steps": plan_steps
        }
        waiter.store_plan(previous_node_id, plan_data)

        logger.info(f"Custom plan created: generation_id={dynamic_generation.generation_id}, "
                    f"node_id={previous_node_id}, plan_name={plan_name}")

        return {
            "generation_id": dynamic_generation.generation_id,
            "node_id": previous_node_id,
            "plan": plan_data,
        }

    def list_plans_by_analysis_id(self, analysis_id):
        try:
            dynamic_generations = dynamic_generation_dao.find_by_analysis_id(
                analysis_id)

            result = []
            for dynamic_generation in dynamic_generations:
                if dynamic_generation.plan_name or dynamic_generation.plan_status:
                    plan_summary = {
                        'generation_id': dynamic_generation.generation_id,
                        'node_id': dynamic_generation.previous_node_id,
                        'name': dynamic_generation.plan_name or 'Untitled Plan',
                        'status': dynamic_generation.plan_status or 'unknown',
                        'created_time': dynamic_generation.created_time.timestamp() * 1000 if dynamic_generation.created_time else None,
                        "plan_status_message": dynamic_generation.plan_status_message or '',
                        'generation_mode': dynamic_generation.generation_mode,
                    }

                    result.append(plan_summary)

            result.sort(key=lambda x: x.get('created_time', 0), reverse=True)
            return result

        except Exception as e:
            logger.error(
                f"Failed to list plans for analysis_id {analysis_id}: {e}")
            return []

    def create(self, previous_node_id, max_node, max_branch, user_request, computation_resource_configure, generation_mode, max_debug, llm_model, version, replan_count_limit):
        now = datetime.now()
        node = node_dao.find_by_id(previous_node_id)
        if not node:
            raise Exception("Node not found")
        latest_computation = computation_dao.find_latest_by_node_id(
            previous_node_id)
        dynamic_generation = DynamicGeneration(
            analysis_id=node.analysis_id,
            previous_node_id=previous_node_id,
            previous_computation_id=latest_computation.id if latest_computation else None,
            max_node=max_node,
            rest_node_count=max_node,
            max_branch=max_branch,
            user_request=user_request,
            created_time=now,
            state=DynamicGenerationState.READY.value,
            computation_resource_configure=computation_resource_configure,
            generation_mode=generation_mode,
            max_debug=max_debug,
            llm_model=llm_model,
            version=version,
            replan_count_limit=replan_count_limit
        )
        dynamic_generation_dao.insert(dynamic_generation)
        first_branch = DynamicGenerationBranch(
            dynamic_generation_id=dynamic_generation.generation_id,
            end_node_id=dynamic_generation.previous_node_id,
            state="running",
            created_time=now,
            updated_time=now
        )
        dynamic_generation_dao.insert_branch(first_branch)
        dynamic_generation_dao.update(dynamic_generation.generation_id, {
            "state": DynamicGenerationState.RUNNING.value
        })
        return dynamic_generation, first_branch

    def create_with_plan(self, dynamic_generation_id, previous_node_id):
        now = datetime.now()
        dynamic_generation_dao.update(dynamic_generation_id, {
            "state": DynamicGenerationState.READY.value,
        })
        first_branch = DynamicGenerationBranch(
            dynamic_generation_id=dynamic_generation_id,
            end_node_id=previous_node_id,
            state="running",
            created_time=now,
            updated_time=now
        )
        dynamic_generation_dao.insert_branch(first_branch)
        dynamic_generation_dao.update(dynamic_generation_id, {
            "state": DynamicGenerationState.RUNNING.value,
            # reset rest_node_count to handle repeated generation under the same plan
            "rest_node_count": dynamic_generation_dao.find_by_id(dynamic_generation_id).max_node
        })

    def get_by_id(self, generation_id):
        return dynamic_generation_dao.find_by_id(generation_id)

    def get_generation_branch_by_end_node_id(self, node_id):
        return dynamic_generation_dao.find_branch_by_end_node_id(node_id)

    def get_generation_branch_list_by_generation_id(self, generation_id):
        return dynamic_generation_dao.find_branches_by_dynamic_generation_id(generation_id)

    def list_by_analysis_id(self, analysis_id):
        dynamic_generation_list = dynamic_generation_dao.find_by_analysis_id_with_consumption(
            analysis_id)
        node_id_set = set(
            [dynamic_generation.previous_node_id for dynamic_generation in dynamic_generation_list])
        nodes = node_dao.find_by_id_list(list(node_id_set))
        node_id_to_node = {node.id: node for node in nodes}
        result = []
        for dynamic_generation in dynamic_generation_list:
            dg = convert_model_to_dict(dynamic_generation, True)
            dg["previous_node"] = node_id_to_node.get(
                dynamic_generation.previous_node_id, None).to_dict() if node_id_to_node.get(
                dynamic_generation.previous_node_id, None) is not None else None
            result.append(dg)
        return result

    def list_running_branches_by_analysis_id(self, analysis_id):
        return dynamic_generation_dao.find_running_branches_by_analysis_id(analysis_id)

    def list_nodes(self, dynamic_generation_id):
        dynamic_generation = dynamic_generation_dao.find_by_id(
            dynamic_generation_id)
        if not dynamic_generation:
            return []
        result = []
        previous_node_id = dynamic_generation.previous_node_id
        previous_node = node_dao.find_by_id(previous_node_id)
        if previous_node is not None:
            previous_node_dict = previous_node.to_dict()
            previous_node_dict["is_previous_node"] = True
            result.append(previous_node_dict)
        generated_nodes = node_dao.find_by_dynamic_generation_id(
            dynamic_generation_id)
        for node in generated_nodes:
            node_dict = node.to_dict()
            node_dict["is_previous_node"] = False
            result.append(node_dict)
        return result

    def _update_branch_to_done(self, dynamic_generation_branch_id):
        """Update the branch status to done"""
        now = datetime.now()
        logger.info(f"Handle dynamic generation branch report {dynamic_generation_branch_id}")
        
        dynamic_generation_dao.update_branch(dynamic_generation_branch_id, {
            "state": "done",
            "updated_time": now
        })
        db.session.commit()

    def _get_branch_and_generation_info(self, dynamic_generation_branch_id):
        """Get branch and dynamic generation info"""
        dynamic_generation_branch = dynamic_generation_dao.find_branch_by_id(dynamic_generation_branch_id)
        if not dynamic_generation_branch:
            raise Exception("Dynamic generation branch not found")
            
        current_dynamic_generation = dynamic_generation_dao.find_by_id(
            dynamic_generation_branch.dynamic_generation_id)
        if not current_dynamic_generation:
            raise Exception("Dynamic generation not found")
            
        return dynamic_generation_branch, current_dynamic_generation

    def _build_node_reference_maps(self, analysis_id):
        """Build the node reference map"""
        nodes = node_dao.find_by_analysis_id(analysis_id)
        node_refered_count_map_for_inner = {node.id: 0 for node in nodes}
        node_refered_count_map_for_outer = {node.id: 0 for node in nodes}
        node_map = {node.id: node for node in nodes}
        
        edges = edge_dao.find_by_analysis_id(analysis_id)
        target_to_source = {edge.target_node_id: edge.source_node_id for edge in edges}
        source_to_target = {edge.source_node_id: edge.target_node_id for edge in edges}
        return node_refered_count_map_for_inner, node_refered_count_map_for_outer, node_map, target_to_source, source_to_target

    def _calculate_inner_node_references(self, current_dynamic_generation, node_refered_count_map_for_inner, target_to_source):
        """Count internal node references"""
        branches = dynamic_generation_dao.find_branches_by_dynamic_generation_id(
            current_dynamic_generation.generation_id)

        for branch in branches:
            if branch.state == "done":
                continue
                
            node_ptr = branch.end_node_id
            while node_ptr != current_dynamic_generation.previous_node_id:
                node_refered_count_map_for_inner[node_ptr] += 1
                node_ptr = target_to_source[node_ptr]
        
        return branches

    def _unlock_current_branch_nodes(self, dynamic_generation_branch, current_dynamic_generation,
                                   node_refered_count_map_for_inner, target_to_source):
        """Unlock the nodes of the current branch"""
        node_ptr = dynamic_generation_branch.end_node_id
        unlocked_nodes = []

        logger.info(f"Starting to unlock nodes for branch {dynamic_generation_branch.id}, "
                   f"end_node={node_ptr}, previous_node={current_dynamic_generation.previous_node_id}")

        while node_ptr != current_dynamic_generation.previous_node_id:
            if node_ptr not in node_refered_count_map_for_inner:
                logger.warning(f"Node {node_ptr} not in inner reference map, breaking")
                break

            ref_count = node_refered_count_map_for_inner[node_ptr]
            logger.debug(f"Checking node {node_ptr}: ref_count={ref_count}")

            if ref_count == 0:
                unlocked_nodes.append(node_ptr)
                # Use get() to avoid KeyError
                next_node = target_to_source.get(node_ptr)
                if next_node is None:
                    logger.warning(f"Node {node_ptr} has no source node in target_to_source, breaking")
                    break
                node_ptr = next_node
            else:
                logger.info(f"Node {node_ptr} still has {ref_count} references, stopping unlock chain")
                break

        if unlocked_nodes:
            logger.info(f"Unlocking {len(unlocked_nodes)} nodes from current branch: {unlocked_nodes}")
            node_dao.unlock_dynamic_generation_by_nodes(unlocked_nodes)
        else:
            logger.info("No nodes to unlock from current branch")

    def _log_branch_status(self, branches, generation_id):
        """Log branch statuses for debugging"""
        all_branches_done = all(branch.state == "done" for branch in branches)
        logger.info(f"Branch status check for generation {generation_id}: "
                   f"Total branches: {len(branches)}, All done: {all_branches_done}")
        
        for branch in branches:
            logger.info(f"Branch {branch.id}: end_node_id={branch.end_node_id}, state={branch.state}")
        
        return all_branches_done

    def _update_generation_to_stopped(self, current_dynamic_generation):
        """Update the dynamic generation status to stopped"""
        logger.info(f"All branches completed for generation {current_dynamic_generation.generation_id}, updating state to STOPPED")
        
        dynamic_generation_dao.update(current_dynamic_generation.generation_id, {
            "state": DynamicGenerationState.STOPPED.value,
        })

        if current_dynamic_generation.plan_status is not None:
            dynamic_generation_dao.update(current_dynamic_generation.generation_id, {
                "plan_status": PlanStatus.STOPPED.value,
            })
        
        db.session.commit()

    def _unlock_outer_nodes(self, current_dynamic_generation, node_refered_count_map_for_outer, target_to_source):
        """Unlock external nodes"""
        unlocked_nodes = []

        # Count node references across all running dynamic generation tasks
        dynamic_generations = dynamic_generation_dao.find_running_by_analysis_id(
            current_dynamic_generation.analysis_id)

        logger.info(f"Found {len(dynamic_generations)} other running dynamic generations for analysis {current_dynamic_generation.analysis_id}")

        for dynamic_generation in dynamic_generations:
            logger.debug(f"Processing running generation {dynamic_generation.generation_id}, previous_node={dynamic_generation.previous_node_id}")
            current_node_id = dynamic_generation.previous_node_id
            if current_node_id not in node_refered_count_map_for_outer:
                continue
            while current_node_id is not None:
                node_refered_count_map_for_outer[current_node_id] += 1
                current_node_id = target_to_source.get(current_node_id, None)

        # Find nodes that can be unlocked
        current_node_id = current_dynamic_generation.previous_node_id
        logger.info(f"Starting to unlock outer nodes from previous_node_id={current_node_id}")

        while current_node_id is not None:
            ref_count = node_refered_count_map_for_outer.get(current_node_id, 0)
            logger.debug(f"Checking outer node {current_node_id}: ref_count={ref_count}")

            if ref_count == 0:
                unlocked_nodes.append(current_node_id)
                current_node_id = target_to_source.get(current_node_id, None)
            else:
                logger.info(f"Outer node {current_node_id} still has {ref_count} references from other running generations, stopping unlock chain")
                break

        if unlocked_nodes:
            logger.info(f"Unlocking {len(unlocked_nodes)} outer nodes (including previous_node_id): {unlocked_nodes}")
            node_dao.unlock_dynamic_generation_by_nodes(unlocked_nodes)
        else:
            logger.warning(f"No outer nodes to unlock! previous_node_id={current_dynamic_generation.previous_node_id} may still be locked by other running generations")

    def _report_chat_tool_callback(self, dynamic_generation: DynamicGeneration, node_map: Dict[str, Node], source_to_target: Dict[str, str], target_to_source: Dict[str, str]):
        analysis = analysis_dao.find_user_relation_by_analysis_id(dynamic_generation.analysis_id)
        for relation in analysis:
            if relation.relation == "belong-to":
                user_id = relation.user_id
                break
        else:
            logger.info(f"No owner found for analysis {dynamic_generation.analysis_id}, skipping callback report")
            return
        """Check whether we are inside a subtask"""
        headers = login_main_server(user_id)
        sub_task = query_chat_sub_task(dynamic_generation.generation_id, "run_autogenie", headers)
        if not sub_task:
            logger.info(f"No sub task found for generation {dynamic_generation.generation_id}, skipping callback report")
            return
        """Report a tool callback to the main server"""
        previous_node = node_map.get(dynamic_generation.previous_node_id, None)
        if not previous_node or source_to_target.get(previous_node.id, None) is None:
            report_chat_tool_callback(
                sub_task.get("id"),
                {
                    "success": False,
                    "message": "There are no nodes generated.",
                },
                headers
            )
            return
        generated_nodes = []
        for node_id, node in node_map.items():
            if node.dynamic_generation_id == dynamic_generation.generation_id:
                attrs = {
                    "id": node.id,
                    "name": node.name,
                    "type": node.type,
                    "state": node.state,
                    "functionBlockId": node.function_block_id,
                    "functionBlockVersionId": node.function_block_version_id,
                }
                if node.state == 'finished':
                    latest_computation = computation_dao.find_latest_by_node_id(node.id)
                    figures = figure_dao.find_by_computation_id(latest_computation.id) if latest_computation else []
                    if figures and len(figures) > 0:
                        attrs["figures"] = [{
                            "figureUuid": fig.figure_uuid,
                            "figureName": fig.figure_name
                        } for fig in figures]
                attrs["previousNodeId"] = target_to_source.get(node_id, None)
                generated_nodes.append(attrs)

        report_chat_tool_callback(
            sub_task.get("id"),
            {
                "success": True,
                "message": f"Auto Genie has successfully generated {len(generated_nodes)} nodes.",
                "data": {
                    "generationId": dynamic_generation.generation_id,
                    "nodes": generated_nodes,
                }
            },
            headers
        )

    def handle_branch_done(self, dynamic_generation_branch_id):
        """Handle branch completion"""
        logger.info(f"=== Starting handle_branch_done for branch {dynamic_generation_branch_id} ===")

        # 1. Update branch status
        self._update_branch_to_done(dynamic_generation_branch_id)

        # 2. Get related info
        dynamic_generation_branch, current_dynamic_generation = self._get_branch_and_generation_info(
            dynamic_generation_branch_id)

        logger.info(f"Processing generation {current_dynamic_generation.generation_id}, "
                   f"previous_node_id={current_dynamic_generation.previous_node_id}, "
                   f"branch end_node_id={dynamic_generation_branch.end_node_id}")

        # 3. Build the node reference map
        node_refered_count_map_for_inner, node_refered_count_map_for_outer, node_map, target_to_source, source_to_target = \
            self._build_node_reference_maps(current_dynamic_generation.analysis_id)

        # 4. Count internal node references
        branches = self._calculate_inner_node_references(
            current_dynamic_generation, node_refered_count_map_for_inner, target_to_source)

        # 5. Unlock current branch nodes
        logger.info(f"Step 5: Unlocking current branch nodes (inner nodes)")
        self._unlock_current_branch_nodes(
            dynamic_generation_branch, current_dynamic_generation,
            node_refered_count_map_for_inner, target_to_source)

        # 6. Check all branch statuses
        all_branches_done = self._log_branch_status(branches, current_dynamic_generation.generation_id)

        # 7. If all branches are done, update the main status and unlock external nodes
        if all_branches_done:
            logger.info(f"Step 7: All branches done, updating generation to STOPPED and unlocking outer nodes")
            self._update_generation_to_stopped(current_dynamic_generation)
            self._unlock_outer_nodes(current_dynamic_generation, node_refered_count_map_for_outer, target_to_source)
            self._report_chat_tool_callback(current_dynamic_generation, node_map, source_to_target, target_to_source)
        else:
            logger.info(f"Not all branches completed for generation {current_dynamic_generation.generation_id}, keeping state as RUNNING")

        logger.info(f"=== Completed handle_branch_done for branch {dynamic_generation_branch_id} ===")
        return dynamic_generation_branch

    def stop(self, generation_id):
        dynamic_generation = dynamic_generation_dao.find_by_id(generation_id)
        if not dynamic_generation:
            raise Exception("Dynamic generation not found")
        os.makedirs(f"/tmp/dynamic_generation/signal", exist_ok=True)
        with open(f"/tmp/dynamic_generation/signal/{generation_id}-terminate", "w") as f:
            f.write("1")

        dynamic_generation_dao.update(generation_id, {
            "state": DynamicGenerationState.STOPPED.value
        })

        if dynamic_generation.plan_status is not None:
            dynamic_generation_dao.update(generation_id, {
                "plan_status": PlanStatus.EXECUTION_FAILED.value,
                "plan_status_message": "Dynamic generation was manually terminated"
            })
        return dynamic_generation

    def stop_all(self):
        ready_generations = dynamic_generation_dao.find_by_state(
            DynamicGenerationState.READY.value)
        for generation in ready_generations:
            logger.info(
                f"Stopping Ready Generation {generation.generation_id}")
            self.stop(generation.generation_id)
        running_branches = dynamic_generation_dao.find_branches_by_state(
            DynamicGenerationState.RUNNING.value)
        for branch in running_branches:
            logger.info(f"Stopping branch {branch.id}")
            self.handle_branch_done(branch.id)

    def get_log(self, generation_id):
        waiter = DynamicGenerationWaiter(generation_id)
        dynamic_generation = dynamic_generation_dao.find_by_id(generation_id)
        if not dynamic_generation:
            raise Exception("Dynamic generation not found")
        result = ""
        node_id_queue = [dynamic_generation.previous_node_id]
        node_id_index = 0
        while node_id_index < len(node_id_queue):
            current_node_id = node_id_queue[node_id_index]
            node_id_index += 1
            next_edges = edge_dao.find_by_source_node_id(current_node_id)
            for edge in next_edges:
                node_id_queue.append(edge.target_node_id)
            prompt_log, output_log = waiter.fetch_log(current_node_id)
            result += f"From Node {current_node_id}:\n"
            result += f"Prompt:\n{prompt_log}\n"
            result += f"Output:\n{output_log}\n"
            result += "--------------------------------\n"
        return result

    def get_log_by_previous_node_id(self, generation_id, previous_node_id):
        waiter = DynamicGenerationWaiter(generation_id)
        session = dynamic_generation_dao.find_session_by_source_node_id_and_generation_id(previous_node_id, generation_id)
        if session is None:
            return None
        prompt_log, output_log = waiter.fetch_log(session.id)
        return {
            "prompt": prompt_log,
            "output": output_log
        }

    def get_log_by_node_id(self, generation_id, node_id):
        waiter = DynamicGenerationWaiter(generation_id)
        node = node_dao.find_by_id(node_id)
        if node is None or node.dynamic_generation_session_id is None:
            return None
        prompt_log, output_log = waiter.fetch_log(node.dynamic_generation_session_id)
        return {
            "prompt": prompt_log,
            "output": output_log
        }

    def get_file_upload_info(self, generation_id, file_name):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"dynamic_generation/{generation_id}/files/{file_name}")
        return porter.get_presigned_post(60 * 60)

    def upload_files_to_llm_server(self, generation_id):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"dynamic_generation/{generation_id}/files/"
        )
        files = porter.list_files()
        logger.info(
            f"Upload files to llm server: \n{json.dumps(files, indent=4)}")
        file_infos = []
        for file_key in files:
            file_name = file_key.split("/")[-1]
            porter.set_operation_target(file_key)
            presigned_url = porter.get_presigned_url(60 * 60)
            file_infos.append({
                "name": file_name,
                "url": presigned_url
            })
        llm_interface = LlmInterface()
        llm_interface.upload_files_to_llm_server(
            file_infos
        )

    def record_session(self, session: dict, user_id: str) -> DynamicGenerationSession:
        """
        Record a dynamic generation session in the database.
        :param session: DynamicGenerationSession object to be recorded.
        :return: The recorded session object.
        """
        try:
            for time_key in ['created_at', "start_time", "end_time"]:
                if time_key in session and session[time_key] is not None:
                    if isinstance(session[time_key], (int, float)):
                        session[time_key] = datetime.fromtimestamp(
                            session[time_key] / 1000)
                    elif not isinstance(session[time_key], datetime):
                        session[time_key] = datetime.now()
                else:
                    session[time_key] = None

            # TODO: add user_id to session if needed
            # Convert session dict to DynamicGenerationSession model
            session_model = DynamicGenerationSession(**session)
            return dynamic_generation_dao.insert_session(session_model)
        except Exception as e:
            logger.error(f"Failed to record session: {e}")
            raise e

    def list_sessions(self, generation_id: str) -> list[DynamicGenerationSession]:
        """
        List all dynamic generation sessions for a given generation ID.
        :param generation_id: The ID of the dynamic generation.
        :return: A list of DynamicGenerationSession objects.
        """
        try:
            return dynamic_generation_dao.find_sessions_by_dynamic_generation_id(generation_id)
        except Exception as e:
            logger.error(
                f"Failed to list sessions for generation {generation_id}: {e}")
            return []

    def list_nodes_by_session_id(self, session_id: str) -> list[dict]:
        return node_dao.find_by_dynamic_generation_session_id(session_id)

    def fix_stuck_generation_states(self) -> dict:
        """
        Fix stuck dynamic_generation statuses
        Find all generations whose status is running but whose branches are all finished, and update their status to stopped
        """
        try:
            # Find all running generations
            running_generations = dynamic_generation_dao.find_by_state(DynamicGenerationState.RUNNING.value)
            fixed_count = 0
            fixed_generations = []
            
            for generation in running_generations:
                # Get all branches of this generation
                branches = dynamic_generation_dao.find_branches_by_dynamic_generation_id(generation.generation_id)
                
                # Check whether all branches are finished
                all_branches_done = all(branch.state == "done" for branch in branches)
                
                if all_branches_done and len(branches) > 0:
                    logger.info(f"Found stuck generation {generation.generation_id} with all branches done, fixing state...")
                    
                    # Update the main status to stopped
                    dynamic_generation_dao.update(generation.generation_id, {
                        "state": DynamicGenerationState.STOPPED.value,
                    })
                    
                    # Also update plan_status if present
                    if generation.plan_status is not None:
                        dynamic_generation_dao.update(generation.generation_id, {
                            "plan_status": PlanStatus.STOPPED.value,
                        })
                    
                    db.session.commit()
                    
                    fixed_count += 1
                    fixed_generations.append({
                        "generation_id": generation.generation_id,
                        "analysis_id": generation.analysis_id,
                        "total_branches": len(branches),
                        "previous_state": "running"
                    })
                    
                    logger.info(f"Fixed generation {generation.generation_id}")
                
            logger.info(f"Fixed {fixed_count} stuck dynamic_generation states")
            
            return {
                "fixed_count": fixed_count,
                "fixed_generations": fixed_generations,
                "message": f"Successfully fixed {fixed_count} stuck dynamic_generation states"
            }
            
        except Exception as e:
            logger.error(f"Failed to fix stuck generation states: {e}")
            db.session.rollback()
            return {
                "error": str(e),
                "fixed_count": 0,
                "message": "Failed to fix stuck dynamic_generation states"
            }

    def continue_generation(self, generation_id: str, node_id: str) -> dict:
        try:
            dynamic_generation = dynamic_generation_dao.find_by_id(generation_id)
            if not dynamic_generation:
                error_msg = f"Dynamic generation {generation_id} not found"
                logger.error(error_msg)
                return {"error": error_msg, "code": 404}

            if dynamic_generation.state not in [DynamicGenerationState.STOPPED.value, None]:
                error_msg = f"Dynamic generation {generation_id} is not in a valid state to continue"
                logger.error(error_msg)
                return {"error": error_msg, "code": 400}

            if dynamic_generation.rest_node_count <= 0:
                error_msg = f"Dynamic generation {generation_id} has no remaining nodes to process"
                logger.error(error_msg)
                return {"error": error_msg, "code": 400}

            node = node_dao.find_by_id(node_id)
            if not node or str(node.dynamic_generation_id) != str(generation_id):
                logger.error(f"Node {node_id} does not belong to generation {generation_id}")
                return None

            dynamic_generation_dao.update(generation_id, {
                "state": DynamicGenerationState.RUNNING.value,
                "plan_status": PlanStatus.EXECUTING.value if dynamic_generation.plan_status else None,
            })

            branches = self.get_generation_branch_list_by_generation_id(generation_id)
            target_branch = None
            for branch in branches:
                if branch.end_node_id == int(node_id):
                    target_branch = branch
                    break

            if not target_branch:
                target_branch = DynamicGenerationBranch(
                    dynamic_generation_id=generation_id,
                    end_node_id=node_id,
                    state="running",
                    created_time=datetime.now(),
                    updated_time=datetime.now()
                )
                dynamic_generation_dao.insert_branch(target_branch)

            guardian = AuthorityGuardianFactory.get_authority_guardian(
                AuthorityCarrier.NODE.value)
            user_id = guardian.get_user_id()

            ComputationLauncher.launch_dynamic_generation_with_plan(
                node_id,
                dynamic_generation,
                target_branch,
                user_id
            )

            logger.info(f"[continue] dynamic generation is relaunched")

            return {
                "generation_id": generation_id,
                "state": DynamicGenerationState.RUNNING.value,
                "branch_id": target_branch.id
            }

        except Exception as e:
            logger.error(f"Failed to continue generation: {e}")
            db.session.rollback()
            return None

    def get_info(self, dynamic_generation_id: str) -> Dict:
        """Get dynamic generation information"""
        generation = dynamic_generation_dao.find_by_id(dynamic_generation_id)
        if generation:
            return generation.to_dict()
        return None

    def update_info(self, dynamic_generation_id: str, updated_attrs: Dict) -> bool:
        """Update dynamic generation information"""
        try:
            dynamic_generation_dao.update(dynamic_generation_id, updated_attrs)
            return True
        except Exception as e:
            logger.error(f"Error updating dynamic generation info: {str(e)}")
            return False

    def create_branch(self, dynamic_generation_id: str, end_node_id: str) -> DynamicGenerationBranch:
        """Create a new dynamic generation branch"""
        now = datetime.now()
        new_branch = DynamicGenerationBranch(
            dynamic_generation_id=dynamic_generation_id,
            end_node_id=end_node_id,
            state="running",
            created_time=now,
            updated_time=now
        )
        dynamic_generation_dao.insert_branch(new_branch)
        return new_branch
    
    def invoke_notebook(self, dynamic_generation_id, user_id):
        dynamic_generation = dynamic_generation_dao.find_by_id(dynamic_generation_id)
        if not dynamic_generation:
            raise Exception("Dynamic generation not found")

    def launch_with_claude_code(self, dynamic_generation_id, previous_node_id, user_id):
        """
        1. Validate dynamic_generation exists and is claude_code mode
        2. Create Claude Code node via main server API
        3. Create edge from previous_node to new node
        4. Update dynamic_generation branch with new node
        5. Store plan for the new node
        6. Dispatch task for execution
        """
        import requests
        from constants.common import MAIN_SERVER_HOST, COMPUTATION_SERVER_HOST
        from constants.authority import SYSTEM_AGENT_KEY
        from constants.node import NodeType
        from constants.computation import SystemEnv

        dynamic_generation = dynamic_generation_dao.find_by_id(dynamic_generation_id)
        if not dynamic_generation:
            raise Exception("Dynamic generation not found")

        if dynamic_generation.generation_mode != "claude_code":
            raise Exception("This endpoint is only for Claude Code mode")

        previous_node = node_dao.find_by_id(previous_node_id)
        if not previous_node:
            raise Exception("Previous node not found")

        login_response = requests.post(
            f"http://{MAIN_SERVER_HOST}/server/user/login-by-system"
            f"?user_id={user_id}",
            headers={"X-System-Agent-Key": SYSTEM_AGENT_KEY or ""}
        )
        if login_response.status_code != 200:
            raise Exception(f"Failed to login to main server: {login_response.text}")
        headers = {"token": login_response.json()["data"]}

        computation_resource_configure = {}
        if dynamic_generation.computation_resource_configure:
            computation_resource_configure = json.loads(
                dynamic_generation.computation_resource_configure
            )
            system_env = computation_resource_configure.pop("system_env", SystemEnv.AWS_BATCH.value)
        else:
            system_env = SystemEnv.AWS_BATCH.value

        create_node_response = requests.post(
            f"http://{MAIN_SERVER_HOST}/server/node/create",
            data={
                "node_type": NodeType.CLAUDE_CODE_NODE.value,
                "analysis_id": previous_node.analysis_id,
                "x": previous_node.x + 200,
                "y": previous_node.y + 200,
                "name": f"{dynamic_generation.plan_name or 'Analysis'}",
                "dynamic_generation_id": dynamic_generation_id,
                "system_env": system_env,
                "computation_resource_configure": json.dumps(computation_resource_configure),
            },
            headers=headers
        )

        if create_node_response.status_code != 200:
            raise Exception(f"Failed to create Claude Code node: {create_node_response.text}")

        new_node_data = create_node_response.json()
        if new_node_data.get("code") != 200:
            raise Exception(f"Failed to create Claude Code node: {new_node_data.get('message')}")

        new_node_id = new_node_data["data"]["id"]
        logger.info(f"[claude code] Created Claude Code node: {new_node_id}")

        requests.post(
            f"http://{MAIN_SERVER_HOST}/server/edge/create",
            data={
                "analysis_id": previous_node.analysis_id,
                "source_node_id": previous_node_id,
                "target_node_id": new_node_id,
            },
            headers=headers
        )
        logger.info(f"[claude code] Created edge from {previous_node_id} to {new_node_id}")

        branches = dynamic_generation_dao.find_branches_by_dynamic_generation_id(dynamic_generation_id)
        if branches:
            first_branch = branches[0]
            dynamic_generation_dao.update_branch(first_branch.id, {
                "end_node_id": new_node_id,
                "updated_time": datetime.now()
            })

        dynamic_generation_dao.update(dynamic_generation_id, {
            "plan_status": PlanStatus.EXECUTING.value
        })

        waiter = DynamicGenerationWaiter(dynamic_generation_id)
        plan = waiter.retrieve_plan(previous_node_id)
        if plan:
            waiter.store_plan(new_node_id, plan)
            logger.info(f"[claude code] Stored plan for new node {new_node_id}")

        dispatch_response = requests.post(
            f"http://{COMPUTATION_SERVER_HOST}/computation-server/task/dispatch",
            json={
                "analysis_id": previous_node.analysis_id,
                "node_id_list": [new_node_id],
                "edge_id_list": [],
            },
            headers=headers
        )

        if dispatch_response.status_code != 200:
            logger.error(f"[claude code] Failed to dispatch task: {dispatch_response.text}")
            raise Exception(f"Failed to dispatch task: {dispatch_response.text}")

        logger.info(f"[claude code] Dispatched task for Claude Code node {new_node_id}")

        return {
            "node_id": new_node_id,
            "dynamic_generation_id": dynamic_generation_id,
            "status": "launched"
        }


dynamic_generation_service = DynamicGenerationService()
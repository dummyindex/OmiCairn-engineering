from dao.dynamic_generation import dynamic_generation_dao
from dao.node import node_dao
from dao.computation import computation_dao
from dao.edge import edge_dao
from log.logger_factory import LoggerFactory
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
from sss.porter_factory import PorterFactory

logger = LoggerFactory.get_logger("LLMInteractionMonitor")


class DynamicGenerationLLMMonitorService:
    """
    LLM interaction monitoring service for Dynamic Generation tasks
    Dedicated to monitoring LLM interactions in dynamic_generation tasks, including:
    1. Interactions during next_fb generation (dynamic_generation_session)
    2. Interactions during computation retry (bug fixer) (bug_fixer_session)
    
    Uniformly uses a hybrid mode: a two-level branch->interactions structure
    """

    def _get_branch_nodes_with_topology(self, generation_id: int, end_node_id: int) -> List[int]:
        """
        Get the topology of all nodes on a branch
        Build a backward index map target_node_id -> source_node_id from the edges,
        then backtrack from end_node_id until reaching the first node whose dynamic_generation_id does not match
        """
        dynamic_generation = dynamic_generation_dao.find_by_id(generation_id)
        if not dynamic_generation:
            return []

        # Get nodes and edges of the whole analysis
        all_nodes = node_dao.find_by_analysis_id(dynamic_generation.analysis_id)
        all_edges = edge_dao.find_by_analysis_id(dynamic_generation.analysis_id)
        
        # Build the target_node_id -> source_node_id mapping
        target_to_source_map = {}
        for edge in all_edges:
            target_to_source_map[edge.target_node_id] = edge.source_node_id
            
        # Build a set of node IDs to verify node existence
        valid_node_ids = {node.id for node in all_nodes}
        nodes_in_path = []
        
        # Backtrack starting from end_node_id
        current_node_id = end_node_id
        visited_nodes = set()  # guard against cycles
        previous_node_id = dynamic_generation.previous_node_id
        
        # Add end_node_id itself
        if current_node_id and current_node_id in valid_node_ids:
            current_node = node_dao.find_by_id(current_node_id)
            # Keep only nodes whose dynamic_generation_id is the current generation_id
            if current_node and current_node.dynamic_generation_id == generation_id:
                nodes_in_path.append(current_node_id)
                visited_nodes.add(current_node_id)
            current_node_id = target_to_source_map.get(current_node_id)
        
        # Continue backtracking
        while (current_node_id and 
               current_node_id != previous_node_id and 
               current_node_id in valid_node_ids and
               current_node_id not in visited_nodes):
            
            current_node = node_dao.find_by_id(current_node_id)
            if not current_node or current_node.dynamic_generation_id != generation_id:
                break
                
            visited_nodes.add(current_node_id)
            nodes_in_path.append(current_node_id)
            
            # Look up the parent node in the in-memory map
            current_node_id = target_to_source_map.get(current_node_id)
        
        # Add the start node
        if previous_node_id and previous_node_id in valid_node_ids and previous_node_id not in visited_nodes:
            nodes_in_path.append(previous_node_id)
            
        nodes_in_path.reverse()  # reverse into chronological order
        
        logger.debug(f"Branch topology for generation {generation_id}: "
                    f"found path of length {len(nodes_in_path)} from node {end_node_id}")
        
        return nodes_in_path

    def _create_interaction_from_dynamic_generation_session(self, session) -> Dict[str, Any]:
        """
        Convert a dynamic_generation_session into an interaction object
        """
        return {
            "id": f"dgs_{session.id}",
            "type": "dynamic_generation",
            "session_id": session.id,
            "interaction_source": "next_fb_generation",
            "source_node_id": session.source_node_id,
            "dynamic_generation_id": session.dynamic_generation_id,
            "is_valid": session.is_valid,
            "errors": session.errors,
            "start_time": session.start_time.timestamp() * 1000 if session.start_time else None,
            "end_time": session.end_time.timestamp() * 1000 if session.end_time else None,
            "created_at": session.created_at.timestamp() * 1000 if session.created_at else None,
            "session_type": session.type
        }

    def _create_interaction_from_bug_fixer_session(self, session) -> Dict[str, Any]:
        """
        Convert a bug_fixer_session into an interaction object
        """
        return {
            "id": f"bfs_{session.id}",
            "type": "bug_fixer", 
            "session_id": session.id,
            "interaction_source": "computation_retry_bug_fixer",
            "node_id": session.node_id,
            "retry_process_id": session.retry_process_id,
            "is_valid": session.is_valid,
            "errors": session.errors,
            "start_time": session.start_time.timestamp() * 1000 if session.start_time else None,
            "end_time": session.end_time.timestamp() * 1000 if session.end_time else None,
            "created_at": session.created_at.timestamp() * 1000 if session.created_at else None,
            "session_type": session.type
        }

    def get_generation_interactions(self, generation_id: int) -> Dict[str, Any]:
        """
        Get all LLM interactions of a complete dynamic_generation task
        Returned as a two-level branch->interactions structure
        """
        try:
            dynamic_generation = dynamic_generation_dao.find_by_id(generation_id)
            if not dynamic_generation:
                return {"error": "Dynamic generation not found"}

            # Get all branches
            branches = dynamic_generation_dao.find_branches_by_dynamic_generation_id(generation_id)
            
            result_branches = []
            
            for branch in branches:
                # Get all nodes on the branch
                branch_nodes = self._get_branch_nodes_with_topology(generation_id, branch.end_node_id)
                
                interactions = []

                initial_plan_sessions = dynamic_generation_dao.find_sessions_by_source_node_id_and_generation_id(
                    dynamic_generation.previous_node_id, generation_id)
                for session in initial_plan_sessions:
                    interaction = self._create_interaction_from_dynamic_generation_session(session)
                    interactions.append(interaction)
                
                # Collect dynamic_generation_sessions
                for node_id in branch_nodes:
                    node = node_dao.find_by_id(node_id)
                    if node and node.dynamic_generation_session_id:
                        session = dynamic_generation_dao.find_session_by_id(node.dynamic_generation_session_id)
                        if session:
                            interaction = self._create_interaction_from_dynamic_generation_session(session)
                            interactions.append(interaction)
                        plan_sessions = dynamic_generation_dao.find_sessions_by_source_node_id_and_generation_id(
                            node_id, generation_id)
                        for session in plan_sessions:
                            interaction = self._create_interaction_from_dynamic_generation_session(session)
                            interactions.append(interaction)
                
                # Collect bug_fixer_sessions
                for node_id in branch_nodes:
                    # Look up computation_retry_process by node_id
                    retry_processes = computation_dao.find_retry_process_by_node_id(node_id)
                    for retry_process in retry_processes:
                        # Find bug_fixer_sessions related to this retry_process
                        bug_fixer_sessions = computation_dao.find_bug_fixer_sessions_by_retry_process_id(retry_process.id)
                        for session in bug_fixer_sessions:
                            if session.dynamic_generation_id != generation_id:
                                continue
                            interaction = self._create_interaction_from_bug_fixer_session(session)
                            interactions.append(interaction)
                    
                    # Also check the new_node_id case
                    retry_processes_new = computation_dao.find_retry_process_by_new_node_id(node_id)
                    for retry_process in retry_processes_new:
                        bug_fixer_sessions = computation_dao.find_bug_fixer_sessions_by_retry_process_id(retry_process.id)
                        for session in bug_fixer_sessions:
                            if session.dynamic_generation_id != generation_id:
                                continue
                            interaction = self._create_interaction_from_bug_fixer_session(session)
                            interactions.append(interaction)
                
                # Merge both lists, sort by start_time descending and deduplicate
                interactions = list({interaction['id']: interaction for interaction in interactions}.values())
                interactions.sort(key=lambda x: x.get('start_time', x.get('created_at', 0)) or 0, reverse=True)
                
                branch_data = {
                    "branch_id": branch.id,
                    "end_node_id": branch.end_node_id,
                    "state": branch.state,
                    "created_time": branch.created_time.timestamp() * 1000 if branch.created_time else None,
                    "updated_time": branch.updated_time.timestamp() * 1000 if branch.updated_time else None,
                    "interactions": interactions,
                    "total_interactions": len(interactions),
                    "nodes_in_branch": branch_nodes
                }
                
                result_branches.append(branch_data)
            
            return {
                "generation_id": generation_id,
                "previous_node_id": dynamic_generation.previous_node_id,
                "state": dynamic_generation.state,
                "branches": result_branches,
                "total_branches": len(result_branches),
                "last_updated": datetime.now().timestamp() * 1000
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(traceback.format_exc())
            logger.error(f"Error getting generation interactions: {e}")
            return {"error": str(e)}

    def get_interaction_details(self, interaction_type: str, session_id: int, 
                              dynamic_generation_id: Optional[int] = None,
                              retry_process_id: Optional[int] = None,
                              node_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch detailed content from S3 according to the interaction type
        - dynamic_generation: s3://bucket/dynamic_generation/{dynamic_generation_id}/{session_id}/
        - bug_fixer: s3://bucket/retry_process/{retry_process_id}/{node_id}/
        """
        try:
            # Use the porter tool instead of a direct S3 client
            porter = PorterFactory.create_porter()
            
            result = {
                "interaction_type": interaction_type,
                "session_id": session_id,
                "input": None,
                "output": None,
                "files_found": []
            }
            
            if interaction_type == "dynamic_generation":
                if not dynamic_generation_id:
                    return {"error": "dynamic_generation_id is required for dynamic_generation type"}
                
                # S3 path: dynamic_generation/{dynamic_generation_id}/{session_id}/
                base_path = f"dynamic_generation/{dynamic_generation_id}/{session_id}/"
                
                # Try to fetch prompt.json
                try:
                    prompt_key = f"{base_path}prompt.json"
                    porter.set_operation_target(prompt_key)
                    prompt_content = porter.fetch_file_text()
                    if prompt_content:
                        result["input"] = prompt_content
                except Exception as e:
                    logger.warning(f"Failed to get prompt.json from {prompt_key}: {e}")
                    result["input"] = {"prompt": None}

                # Try to fetch output.json
                try:
                    output_key = f"{base_path}output.json"
                    porter.set_operation_target(output_key)
                    output_content = porter.fetch_file_text()
                    if output_content:
                        result["output"] = output_content
                except Exception as e:
                    logger.warning(f"Failed to get output.json from {output_key}: {e}")
                    result["output"] = {"text": None}

            elif interaction_type == "bug_fixer":
                if not retry_process_id or not session_id:
                    return {"error": "retry_process_id and session_id are required for bug_fixer type"}

                # S3 path: retry_process/{retry_process_id}/{session_id}/
                base_path = f"retry_process/{retry_process_id}/{session_id}/"
                
                # Try to fetch session.json
                try:
                    input_key = f"{base_path}session.json"
                    porter.set_operation_target(input_key)
                    session_content = porter.fetch_file_text()
                    session = json.loads(session_content)
                    if session_content:
                        result["input"] = session.get("input_prompt", None)
                        result["output"] = session.get("raw_response", None)
                except Exception as e:
                    logger.warning(f"Failed to get session.json  from {input_key}: {e}")
                    result["input"] = {"prompt": None}
                    result["output"] = {"text": None}

            else:
                return {"error": f"Unsupported interaction type: {interaction_type}"}
            
            logger.info(f"Successfully retrieved interaction details for type: {interaction_type}, "
                       f"session_id: {session_id}")
            
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(traceback.format_exc())
            logger.error(f"Error getting interaction details: {e}")
            return {"error": str(e)}


# Create the service instance
dynamic_generation_llm_monitor_service = DynamicGenerationLLMMonitorService()
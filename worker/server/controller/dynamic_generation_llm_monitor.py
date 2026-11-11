from flask import Blueprint, request
from flask_restful import Api, Resource
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from service.dynamic_generation_llm_monitor import dynamic_generation_llm_monitor_service
from log.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("DynamicGenerationLLMMonitorController")


class DynamicGenerationInteractionsAPI(Resource):
    """Dynamic Generation LLM interaction monitoring API - hybrid mode"""
    
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "generation_id"
        ])
        
        generation_id = int(request.args.get("generation_id"))
        
        logger.info(f"Getting interactions for generation_id: {generation_id}")
        
        result = dynamic_generation_llm_monitor_service.get_generation_interactions(generation_id)
        
        if "error" in result:
            return ResponseManager.new_bad_request_response(result["error"])
        
        return ResponseManager.new_success_response(data=result)


class InteractionDetailsAPI(Resource):
    """API to get the detailed content of a single interaction"""
    
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "interaction_type",
            "session_id"
        ])
        
        interaction_type = request.args.get("interaction_type")
        session_id = int(request.args.get("session_id"))
        
        # Get optional parameters
        dynamic_generation_id = request.args.get("dynamic_generation_id")
        retry_process_id = request.args.get("retry_process_id")
        node_id = request.args.get("node_id")
        
        logger.info(f"Getting interaction details for type: {interaction_type}, session_id: {session_id}")
        
        result = dynamic_generation_llm_monitor_service.get_interaction_details(
            interaction_type=interaction_type,
            session_id=session_id,
            dynamic_generation_id=int(dynamic_generation_id) if dynamic_generation_id else None,
            retry_process_id=int(retry_process_id) if retry_process_id else None,
            node_id=int(node_id) if node_id else None
        )
        
        if "error" in result:
            return ResponseManager.new_bad_request_response(result["error"])
        
        return ResponseManager.new_success_response(data=result)


# Create the blueprint and API
dynamic_generation_llm_monitor_bp = Blueprint("dynamic_generation_llm_monitor", __name__)
dynamic_generation_llm_monitor_api = Api(dynamic_generation_llm_monitor_bp, "/dynamic-generation-llm-monitor")

# Register API resources
dynamic_generation_llm_monitor_api.add_resource(
    DynamicGenerationInteractionsAPI, 
    "/interactions"
)
dynamic_generation_llm_monitor_api.add_resource(
    InteractionDetailsAPI,
    "/interaction-details"
)
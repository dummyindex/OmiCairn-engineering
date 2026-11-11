"""
Code Agent LLM Proxy Controller

Provides a proxy endpoint for code_agent to call LLM through omicairn-worker,
which has access to network proxy and can reach GPT server.
"""

from flask import Blueprint, request
from flask_restful import Api, Resource
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from log.logger_factory import LoggerFactory
import requests
import os

logger = LoggerFactory.get_logger("CodeAgentProxyController")

# Environment variables
GPT_WORKFLOW_SERVER_HOST = os.environ.get("GPT_WORKFLOW_SERVER_HOST")
GPT_WORKFLOW_SERVER_PORT = os.environ.get("GPT_WORKFLOW_SERVER_PORT", "5000")
NETWORK_PROXY_HOST = os.environ.get("NETWORK_PROXY_HOST")
NETWORK_PROXY_PORT = os.environ.get("NETWORK_PROXY_PORT")
SYSTEM_AGENT_KEY = os.getenv("SYSTEM_AGENT_KEY")

# Proxy configuration
PROXIES = None
if NETWORK_PROXY_HOST and NETWORK_PROXY_PORT:
    PROXIES = {
        "http": f"http://{NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}",
        "https": f"http://{NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}"
    }
    logger.info(f"Using proxy: {NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}")
else:
    logger.warning("No proxy configured")


class CodeAgentLLMProxyAPI(Resource):
    """
    Proxy endpoint for code_agent to call LLM
    
    Request body:
    {
        "messages": [{"role": "...", "content": "..."}],
        "tools": [...],  # optional
        "model": "gpt-4o",  # optional
        "temperature": 0.0  # optional
    }
    
    Response:
    {
        "code": 200,
        "message": "success",
        "data": {
            "message": "LLM response text",
            "token_consumptions": {...},
            "model_time": 0.0,
            "tool_calls": [...]
        }
    }
    """
    
    @exception_wrapper
    def post(self):
        """Forward LLM request to GPT server"""
        try:
            # Validate request
            request_auditor.request_json_check(request, ["messages"])
            post_data = request.get_json()
            
            messages = post_data.get("messages")
            tools = post_data.get("tools")
            model = post_data.get("model", "gpt-4o")
            temperature = post_data.get("temperature", 0.0)
            
            # Build request for GPT server
            gpt_request = {
                "messages": messages,
                "model": model,
                "temperature": temperature
            }
            
            if tools:
                gpt_request["tools"] = tools
            
            # Call GPT workflow server
            gpt_url = f"http://{GPT_WORKFLOW_SERVER_HOST}:{GPT_WORKFLOW_SERVER_PORT}/v3.0/chat"
            
            # Get token from request headers if available
            headers = {}
            if request.headers.get("token"):
                headers["token"] = request.headers.get("token")
            
            response = requests.post(
                gpt_url,
                json=gpt_request,
                headers=headers,
                proxies=PROXIES,
                timeout=600  # 10 minutes timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') != 200:
                error_msg = result.get('message', 'Unknown error from GPT server')
                logger.error(f"GPT server returned error: {error_msg}")
                return ResponseManager.new_bad_request_response(error_msg)
            
            data = result.get('data', {})
            
            return ResponseManager.new_success_response(data=data)
            
        except requests.exceptions.Timeout:
            logger.error("GPT server request timeout")
            return ResponseManager.new_bad_request_response("LLM request timeout")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling GPT server: {str(e)}")
            return ResponseManager.new_bad_request_response(f"Failed to call GPT server: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected error in code agent proxy: {str(e)}")
            import traceback
            traceback.print_exc()
            return ResponseManager.new_bad_request_response(f"Internal error: {str(e)}")


class CodeAgentHealthCheckAPI(Resource):
    """Health check endpoint for code_agent proxy"""
    
    @exception_wrapper
    def get(self):
        """Check if proxy is configured and accessible"""
        status = {
            "proxy_configured": PROXIES is not None,
            "gpt_server_host": GPT_WORKFLOW_SERVER_HOST,
            "gpt_server_port": GPT_WORKFLOW_SERVER_PORT,
            "network_proxy": f"{NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}" if PROXIES else None
        }
        
        return ResponseManager.new_success_response(data=status)


class CodeAgentMessageUploadPresignedAPI(Resource):
    """
    Generate presigned POST URL for uploading code agent messages to S3
    
    Request body:
    {
        "computation_id": "xxx",
        "message_uuid": "xxx"
    }
    
    Response:
    {
        "code": 200,
        "message": "success",
        "data": {
            "url": "https://...",
            "fields": {...}
        }
    }
    """
    
    @exception_wrapper
    def post(self):
        """Generate presigned POST for message upload"""
        from sss.porter_factory import PorterFactory
        
        try:
            request_auditor.request_json_check(request, ["computation_id", "message_uuid"])
            post_data = request.get_json()
            
            computation_id = post_data.get("computation_id")
            message_uuid = post_data.get("message_uuid")
            
            # Create porter for S3 operations
            porter = PorterFactory.create_porter()
            
            # Set S3 key: code_agent_messages/{computation_id}/{message_uuid}.json
            s3_key = f"code_agent_messages/{computation_id}/{message_uuid}.json"
            porter.set_operation_target(s3_key)
            
            # Generate presigned POST (valid for 1 hour)
            presigned_post = porter.get_presigned_post(expiration=3600)
            
            return ResponseManager.new_success_response(data=presigned_post)
            
        except Exception as e:
            logger.error(f"Error generating presigned POST: {str(e)}")
            import traceback
            traceback.print_exc()
            return ResponseManager.new_bad_request_response(f"Failed to generate presigned POST: {str(e)}")


class CodeAgentMessageListAPI(Resource):
    """
    List code agent messages for a computation
    
    Query parameters:
    - computation_id: Computation ID (required)
    - offset: Pagination offset (default: 0)
    - limit: Pagination limit (default: 20)
    
    Response:
    {
        "code": 200,
        "message": "success",
        "data": {
            "messages": [
                {
                    "message_uuid": "xxx",
                    "s3_key": "code_agent_messages/xxx/xxx.json",
                    "last_modified": "2025-10-20T10:30:00Z",
                    "size": 1234,
                    "presigned_url": "https://..."
                }
            ],
            "total": 100,
            "offset": 0,
            "limit": 20,
            "has_more": true
        }
    }
    """
    
    @exception_wrapper
    def get(self):
        """List messages for a computation with pagination"""
        from sss.porter_factory import PorterFactory
        
        try:
            computation_id = request.args.get("computation_id")
            if not computation_id:
                return ResponseManager.new_bad_request_response("Missing computation_id parameter")
            
            offset = int(request.args.get("offset", 0))
            limit = int(request.args.get("limit", 20))
            
            # Create porter for S3 operations
            porter = PorterFactory.create_porter()
            
            # List all messages for this computation
            prefix = f"code_agent_messages/{computation_id}/"
            porter.set_operation_target(prefix)
            
            # List files in S3
            all_files = porter.list_files()
            
            if not all_files:
                return ResponseManager.new_success_response(data={
                    "messages": [],
                    "total": 0,
                    "offset": offset,
                    "limit": limit,
                    "has_more": False
                })
            
            # Get metadata for each file
            message_list = []
            for file_key in all_files:
                try:
                    # Extract message_uuid from key: code_agent_messages/{computation_id}/{message_uuid}.json
                    message_uuid = file_key.split('/')[-1].replace('.json', '')
                    
                    # Get file metadata
                    porter.set_operation_target(file_key)
                    metadata = porter.get_file_info()
                    
                    message_list.append({
                        "message_uuid": message_uuid,
                        "s3_key": file_key,
                        "last_modified": metadata.get("LastModified"),
                        "size": metadata.get("Size", 0)
                    })
                except Exception as e:
                    logger.error(f"Error getting metadata for {file_key}: {e}")
                    continue
            
            # Sort by last_modified (newest first)
            message_list.sort(key=lambda x: x.get("last_modified", ""), reverse=True)
            
            # Apply pagination
            total = len(message_list)
            paginated_messages = message_list[offset:offset + limit]
            has_more = (offset + limit) < total
            
            # Generate presigned URLs for paginated messages
            for msg in paginated_messages:
                porter.set_operation_target(msg["s3_key"])
                msg["presigned_url"] = porter.get_presigned_url(expiration=3600)

            return ResponseManager.new_success_response(data={
                "messages": paginated_messages,
                "total": total,
                "offset": offset,
                "limit": limit,
                "has_more": has_more
            })
            
        except Exception as e:
            logger.error(f"Error listing messages: {str(e)}")
            import traceback
            traceback.print_exc()
            return ResponseManager.new_bad_request_response(f"Failed to list messages: {str(e)}")


class CodeAgentActionRecordsUploadAPI(Resource):
    @exception_wrapper
    def post(self):
        """
        Upload code agent action records to S3

        Request body:
        {
            "computation_id": "123",
            "actions": [...]
        }
        """
        request_auditor.request_json_check(request, ["computation_id", "actions"])
        post_data = request.get_json()
        computation_id = post_data.get("computation_id")
        actions = post_data.get("actions")

        from sss.porter_factory import PorterFactory
        import json
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"code_agent_space/{computation_id}/actions.json")
        porter.save_file_text(json.dumps(actions, indent=2))

        return ResponseManager.new_success_response(data=True)

class CodeAgentActionRecordsGetAPI(Resource):
    @exception_wrapper
    def get(self):
        from sss.porter_factory import PorterFactory
        import json
        request_auditor.request_args_check(request, ["computation_id"])
        computation_id = request.args.get("computation_id")
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"code_agent_space/{computation_id}/actions.json")
        actions = porter.fetch_file_text() or "[]"
        return ResponseManager.new_success_response(data=json.loads(actions))

# Register blueprint
code_agent_proxy_bp = Blueprint("code_agent_proxy", __name__)
code_agent_proxy_api = Api(code_agent_proxy_bp, "/code-agent-proxy")
code_agent_proxy_api.add_resource(CodeAgentLLMProxyAPI, "/llm/chat")
code_agent_proxy_api.add_resource(CodeAgentHealthCheckAPI, "/health")
code_agent_proxy_api.add_resource(CodeAgentMessageUploadPresignedAPI, "/message/upload-presigned")
code_agent_proxy_api.add_resource(CodeAgentMessageListAPI, "/message/list")
code_agent_proxy_api.add_resource(CodeAgentActionRecordsUploadAPI, "/upload-action-records")
code_agent_proxy_api.add_resource(CodeAgentActionRecordsGetAPI, "/get-action-records")

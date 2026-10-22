import json
from datetime import datetime
from typing import Dict, Any, List, Optional
try:
    from .server_api_invoker import ServerAPIInvoker
except ImportError:
    from server_api_invoker import ServerAPIInvoker
import os
DATA_SERVER_HOST = os.getenv("DATA_SERVER_HOST")

class ChatStatus:
    NORMAL = "normal"
    EXECUTING = "executing"
    RESPONDING = "responding"
    SUMMARIZING = "summarizing"


class ChatSubTaskStatus:
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"


class MessageRole:
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class ChatAgent:
    """Chat Agent for handling chat interactions and tool executions"""
    
    def __init__(self, chat_id: str, user_id: str = None):
        self.chat_id = chat_id
        self.user_id = user_id
        self.api = ServerAPIInvoker(user_id=user_id)
        self.chat_information = self.api.get_chat_information(chat_id)
        
        if not self.chat_information:
            raise ValueError(f"Chat {chat_id} not found")
    
    def init(self) -> bool:
        """Initialize chat - currently just pass"""
        return True
    
    def auto_handle_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        auto_triggered_tool_calls = [
            "get_analysis_info",
            "get_current_node_branch",
            "get_current_node_info",
            "plan_autogenie",
            "run_autogenie",
            "get_computation_details",
            "get_available_function_blocks",
            "get_function_block_codes",
            "create_computation_node",
            "create_report",
            "create_data_node",
            "change_current_node",
            "capture_data",
            "run_node",
            "read_file",
        ]
        for tool_call in tool_calls:
            # [{"id": "call_vMvOb5HlkMObh1L7JkorhFVb", "name": "run_autogenie", "parameters": {"generation_id": "531"}}]
            tool_name = tool_call.get("name", None)
            tool_params = tool_call.get("parameters", {})
            tool_call_id = tool_call.get("id", None)
            if tool_name in auto_triggered_tool_calls:
                print(f"Auto executing tool: {tool_name} with params: {tool_params}")
                self.call_tool(tool_name, tool_params if tool_params else {}, tool_call_id)

    def auto_handle_history(self) -> List[dict]:
        """Auto handle history messages for summarization if needed"""
        all_messages = self.api.get_chat_messages(self.chat_id)
        all_messages_without_new = all_messages[:-1]  # Exclude the just added user message for summarization check
        unsummarized_messages = [msg for msg in all_messages_without_new if msg.get("summaryMessageId", None) is None]
        if len(unsummarized_messages) > 30:
            print("Summarizing history messages ...")
            self.api.update_chat_information(self.chat_id, {
                "status": ChatStatus.SUMMARIZING,
            })
            summary_message = self.api.create_chat_message(self.chat_id, {
                "chat_id": self.chat_id,
                "content": "Summarizing previous messages ...",
                "role": MessageRole.ASSISTANT,
                "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model": self.chat_information.get("model", "gpt-4o-mini"),
                "model_time": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "is_summary": True
            })

            unsummarized_messages_contents = [
                {
                    "role": msg["role"],
                    "content": msg["content"] or "",
                    "toolCalls": json.loads(msg["toolCalls"]) if msg["toolCalls"] else None
                } for msg in unsummarized_messages
            ]

            success, message, summary_pack = self.api.summary_history_messages(
                unsummarized_messages_contents,
                model=self.chat_information.get("model", "gpt-4o-mini"),
                max_tokens=10240
            )

            if not success:
                self.api.update_chat_information(self.chat_id, {
                    "status": ChatStatus.NORMAL
                })
                return []
            summary = summary_pack.get("summary", "Empty summary")
            prompt_tokens = summary_pack.get("token_consumptions", {}).get("prompt_tokens", 0)
            completion_tokens = summary_pack.get("token_consumptions", {}).get("completion_tokens", 0)
            total_tokens = prompt_tokens + completion_tokens
            
            self.api.update_chat_message(summary_message["id"], {
                "content": summary,
                "model_time": summary_pack.get("model_time", 0),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            })
            summary_message.update({
                "content": summary,
                "modelTime": summary_pack.get("model_time", 0),
                "promptTokens": prompt_tokens,
                "completionTokens": completion_tokens,
            })
            
            # Record LLM consumption
            consumption_data = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "model": self.chat_information.get("model", "gpt-4o-mini"),
                "functionality": "Chat",
                "functionality_task_id": self.chat_id,
                "node_id": None
            }
            self.api.record_llm_consumption(consumption_data)
            self.api.update_batch_chat_messages(
                [msg["id"] for msg in unsummarized_messages],
                {"summary_message_id": summary_message["id"]}
            )
            self.api.update_chat_information(self.chat_id, {
                "status": ChatStatus.NORMAL
            })
            return [summary_message] + [all_messages[-1]]  # Return summary message and the last user message
        return unsummarized_messages + [all_messages[-1]]  # Return all messages if no summarization needed
    
    def send_message(self, message: str, attached_files: List[str] = None) -> bool:
        """Send a user message and get LLM response"""
        try:
            # Create user message
            user_message_data = {
                "chat_id": self.chat_id,
                "content": message,
                "role": MessageRole.USER,
                "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model": None,
                "model_time": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0
            }
            
            if attached_files:
                user_message_data["attached_file_s3_keys"] = attached_files
            
            user_message = self.api.create_chat_message(self.chat_id, user_message_data)

            if not user_message:
                return False
            
            self.api.update_chat_information(self.chat_id, {
                "status": ChatStatus.RESPONDING
            })

            post_common_messages = self.auto_handle_history()

            self.api.update_chat_information(self.chat_id, {
                "status": ChatStatus.RESPONDING
            })

            system_messages = self._get_system_message()
            post_messages = system_messages

            for common_message in post_common_messages:
                if common_message["role"] == MessageRole.USER:
                    content = common_message["content"] or ""
                    if common_message.get("attachedFileS3Keys"):
                        attached_file_s3_keys = common_message["attachedFileS3Keys"]
                        
                        if isinstance(attached_file_s3_keys, str):
                            try:
                                attached_file_s3_keys = json.loads(attached_file_s3_keys)
                            except json.JSONDecodeError:
                                attached_file_s3_keys = [attached_file_s3_keys]

                        if not isinstance(attached_file_s3_keys, list):
                            attached_file_s3_keys = list(attached_file_s3_keys) if attached_file_s3_keys else []

                        attached_file_s3_keys_str = ", ".join(attached_file_s3_keys.copy())
                        content += f"\n\n[Attached files s3 paths: {attached_file_s3_keys_str}]"
                        
                    post_messages.append({
                        "role": common_message["role"],
                        "content": content
                    })
                elif common_message["role"] == MessageRole.ASSISTANT:
                    tool_calls = json.loads(common_message["toolCalls"]) if common_message["toolCalls"] else None
                    if tool_calls is not None and len(tool_calls) > 0:
                        tool_calls = [
                            {
                                "type": "function",
                                "id": tc.get("id", None),
                                "function": {
                                    "name": tc.get("name", ""),
                                    "arguments": json.dumps(tc.get("parameters", {}))  # ensure it is a JSON string
                                }
                            } for tc in tool_calls
                        ]
                    post_messages.append({
                        "role": common_message["role"],
                        "content": common_message["content"] or "",
                        # "tool_calls": tool_calls
                    })
                elif common_message["role"] == MessageRole.TOOL:
                    # Add tool result as system message
                    post_messages.append({
                        # "role": "tool",
                        "role": "user",
                        # "tool_call_id": history_message["toolCallId"],
                        "content": f"Tool execution result: {common_message['content']}"
                    })
            
            # Call LLM
            tools = self._get_tools()
            new_message, token_consumptions, model_time, tool_calls = self.api.chat_with_llm(
                post_messages,
                tools=tools,
                model=self.chat_information.get("model", "gpt-4o-mini")
            )
            
            prompt_tokens = token_consumptions.get("prompt_tokens", 0)
            completion_tokens = token_consumptions.get("completion_tokens", 0)
            total_tokens = prompt_tokens + completion_tokens
            
            # Create assistant message
            self.api.create_chat_message(self.chat_id, {
                "chat_id": self.chat_id,
                "content": new_message,
                "tool_calls": json.dumps(tool_calls) if tool_calls else None,
                "role": MessageRole.ASSISTANT,
                "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model": self.chat_information.get("model", "gpt-4o-mini"),
                "model_time": model_time,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            })
            
            # Record LLM consumption
            consumption_data = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "model": self.chat_information.get("model", "gpt-4o-mini"),
                "functionality": "Chat",
                "functionality_task_id": self.chat_id,
                "node_id": None
            }
            self.api.record_llm_consumption(consumption_data)
            
            # Update chat status back to normal
            self.api.update_chat_information(self.chat_id, {
                "status": ChatStatus.NORMAL
            })

            self.auto_handle_tool_calls(tool_calls if tool_calls else [])
            
            return True
            
        except Exception as e:
            print(f"Error in send_message: {str(e)}")
            # Reset status to normal on error
            self.api.update_chat_information(self.chat_id, {
                "status": ChatStatus.NORMAL,
                "updated_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return False

    def call_tool(self, tool_name: str, tool_params: Dict[str, Any], tool_call_id: str) -> Dict[str, Any]:
        """Call a tool and execute it"""
        # Create tool message
        tool_content = f"Calling tool: {tool_name}"
        if tool_params:
            tool_content += f" with params: {json.dumps(tool_params)}"
        
        chat_message = self.api.create_chat_message(self.chat_id, {
            "chat_id": self.chat_id,
            "tool_call_id": tool_call_id,
            "content": tool_content,
            "role": MessageRole.TOOL,
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": None,
            "model_time": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0
        })

        if not chat_message:
            return {"error": "Failed to create tool message"}
        
        # Create sub task
        chat_sub_task = self.api.create_chat_sub_task(self.chat_id, {
            "chat_id": self.chat_id,
            "chat_message_id": chat_message["id"],
            "tool_name": tool_name,
            "tool_params": json.dumps(tool_params),
            "tool_call_id": tool_call_id,
            "system_task_id": None,
            "outputs": None,
            "status": ChatSubTaskStatus.RUNNING,
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": None
        })
        
        if not chat_sub_task:
            return {"error": "Failed to create sub task"}
        
        # Update chat status to executing
        self.api.update_chat_information(self.chat_id, {
            "status": ChatStatus.EXECUTING
        })
        
        # Execute the tool
        self._execute_tool(tool_name, tool_params, chat_sub_task["id"])
        
    
    def call_tool_feedback(self, chat_sub_task_id: str, output: str) -> bool:
        """Process tool feedback and get LLM response"""
        output_data = json.loads(output) if output else {}
        status = output_data.get("status", ChatSubTaskStatus.FINISHED)
        # try:
        # Get sub task information
        chat_sub_task = self.api.get_chat_sub_task(chat_sub_task_id)
        if not chat_sub_task:
            print(f"Sub task {chat_sub_task_id} not found")
            return False
        
        # Update chat status to responding
        self.api.update_chat_information(self.chat_id, {
            "status": ChatStatus.RESPONDING,
        })

        self.api.update_chat_sub_task(chat_sub_task_id, {
            "outputs": output,
            "status": status,
            "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        self.api.update_chat_message(chat_sub_task["chatMessageId"], {
            "content": output
        })
        
        post_common_messages = self.auto_handle_history()

        self.api.update_chat_information(self.chat_id, {
            "status": ChatStatus.RESPONDING
        })

        system_messages = self._get_system_message()
        post_messages = system_messages

        for history_message in post_common_messages:
            if history_message["role"] == MessageRole.USER:
                content = history_message["content"] or ""
                if history_message.get("attachedFileS3Keys"):
                    attached_file_s3_keys = history_message["attachedFileS3Keys"]

                    if isinstance(attached_file_s3_keys, str):
                        try:
                            attached_file_s3_keys = json.loads(attached_file_s3_keys)
                        except json.JSONDecodeError:
                            attached_file_s3_keys = [attached_file_s3_keys]

                    if not isinstance(attached_file_s3_keys, list):
                        attached_file_s3_keys = list(attached_file_s3_keys) if attached_file_s3_keys else []

                    attached_file_s3_keys_str = ", ".join(attached_file_s3_keys)
                    content += f"\n\n[Attached files: {attached_file_s3_keys_str}]"

                post_messages.append({
                    "role": history_message["role"],
                    "content": content
                })
            elif history_message["role"] == MessageRole.ASSISTANT:
                tool_calls = json.loads(history_message["toolCalls"]) if history_message["toolCalls"] else None
                if tool_calls is not None and len(tool_calls) > 0:
                    tool_calls = [
                        {
                            "type": "function",
                            "id": tc.get("id", None),
                            "function": {
                                "name": tc.get("name", ""),
                                "arguments": json.dumps(tc.get("parameters", {}))  # ensure it is a JSON string
                            }
                        } for tc in tool_calls
                    ]
                post_messages.append({
                    "role": history_message["role"],
                    "content": history_message["content"] or "",
                    # "tool_calls": tool_calls
                })
            elif history_message["role"] == MessageRole.TOOL:
                # Add tool result as system message
                post_messages.append({
                    # "role": "tool",
                    "role": "user",
                    # "tool_call_id": history_message["toolCallId"],
                    "content": f"Tool execution result: {history_message['content']}"
                })


        # Call LLM
        new_message, token_consumptions, model_time, tool_calls = self.api.chat_with_llm(
            post_messages,
            tools=self._get_tools(),
            model=self.chat_information.get("model", "gpt-4o-mini")
        )
        
        prompt_tokens = token_consumptions.get("prompt_tokens", 0)
        completion_tokens = token_consumptions.get("completion_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens
        
        # Create assistant message
        self.api.create_chat_message(self.chat_id, {
            "chat_id": self.chat_id,
            "content": new_message,
            "tool_calls": json.dumps(tool_calls) if tool_calls else None,
            "role": MessageRole.ASSISTANT,
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": self.chat_information.get("model", "gpt-4o-mini"),
            "model_time": model_time,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens
        })
        
        # Record LLM consumption
        consumption_data = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "model": self.chat_information.get("model", "gpt-4o-mini"),
            "functionality": "Chat",
            "functionality_task_id": self.chat_id,
            "node_id": None
        }
        self.api.record_llm_consumption(consumption_data)
        
        # Update chat status back to normal
        self.api.update_chat_information(self.chat_id, {
            "status": ChatStatus.NORMAL
        })

        self.auto_handle_tool_calls(tool_calls if tool_calls else [])
        
        return True
            
        # except Exception as e:
        #     print(f"Error in call_tool_feedback: {str(e)}")
        #     # Reset status to normal on error
        #     self.api.update_chat_information(self.chat_id, {
        #         "status": ChatStatus.NORMAL,
        #         "updated_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #     })
        #     return False
    
    def _execute_tool(self, tool_name: str, params: Dict[str, Any], chat_sub_task_id: str) -> str:
        """Execute the specific tool based on tool name"""
        tool_methods = {
            "get_analysis_info": self._get_analysis_info,
            "get_current_node_info": self._get_current_node_info,
            "change_current_node": self._change_current_node,
            "get_whole_tree_info": self._get_whole_tree_info,
            "get_whole_branch_info": self._get_whole_branch_info,
            "capture_data": self._capture_data,
            "fix_bug": self._fix_bug,
            "plan_autogenie": self._plan_autogenie,
            "run_autogenie": self._run_autogenie,
            "create_data_node": self._create_data_node,
            "get_computation_details": self._get_computation_details,
            "get_function_block_codes": self._get_function_block_codes,
            "get_available_function_blocks": self._get_available_function_blocks,
            "create_computation_node": self._create_computation_node,
            "create_report": self._create_report,
            "read_file": self._read_file,
            "import_and_process_h5ad_dataset": self._import_and_process_h5ad_dataset,
            "import_and_process_general_input_folder": self._import_and_process_general_input_folder,
            # "choose_autogenie_version": self._choose_autogenie_version,
            # "handle_version_choice_response": self._handle_version_choice_response
        }
        
        if tool_name in tool_methods:
            return tool_methods[tool_name](chat_sub_task_id, params)
        else:
            return f"Unknown tool: {tool_name}"
        
    def _get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "get_analysis_info",
                "type": "function",
                "function":{
                    "name": "get_analysis_info",
                    "description": "Get current analysis information and `all nodes information` and `all edges information` and `all available datas` in it.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "id": "get_current_node_branch",
                "type": "function",
                "function":{
                    "name": "get_current_node_branch",
                    "description": "Get whole branch information of the current analysis, including all nodes and edges from the root node to the current node",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "id": "get_current_node_info",
                "type": "function",
                "function":{
                    "name": "get_current_node_info",
                    "description": "Get current node information",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "id": "change_current_node",
                "type": "function",
                "function":{
                    "name": "change_current_node",
                    "description": "Change current node in the chat context, find the node by node_id and focus on it",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "node_id": {
                                "type": "string",
                                "description": "The ID of the node to change to"
                            }
                        },
                        "required": ["node_id"]
                    }
                }
            },
            {
                "id": "capture_data",
                "type": "function",
                "function":{
                    "name": "capture_data",
                    "description": "Search and discover external datasets outside the current analysis based on user requirements. IMPORTANT: After showing search results, direct users to see the Actions List panel where they can import any of these external datasets into their analysis. The search results contain 'id' fields which are external dataset identifiers and are NOT the same as 'data_id' used in create_data_node. Do not ask users which dataset to import - instead inform them where they can import datasets themselves. You can use get_analysis_info to see available 'data_id' values when completing requests related to create_data_node.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "requirement": {
                                "type": "string",
                                "description": "The requirement of the data to capture"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "id": "plan_autogenie",
                "type": "function",
                "function":{
                    "name": "plan_autogenie",
                    "description": (
                        "Create an automated analysis plan from the current node. This tool generates a detailed execution plan and returns a generation_id for use with run_autogenie. "
                        "Necessarily, the current node must be a finished node or a data node. Use get_current_node_info to check the current node state and type. "
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "generation_request": {
                                "type": "string",
                                "description": "The user's requirement description for what kind of analysis should be planned and generated"
                            },
                            "generation_mode": {
                                "type": "string",
                                "description": "The mode of generation: 'mixed' (recommended default - uses both existing and new function blocks), 'only_existing' (uses only existing function blocks), 'only_new' (creates new function blocks)",
                                "enum": ["mixed", "only_existing", "only_new"],
                            },
                            "max_node": {
                                "type": "integer",
                                "description": "The maximum number of computation nodes to include in the generated analysis plan",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 20
                            }
                        },
                        "required": ["generation_request", "generation_mode", "max_node"]
                    }
                }
            },
            {
                "id": "run_autogenie",
                "type": "function",
                "function": {
                    "name": "run_autogenie",
                    "description": "Execute a previously planned automated analysis. This tool runs an analysis plan created by plan_autogenie using the generation_id returned from that tool. Always use plan_autogenie first to create the plan before using this tool.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "generation_id": {
                                "type": "string",
                                "description": "The generation ID returned from plan_autogenie tool. This is the same as the system_task_id from the plan_autogenie response."
                            }
                        },
                        "required": ["generation_id"]
                    }
                }
            },
            {
                "id": "get_computation_details",
                "type": "function",
                "function":{
                    "name": "get_computation_details",
                    "description": "Get detailed information about the computation process of the pointed node, including function_block_id and function_block_version_id, computation log and parameters.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "node_id": {
                                "type": "string",
                                "description": "The ID of the node to get computation details for."
                            }
                        },
                        "required": ["node_id"]
                    }
                }
            },
            {
                "id": "create_data_node",
                "type": "function",
                "function":{
                    "name": "create_data_node",
                    "description": (
                        "Create a new data node in the current analysis using a valid 'data_id' from the analysis's available datasets. "
                        "IMPORTANT: Only use 'data_id' values that appear in the 'Available Datasets in Analysis' section of the system prompt. "
                        "Do NOT use 'id' values from capture_data results - those are external dataset identifiers that must be imported first. "
                        "Current node will be changed to the newly created data node immediately after successful creation."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data_id": {
                                "type": "string",
                                "description": "The data_id from the 'Available Datasets in Analysis' section in the system prompt (NOT the 'id' field from capture_data results)"
                            }
                        },
                        "required": ["data_id"]
                    }
                }
            },
            {
                "id": "get_function_block_codes",
                "type": "function",
                "function":{
                    "name": "get_function_block_codes",
                    "description": "Get the code and configuration of a function block by function_block_id and function_block_version_id.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_block_id": {
                                "type": "string",
                                "description": "The ID of the function block"
                            },
                            "function_block_version_id": {
                                "type": "string",
                                "description": "The version ID of the function block"
                            }
                        },
                        "required": ["function_block_id", "function_block_version_id"]
                    }
                }
            },
            {
                "id": "get_available_function_blocks",
                "type": "function",
                "function":{
                    "name": "get_available_function_blocks",
                    "description": "Get all available function blocks in the system. These function blocks can be used for analysis to create computation nodes.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "id": "create_computation_node",
                "type": "function",
                "function": {
                    "name": "create_computation_node",
                    "description": "Create a new computation node in the analysis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_block_id": {
                                "type": "string",
                                "description": "The ID of the function block to use for the computation node."
                            },
                            "node_name": {
                                "type": "string",
                                "description": "The name of the computation node."
                            }
                        },
                        "required": ["function_block_id", "node_name"]
                    }
                }
            },
            {
                "id": "create_report",
                "type": "function",
                "function": {
                    "name": "create_report",
                    "description": (
                        "Create a new report for the whole computation pipeline from the frontest data node to the end computation node."
                        "The report will include all nodes and edges in the path from the head data node to the end computation node, along with their outputs and visualizations."
                        "The invoking requires the end_node_id to specify where to end the report and the end node must be a computation node and its `state` must be finished."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "end_node_id": {
                                "type": "string",
                                "description": "The ID of the computation node to end the report at."
                            }
                        },
                        "required": ["end_node_id"]
                    }
                }
            },
            {
                "id": "read_file",
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read and analyze file contents from the chat workspace. Use this tool when attached_file_s3_keys are not null in the message to examine uploaded files.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_key": {
                                "type": "string",
                                "description": "The s3 prefix of the uploaded file to be read and analyzed"
                            }
                        },
                        "required": ["file_key"]
                    }
                }
            },
            {
                "id": "import_and_process_h5ad_dataset",
                "type": "function",
                "function": {
                    "name": "import_and_process_h5ad_dataset",
                    "description": "Call this when user uploads .h5ad files that need processing. This tool imports and processes an uploaded H5AD (AnnData) file into the current analysis. This tool creates a data framework entry, copies the file to the appropriate storage location, renames it with a standardized ID, disassembles it into component parts, and imports it into the current analysis for use in computational workflows.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_key": {
                                "type": "string",
                                "description": "The s3 prefix of the uploaded .h5ad file to be processed and imported"
                            }
                        },
                        "required": ["file_key"]
                    }
                }
            },
            {
                "id": "import_and_process_general_input_folder",
                "type": "function",
                "function": {
                    "name": "import_and_process_general_input_folder",
                    "description": "Call this when user uploads a folder that needs processing. To identify whether user uploaded a folder, check if the attached_file_s3_keys contains no suffix of a typical file. This tool imports and processes a general input folder uploaded to the chat workspace into the current analysis. It creates a data framework entry, copies the entire folder to the appropriate storage location, renames it with a standardized ID, and imports it into the current analysis for use in computational workflows.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_key": {
                                "type": "string",
                                "description": "The s3 prefix of the uploaded folder to be processed and imported"
                            }
                        },
                        "required": ["file_key"]
                    }
                }
            },
            {
                "id": "choose_autogenie_version",
                "type": "function",
                "function": {
                    "name": "choose_autogenie_version",
                    "description": "Ask user to choose between v1 and v2 versions of auto genie. The handle_version_choice_response tool will be called next to process user's choice.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_block_version_id": {
                                "type": "string",
                                "description": "The function block version ID that needs version selection"
                            }
                        },
                        "required": ["function_block_version_id"]
                    }
                }
            },
            {
                "id": "handle_version_choice_response",
                "type": "function",
                "function": {
                    "name": "handle_version_choice_response",
                    "description": "Update the function block version.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_block_version_id": {
                                "type": "string",
                                "description": "The function block version ID to update"
                            },
                            "user_choice": {
                                "type": "string",
                                "description": "The user's choice: 'v1' or 'v2'"
                            }
                        },
                        "required": ["function_block_version_id", "user_choice"]
                    }
                }
            },
        ]
    
    def _get_system_message(self):
        """Get system prompt for LLM"""
        fixed_part = {
            "role": "system", "content":
            (
            "You are an AI assistant in a bioinformatics analysis environment. Your role is to help users analyze their data through interactive conversations and tool usage.\n\n"

            "## Environment Overview:\n"
            "- You operate within a specific analysis environment with a unique analysis ID\n"
            "- The analysis contains computational workflows with nodes and edges\n"
            "- Available resources include public datasets and imported datasets\n\n"

            "## Node Types:\n"
            "1. **Data Nodes**: Contain actual data, identified by 'data_id'\n"
            "2. **Computation Nodes**: Represent computation steps with attributes like function_block_id, function_block_version_id, computation_params\n\n"

            "## Function Blocks:\n"
            "- Reusable computation modules with unique function_block_id and version_id\n"
            "- Each defines specific operations that can be performed on data nodes\n"
            "- Required files: function_block.(py|R|sh) and static-config.json\n"
            "- Optional dependencies: requirements.txt, libs.R, libs.sh, install.sh\n"
            "- Run in Ubuntu 22.04 LTS environment\n\n"

            "## Data Management:\n"
            "- **CRITICAL RULE**: Distinguish between 'id' field from capture_data (external dataset identifiers) and 'data_id' (for create_data_node)\n"
            "- Use capture_data to discover external datasets - results contain 'id' fields that are NOT usable as data_id\n"
            "- **CRITICAL RULE**: Only create data nodes with 'data_id' from the available datasets listed in this system prompt, never with 'id' from capture_data\n"
            "- **NEVER VIOLATE**: Even if user directly requests creating data nodes after capture_data, you MUST NOT use 'id' from capture_data results. Always direct users to import external datasets via the Actions List panel before creating data nodes. Do not ask users which dataset to import.\n"
            "- **WORKFLOW**: capture_data → direct user to see Actions List panel for import → get_analysis_info to check available datasets in system prompt → create_data_node with valid data_id\n"
            "- **AVAILABLE DATA_IDs**: Use only the 'data_id' values from the 'Available Datasets in Analysis' section below in this system prompt for create_data_node tool\n\n"

            "## Analysis Report:\n"
            "- You can create comprehensive reports summarizing the entire analysis pipeline by using the create_report tool\n\n"

            "## Figure Display Format:\n"
            "- To display figures in your responses, use the exact format: [[FIGURE:<figureUuid>]]\n"
            "- figureUuid consists uuid and file extension, e.g., 59d4458423b14a9c9962300e6c9e1ba8.png\n"
            "- **CRITICAL**: The <figureUuid> must be ONLY the `figureUuid` value, no additional characters, spaces, or text\n"

            "## Execution Rules:\n"
            "- **TOOL USAGE**: Execute only ONE tool at a time and wait for results before proceeding to the next tool call\n"
            "- **FILE ATTACHMENTS**: If attached_file_s3_keys are not null and are not .h5ad files, call read_file tool first to examine the content before proceeding with any other actions\n"
            "- Nodes must have input data to be runnable (previous nodes must be finished)\n"
            "- Recommend tools proactively with clear reasoning\n"
            "- Continue tool execution until user needs are fulfilled\n"
            "- **IMPORTANT**: When you need to call tools to fulfill user requests, execute them directly without asking for user confirmation. Act autonomously to gather information and complete tasks.\n"
            "- Handle errors by calling appropriate tools to get updated information\n\n"
            
            "## Analysis Workflow Strategy:\n"
            "- **PRIORITY WORKFLOW**: When user intends to start or perform an analysis, prioritize the `plan_autogenie -> run_autogenie` approach\n"
            "- **PREREQUISITE CHECK**: Before using plan_autogenie, verify current node meets ONE of these conditions:\n"
            "  1. Node type == 'data node' (any state)\n"
            "  2. Node type == 'computation node' AND node state == 'finished'\n"
            "- **NODE PREPARATION WORKFLOW**:\n"
            "  - If current node doesn't meet prerequisites, first call `get_analysis_info` to get all nodes\n"
            "  - Search for the most suitable data node in the analysis and use `change_current_node` to switch to it\n"
            "  - If no data nodes exist, create one using `create_data_node` with available datasets from the analysis\n"
            "  - Then proceed with `plan_autogenie -> run_autogenie`\n"
            "- **EXECUTION SEQUENCE**: plan_autogenie first, then immediately follow with run_autogenie using the returned generation_id\n"
            "- **RESULT DISPLAY**: Show figures in result nodes using format `[[FIGURE:<figureUuid>]]` if ANY figures are generated (where <figureUuid> is ONLY the `figureUuid` value)\n"
        )}

        current_node_info = self.api.get_node_information(self.chat_information.get("currentNodeId")) if self.chat_information.get("currentNodeId") else None
        current_node_info = current_node_info if current_node_info else {}
        avaliable_datas = self.api.get_avaliable_datasets(self.chat_information.get("analysisId")) if self.chat_information.get("analysisId") else {"public-datas": [], "imported-datas": []}

        real_time_info = {
            "role": "system",
            "content": (
                f"## Current Context:\n"
                f"Node ID: {current_node_info.get('id', 'None')}\n"
                f"Node Name: {current_node_info.get('name', 'None')}\n"
                f"Node Type: {current_node_info.get('type', 'None')}\n"
                + (f"Node State: {current_node_info.get('state', 'None')}\n" if current_node_info.get('type') == 'computation node' else "")
                + (f"Data ID: {current_node_info.get('dataId', 'None')}\n" if current_node_info.get('type') == 'data node' else "")
                + "## Available Datasets in Analysis:\n"
                + f"- Public Datasets: {json.dumps(avaliable_datas.get('public-datas', []), indent=2)}\n"
                + f"- Imported Datasets: {json.dumps(avaliable_datas.get('imported-datas', []), indent=2)}\n"
            )
        }
        return [fixed_part, real_time_info]

    def _update_current_node_id(self, new_node_id: str) -> bool:
        """Update current node ID in chat information"""
        try:
            self.api.update_chat_information(self.chat_id, {
                "current_node_id": new_node_id
            })
            self.chat_information["currentNodeId"] = new_node_id
            return True
        except Exception as e:
            print(f"Error updating current node ID: {str(e)}")
            return False

    # Tool implementation methods (to be implemented based on specific requirements)
    def _get_analysis_info(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:
        """Get current analysis information"""
        analysis_id = self.chat_information.get('analysisId')
        analysis_details = self.api.get_analysis_information(analysis_id)
        analysis_details_str = json.dumps(analysis_details, indent=2) if analysis_details else "No details found"
        self.call_tool_feedback(chat_sub_task_id, analysis_details_str)

    def _get_current_node_info(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:
        """Get current node information"""
        current_node_id = self.chat_information.get('currentNodeId')
        if not current_node_id:
            self.call_tool_feedback(chat_sub_task_id, "No current node set in the chat context.")
            return
        current_node_info = self.api.get_node_information(current_node_id)
        current_node_info_str = json.dumps(current_node_info, indent=2) if current_node_info else "No details found"
        self.call_tool_feedback(chat_sub_task_id, current_node_info_str)

    def _change_current_node(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:

        """Change current node in the chat context"""
        new_node_id = params.get("node_id")
        if not new_node_id:
            print("Parameter 'node_id' is required to change current node.")
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": "Parameter 'node_id' is required to change current node.",
                "node_info": None
            }))
            return

        node_info = self.api.get_node_information(new_node_id)
        if not node_info:
            print(f"Node {new_node_id} not found")
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Node {new_node_id} not found",
                "node_info": None
            }))
            return
        if node_info["analysisId"] != self.chat_information.get("analysisId"):
            print(f"Node {new_node_id} does not belong to the current analysis")
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Node {new_node_id} does not belong to the current analysis",
                "node_info": None
            }))
            return
        print(f"Changing current node to {new_node_id}")
        self._update_current_node_id(new_node_id)
        print(f"Current node changed to {new_node_id}")
        
        self.call_tool_feedback(chat_sub_task_id, json.dumps({
            "success": True,
            "message": f"Current node changed to {new_node_id}",
            "node_info": node_info
        }))

    def _get_whole_tree_info(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:
        """Get whole tree information"""
        analysis_id = self.chat_information.get('analysis_id')
        # TODO: Implement actual tree info retrieval
        return f"Tree information for analysis {analysis_id}: [Placeholder - implement with actual tree service]"
    
    def _get_whole_branch_info(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:
        """Get whole branch information"""
        current_node_id = self.chat_information.get('current_node_id')
        # TODO: Implement actual branch info retrieval
        return f"Branch information from node {current_node_id}: [Placeholder - implement with actual branch service]"
    
    def _capture_data(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:
        """Capture data from current node"""
        requirement = params.get("requirement", "Random data capture")
        recommended_result = self.api.get_recommended_datasets(requirement)
        result_str = json.dumps(recommended_result, indent=2) if recommended_result else "[]"
        self.call_tool_feedback(chat_sub_task_id, result_str)
    
    def _fix_bug(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:
        """Fix bug in the analysis"""
        # TODO: Implement actual bug fixing
        system_task_id = None
        self.api.update_chat_sub_task(chat_sub_task_id, {
            "system_task_id": system_task_id
        })
        return "Bug fixing initiated: [Placeholder - implement with actual bug fixing service]"
    
    def _plan_autogenie(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:
        """Run automated analysis"""
        # TODO: Implement actual autogenie functionality
        system_task_id = None
        node_id = self.chat_information.get('currentNodeId')
        if not node_id:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"No current node set in the chat context. You should focus on one node first.",
                "system_task_id": None,
                "dynamic_generation_task": None
            }, indent=2))
            return
        user_request = params.get("generation_request", "classic analysis computation flow")
        generation_mode = params.get("generation_mode", "mixed")
        llm_model = self.chat_information.get("model", "gpt-4o-mini")
        max_node = params.get("max_node", 5)
        plan_result = self.api.plan_auto_genie_task(
            start_node_id=node_id,
            user_request=user_request,
            max_node=max_node,
            generate_mode=generation_mode,
            llm_model=llm_model
        )
        if not plan_result:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": "Failed to create auto-genie task",
                "system_task_id": None,
                "dynamic_generation_task": None
            }, indent=2))
            return
        generation_id = system_task_id = plan_result.get("generation_id")
        self.api.update_chat_sub_task(chat_sub_task_id, {
            "system_task_id": system_task_id
        })
        self.call_tool_feedback(chat_sub_task_id, json.dumps({
            "success": True,
            "message": "Auto-genie task created successfully",
            "system_task_id": system_task_id,
            "plan": plan_result.get("plan"),
            "autogenie_id": generation_id,
        }, indent=2))

    def _run_autogenie(self, chat_sub_task_id: str, params: Dict[str, Any]) -> None:
        """Run the auto-genie system task"""
        generation_id = params.get("generation_id")
        if not generation_id:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": "No generation_id provided. Please use plan_autogenie first to create a plan and get the generation_id.",
                "system_task_id": None,
                "dynamic_generation_task": None
            }, indent=2))
            return
        node_id = self.chat_information.get('currentNodeId')
        if not node_id:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"No current node set in the chat context. You should focus on one node first.",
                "system_task_id": None,
                "dynamic_generation_task": None
            }, indent=2))
            return
        run_result, error_message = self.api.prepare_auto_genie(generation_id, node_id)
        if not run_result:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Failed to run auto-genie task, {error_message}",
                "system_task_id": None,
                "dynamic_generation_task": None
            }, indent=2))
            return
        self.api.update_chat_sub_task(chat_sub_task_id, {
            "system_task_id": generation_id
        })
        run_result, error_message = self.api.run_auto_genie(generation_id)
        if not run_result:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Failed to run auto-genie task, {error_message}",
                "system_task_id": generation_id,
                "dynamic_generation_task": None
            }, indent=2))
            return
        
    def _get_computation_details(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:
        """Get computation details of the current node"""
        node_id = params.get("node_id")
        if not node_id:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": "Parameter 'node_id' is required to get computation details.",
                "computation_details": None
            }, indent=2))
            return
        node_info = self.api.get_node_information(node_id)
        if not node_info:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Node {node_id} not found",
                "computation_details": None
            }, indent=2))
            return
        if node_info["type"] != "computation node" and node_info["type"] != "computation node v2":
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Node {node_id} is not a computation node",
                "computation_details": None
            }, indent=2))
            return
        computation_details = self.api.get_computation_details(node_id)
        self.call_tool_feedback(chat_sub_task_id, json.dumps({
            "success": True,
            "message": f"Computation details for node {node_id} retrieved successfully",
            "computation_details": computation_details
        }, indent=2))

    def _get_function_block_codes(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:
        """Get function block code files of the current node"""
        function_block_id = params.get("function_block_id")
        function_block_version_id = params.get("function_block_version_id")
        if not function_block_id or not function_block_version_id:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": "Parameters 'function_block_id' and 'function_block_version_id' are required to get function block codes.",
                "code_files": None
            }, indent=2))
            return
        code_files = self.api.get_function_block_codes(function_block_id, function_block_version_id)
        if code_files is None:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Function block {function_block_id} version {function_block_version_id} not found",
                "code_files": None
            }, indent=2))
            return
        self.call_tool_feedback(chat_sub_task_id, json.dumps({
            "success": True,
            "message": f"Function block {function_block_id} version {function_block_version_id} code files retrieved successfully",
            "code_files": code_files
        }, indent=2))
        
        
    def _create_data_node(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:
        """Create a new data node"""
        data_id = params.get("data_id")
        if not data_id:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": "Parameter 'data_id' is required to create a data node.",
                "data_node_id": None
            }, indent=2))
            return

        data_info = self.api.get_data_info(data_id)
        if not data_info:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Data node {data_id} not found",
                "data_node_id": None
            }, indent=2))
            return
        
        create_node_success, error, node_info = self.api.create_data_node(self.chat_information.get("analysisId"), data_info["id"], data_info["name"])
        if not create_node_success:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Failed to create data node for data {data_id}, ERROR: {error}",
                "data_node_id": None
            }, indent=2))
            return

        self._update_current_node_id(node_info["id"])

        self.call_tool_feedback(chat_sub_task_id, json.dumps({
            "success": True,
            "message": f"Data node {data_id} retrieved successfully",
            "data_info": data_info,
            "new_data_node_info": node_info
        }, indent=2))

    def _create_computation_node(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:
        """Create a new computation node"""
        current_node_id = self.chat_information.get("currentNodeId")
        current_node_info = self.api.get_node_information(current_node_id) if current_node_id else None
        function_block_id = params.get("function_block_id")
        node_name = params.get("node_name", "Computation Node")

        if not function_block_id:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": "Parameter 'function_block_id' is required to create a computation node.",
                "computation_node_id": None
            }, indent=2))
            return
        
        function_block_info = self.api.get_function_block_information(function_block_id)
        if not function_block_info:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Function block {function_block_id} not found",
                "computation_node_id": None
            }, indent=2))
            return
        
        function_block_version_id = function_block_info.get("currentVersionId")
        
        new_node_x = current_node_info.get("x", 0) + 200 if current_node_info else 0
        new_node_y = current_node_info.get("y", 0) if current_node_info else 0

        create_node_success, error, node_info = self.api.create_computation_node(
            analysis_id=self.chat_information.get("analysisId"),
            function_block_id=function_block_id,
            function_block_version_id=function_block_version_id,
            node_name=node_name,
            x=new_node_x,
            y=new_node_y
        )
        if not create_node_success:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Failed to create computation node, ERROR: {error}",
                "computation_node_id": None
            }, indent=2))
            return
        
        new_edge = self.api.create_edge(self.chat_information.get("analysisId"), current_node_id, node_info["id"]) if current_node_id else None
        if new_edge is None:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Failed to create edge from current node {current_node_id} to new computation node {node_info['id']}",
                "computation_node_id": None
            }, indent=2))
            return

        self._update_current_node_id(node_info["id"])
        self.call_tool_feedback(chat_sub_task_id, json.dumps({
            "success": True,
            "message": f"Computation node created successfully",
            "new_computation_node_info": node_info
        }, indent=2))

    def _get_available_function_blocks(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:
        """Get public function block groups"""
        public_groups = self.api.get_public_function_block_groups()
        if public_groups is None:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": "Failed to retrieve public function block groups",
                "groups": None
            }, indent=2))
            return
        self.call_tool_feedback(chat_sub_task_id, json.dumps({
            "success": True,
            "message": f"Retrieved {len(public_groups)} public function block groups successfully",
            "groups": public_groups
        }, indent=2))

    def _create_report(self, chat_sub_task_id: str, params: Dict[str, Any]) -> bool:
        """Create a report for the current node"""
        try:
            node_id = params.get("end_node_id")
            analysis_id = self.chat_information.get('analysisId')
            if not node_id:
                print(f"No current node set in the chat context. You should focus on one node first.")
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "success": False,
                    "message": f"No current node set in the chat context. You should focus on one node first.",
                    "report_node": None
                }, indent=2))
                return
            node_info = self.api.get_node_information(node_id)
            if not node_info:
                print(f"Node {node_id} not found")
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "success": False,
                    "message": f"Node {node_id} not found",
                    "report_node": None
                }, indent=2))
                return
            if node_info["type"] != "computation node" and node_info["type"] != "computation node v2":
                print(f"Node {node_id} is not a computation node")
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "success": False,
                    "message": f"Node {node_id} is not a computation node, considering a auto genie tool call to analyze the node first",
                    "report_node": None
                }, indent=2))
                return
            if node_info.get("state") != "finished":
                print(f"Node {node_id} is not finished yet")
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "success": False,
                    "message": f"Node {node_id} is not finished yet",
                    "report_node": None
                }, indent=2))
                return

            report_node_x = node_info.get("x", 0) + 200
            report_node_y = node_info.get("y", 0)
            report_name = f"Branch Report Generation"
            create_report_node_success, create_report_node_message, new_report_node = self.api.create_report_node(analysis_id, report_name, report_node_x, report_node_y)
            if not create_report_node_success:
                print(f"Failed to create report node", create_report_node_message)
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "success": False,
                    "message": f"Failed to create report node, {create_report_node_message}",
                    "report_node": None
                }, indent=2))
                return
            
            new_edge = self.api.create_edge(analysis_id, node_id, new_report_node["id"])

            branch_nodes = self.api.get_branch_nodes(node_id)
            if branch_nodes is None:
                print(f"Failed to get branch nodes for node {node_id}")
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "success": False,
                    "message": f"Failed to get branch nodes for node {node_id}",
                    "report_node": None
                }, indent=2))
                return

            create_report_success, create_report_message, report_handler = self.api.create_report(analysis_id=analysis_id, branch_nodes=branch_nodes, report_node=new_report_node, model=self.chat_information.get("model", "gpt-4o-mini"))
            if not create_report_success:
                print(f"Failed to create report for node {node_id}")
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "success": False,
                    "message": f"Failed to create report for node {create_report_message}",
                    "report_node": new_report_node
                }, indent=2))
                return

            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": True,
                "message": f"Report node created successfully",
                "report_handler": {
                    "jobId": report_handler.get("jobId"),
                    "message": report_handler.get("message"),
                    "reportId": report_handler.get("reportId")
                }
            }, indent=2))
            return True
        except Exception as e:
            print(f"Error creating branch report for node {node_id}: {e}")
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Error creating branch report for node {node_id}: {e}",
                "report_node": None
            }, indent=2))
            return False
        
    def _run_node(self, chat_sub_task_id: str, params: Dict[str, Any]) -> bool:
        """Run the current computation node"""
        current_node_id = self.chat_information.get("currentNodeId")
        if not current_node_id:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"No current node set in the chat context. You should focus on one node first.",
                "computation_node_id": None
            }, indent=2))
            return False
        node_info = self.api.get_node_information(current_node_id)
        if not node_info:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Node {current_node_id} not found",
                "computation_node_id": None
            }, indent=2))
            return False
        if node_info["type"] != "computation node" and node_info["type"] != "computation node v2":
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Node {current_node_id} is not a computation node",
                "computation_node_id": None
            }, indent=2))
            return False
        if node_info.get("locked", True) or node_info.get("dynamicGenerationLocked", True):
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Node {current_node_id} is locked or in dynamic generation, cannot run",
                "computation_node_id": None
            }, indent=2))
            return False
        
        branch_path = self.api.get_branch_path(current_node_id, with_self=True)
        if branch_path is None:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Failed to get branch path for node {current_node_id}",
                "computation_node_id": None
            }, indent=2))
            return False

        previous_nodes = branch_path.get("previousNodeList", [])
        previous_edges = branch_path.get("previousEdgeList", [])

        target_2_edge_map = {edge["targetNodeId"]: edge for edge in previous_edges}

        node_map = {node["id"]: node for node in previous_nodes}

        involved_node_id_list = [current_node_id]
        involved_edge_id_list = []

        edge_ptr = target_2_edge_map.get(current_node_id, None)
        runnable = edge_ptr is not None
        while edge_ptr is not None:
            node = node_map.get(edge_ptr["sourceNodeId"], None)
            if node is None:
                runnable = False
                break
            if (node["type"] != "computation node" and node["type"] != "computation node v2") or node.get("state") == "finished":
                break
            involved_node_id_list.append(node["id"])
            involved_edge_id_list.append(edge_ptr["id"])
            edge_ptr = target_2_edge_map.get(node["id"], None)

        if not runnable:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Node {current_node_id} is not runnable, please ensure there is at least one previous finished computation node or data node",
            }, indent=2))
            return False

        success,message,new_task = self.api.launch_computation(self.chat_information.get("analysisId"), involved_node_id_list, involved_edge_id_list)
        if not success:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Failed to launch computation for node {current_node_id}, {message}",
            }, indent=2))
            return False
        self.api.update_chat_sub_task(chat_sub_task_id, {
            "system_task_id": new_task.get("id")
        })
        self.call_tool_feedback(chat_sub_task_id, json.dumps({
            "success": True,
            "message": f"Successfully launched computation for node {current_node_id}",
            "task": new_task,
            "involved_node_list": [node_map[nid] for nid in involved_node_id_list],
            "end_node_id": current_node_id
        }, indent=2))
        return True
    
    def _read_file(self, chat_sub_task_id: str, params: Dict[str, Any]) -> bool:
        print(f"chat_sub_task_id: {chat_sub_task_id}")
        print(f"params: {params}")

        # Step 1: Get file_key from params and validate
        file_key = params.get("file_key")
        if not file_key:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": "Parameter 'file_key' is required to read file contents.",
                "content": None
            }, indent=2))
            return False
        
        if not isinstance(file_key, str) or not file_key.strip():
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": "Parameter 'file_key' must be a non-empty string.",
                "content": None
            }, indent=2))
            return False
        
        # Step 2: Get user request context from recent messages
        user_request = self._get_user_request_context()
        
        # Step 3: Detect file type and call appropriate API
        file_type = self._detect_file_type(file_key)
        
        # Step 4: Handle different file types
        try:
            if file_type == "text":
                raw_content = self._handle_text_file(file_key)
                content = self._analyze_file_content(raw_content, file_type, user_request)
            elif file_type == "image":
                image_content = self._handle_image_file(file_key)
                content = self._analyze_file_content(image_content, file_type, user_request)
            elif file_type == "pdf":
                pdf_content = self._handle_pdf_file(file_key)
                content = self._analyze_file_content(pdf_content, file_type, user_request)
            elif file_type == "notebook":
                raw_content = self._handle_notebook_file(file_key)
                content = self._analyze_file_content(raw_content, file_type, user_request)
            elif file_type == "structured_data":
                raw_content = self._handle_structured_data(file_key)
                content = self._analyze_file_content(raw_content, file_type, user_request)
            elif file_type == "docx":
                raw_content = self._handle_docx_file(file_key)
                content = self._analyze_file_content(raw_content, file_type, user_request)
            else:
                content = "Unknown file type or unsupported file extension"
                
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": True,
                "message": f"File read successfully (file type: {file_type})",
                "content": content,
                "file_type": file_type
            }, indent=2))
            return True
            
        except Exception as e:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Error reading file: {str(e)}",
                "content": None
            }, indent=2))
            return False
    
    def _detect_file_type(self, file_key: str) -> str:
        """Detect file type based on fileName extension"""
        import os
        
        fileName = file_key.split("/")[-1]
        _, ext = os.path.splitext(fileName.lower())
        
        text_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.php', 
            '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.html', '.css', '.scss',
            '.sass', '.less', '.xml', '.sql', '.sh', '.bat', '.ps1', '.r', '.m',
            '.txt', '.md', '.rst', '.log', '.ini', '.cfg', '.conf', '.env'
        }
        
        image_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.svg', 
            '.webp', '.ico', '.eps'
        }
        
        structured_extensions = {
            '.json', '.yaml', '.yml', '.csv', '.tsv', '.toml', '.properties'
        }
        
        if ext == '.pdf':
            return "pdf"
        elif ext in {'.ipynb', '.pynb'}:
            return "notebook"
        elif ext == '.docx':
            return "docx"
        elif ext in text_extensions:
            return "text"
        elif ext in image_extensions:
            return "image"
        elif ext in structured_extensions:
            return "structured_data"
        else:
            return "unknown"
    
    def _handle_text_file(self, file_key: str) -> str:
        """Handle text-based files (source code, config files, etc)"""
        try: 
            analysis_id = self.chat_information.get('analysisId')
            raw_content = self.api.read_file_from_storage(
                file_key=file_key, 
                analysis_id=analysis_id
            )

            if not raw_content:
                return "Error: Could not read file from storage"
        except Exception as e:
            return f"Error reading file: {str(e)}"
        
        try:
            content = raw_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = raw_content.decode('utf-16')
            except UnicodeDecodeError:
                try:
                    content = raw_content.decode('latin1')
                except UnicodeDecodeError:
                    content = raw_content.decode('utf-8', errors='replace')
        
        if len(content) > 10000:
            truncated_content = content[:10000] + f"\n\n[Content truncated. Total size: {len(content)} characters, {content.count(chr(10)) + 1} lines]"
            content = truncated_content
        
        result = content
        
        return result
    
    def _handle_image_file(self, file_key: str):
        """Handle image files by converting to Base64 for LLM analysis"""
        import base64
        try:
            analysis_id = self.chat_information.get('analysisId')
            image_bytes = self.api.read_file_from_storage(
                file_key=file_key, 
                analysis_id=analysis_id
            )

            if not image_bytes:
                return "Error: Could not read image file from storage"

            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            return f"data:image/png;base64,{base64_image}"
            
        except Exception as e:
            return f"Error reading image file: {str(e)}"
    
    def _handle_pdf_file(self, file_key: str) -> str:
        """Handle PDF files by extracting text content"""
        try:
            analysis_id = self.chat_information.get('analysisId')
            pdf_bytes = self.api.read_file_from_storage(
                file_key=file_key, 
                analysis_id=analysis_id
            )

            if not pdf_bytes:
                return "Error: Could not read PDF file from storage"

            try:
                import PyPDF2
                import io
                
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                extracted_text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            extracted_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    except Exception as e:
                        extracted_text += f"\n--- Page {page_num + 1} (extraction failed) ---\n"
                
                if extracted_text.strip():
                    if len(extracted_text) > 15000:
                        extracted_text = extracted_text[:15000] + f"\n\n[Content truncated. Total extracted length: {len(extracted_text)} characters]"
                    return extracted_text
                else:
                    return "PDF appears to be image-based or text extraction failed. Consider using OCR for better results."
                    
            except ImportError:
                try:
                    import pdfplumber
                    import io
                    
                    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                        extracted_text = ""
                        for page_num, page in enumerate(pdf.pages):
                            try:
                                page_text = page.extract_text()
                                if page_text:
                                    extracted_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                            except Exception as e:
                                extracted_text += f"\n--- Page {page_num + 1} (extraction failed) ---\n"
                    
                    if extracted_text.strip():
                        if len(extracted_text) > 15000:
                            extracted_text = extracted_text[:15000] + f"\n\n[Content truncated. Total extracted length: {len(extracted_text)} characters]"
                        return extracted_text
                    else:
                        return "PDF appears to be image-based or text extraction failed."
                        
                except ImportError:
                    return "Error: PDF processing libraries (PyPDF2 or pdfplumber) not available. Please install: pip install PyPDF2 pdfplumber"
                    
        except Exception as e:
            return f"Error processing PDF file: {str(e)}"
    
    def _handle_structured_data(self, file_key: str) -> str:
        """Handle structured data files (JSON, CSV, YAML, XML, TSV, TOML)"""
        import json
        import csv
        import io
        
        try:
            analysis_id = self.chat_information.get('analysisId')
            raw_content = self.api.read_file_from_storage(
                file_key=file_key, 
                analysis_id=analysis_id
            )

            if not raw_content:
                return "Error: Could not read structured data file from storage"
                
            import os
            fileName = file_key.split("/")[-1]
            _, ext = os.path.splitext(fileName.lower())
            try:
                content_str = raw_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content_str = raw_content.decode('utf-16')
                except UnicodeDecodeError:
                    content_str = raw_content.decode('latin1')
            
            parsed_data = None
            parsing_info = ""
            
            if ext == '.json':
                try:
                    parsed_data = json.loads(content_str)
                    parsing_info = f"JSON file parsed successfully. Root type: {type(parsed_data).__name__}"
                    if isinstance(parsed_data, dict):
                        parsing_info += f", {len(parsed_data)} top-level keys"
                    elif isinstance(parsed_data, list):
                        parsing_info += f", {len(parsed_data)} items"
                except json.JSONDecodeError as e:
                    parsing_info = f"JSON parsing failed: {str(e)}"
                    
            elif ext in ['.csv', '.tsv']:
                try:
                    delimiter = ',' if ext == '.csv' else '\t'
                    csv_reader = csv.reader(io.StringIO(content_str), delimiter=delimiter)
                    rows = list(csv_reader)
                    if rows:
                        headers = rows[0] if rows else []
                        data_rows = rows[1:] if len(rows) > 1 else []
                        parsed_data = {
                            "headers": headers,
                            "data": data_rows[:100],
                            "total_rows": len(data_rows),
                            "total_columns": len(headers)
                        }
                        parsing_info = f"{ext.upper()} file parsed successfully. {len(headers)} columns, {len(data_rows)} data rows"
                        if len(data_rows) > 100:
                            parsing_info += " (showing first 100 rows in analysis)"
                    else:
                        parsing_info = "CSV/TSV file appears to be empty"
                except Exception as e:
                    parsing_info = f"CSV/TSV parsing failed: {str(e)}"
                    
            elif ext in ['.yaml', '.yml']:
                try:
                    import yaml
                    parsed_data = yaml.safe_load(content_str)
                    parsing_info = f"YAML file parsed successfully. Root type: {type(parsed_data).__name__}"
                    if isinstance(parsed_data, dict):
                        parsing_info += f", {len(parsed_data)} top-level keys"
                    elif isinstance(parsed_data, list):
                        parsing_info += f", {len(parsed_data)} items"
                except ImportError:
                    parsing_info = "YAML parsing failed: PyYAML library not available. Install with: pip install PyYAML"
                except Exception as e:
                    parsing_info = f"YAML parsing failed: {str(e)}"
                    
            elif ext == '.toml':
                try:
                    import toml
                    parsed_data = toml.loads(content_str)
                    parsing_info = f"TOML file parsed successfully. {len(parsed_data)} top-level sections"
                except ImportError:
                    parsing_info = "TOML parsing failed: toml library not available. Install with: pip install toml"
                except Exception as e:
                    parsing_info = f"TOML parsing failed: {str(e)}"
                    
            elif ext == '.xml':
                try:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(content_str)
                    
                    def xml_to_dict(element):
                        result = {}
                        if element.text and element.text.strip():
                            result['_text'] = element.text.strip()
                        if element.attrib:
                            result['_attributes'] = element.attrib
                        for child in element:
                            child_data = xml_to_dict(child)
                            if child.tag in result:
                                if not isinstance(result[child.tag], list):
                                    result[child.tag] = [result[child.tag]]
                                result[child.tag].append(child_data)
                            else:
                                result[child.tag] = child_data
                        return result
                    
                    parsed_data = {root.tag: xml_to_dict(root)}
                    parsing_info = f"XML file parsed successfully. Root element: {root.tag}"
                except Exception as e:
                    parsing_info = f"XML parsing failed: {str(e)}"
                    
            elif ext == '.properties':
                try:
                    parsed_data = {}
                    for line in content_str.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            parsed_data[key.strip()] = value.strip()
                    parsing_info = f"Properties file parsed successfully. {len(parsed_data)} properties"
                except Exception as e:
                    parsing_info = f"Properties parsing failed: {str(e)}"
            
            if parsed_data is not None:
                if ext in ['.csv', '.tsv']:
                    headers = parsed_data.get('headers', [])
                    data_sample = parsed_data.get('data', [])[:15]  # Show first 15 rows for analysis
                    
                    analysis_content = f"File Type: {ext.upper()}\n"
                    analysis_content += f"Parsing Status: {parsing_info}\n\n"
                    analysis_content += f"Headers ({len(headers)}): {', '.join(headers)}\n\n"
                    analysis_content += "Sample Data (first 15 rows):\n"
                    for i, row in enumerate(data_sample, 1):
                        analysis_content += f"Row {i}: {row}\n"
                    
                    if parsed_data.get('total_rows', 0) > 15:
                        analysis_content += f"\n[Showing 15 of {parsed_data['total_rows']} total data rows]"
                        
                else:
                    try:
                        formatted_data = json.dumps(parsed_data, indent=2, ensure_ascii=False)
                        if len(formatted_data) > 8000:
                            formatted_data = formatted_data[:8000] + "\n\n[Content truncated for analysis]"
                        
                        analysis_content = f"File Type: {ext.upper()}\n"
                        analysis_content += f"Parsing Status: {parsing_info}\n\n"
                        analysis_content += "Structured Content:\n"
                        analysis_content += formatted_data
                    except Exception as e:
                        analysis_content = f"File Type: {ext.upper()}\n"
                        analysis_content += f"Parsing Status: {parsing_info}\n"
                        analysis_content += f"Data representation error: {str(e)}\n"
                        analysis_content += f"Raw content preview:\n{content_str[:2000]}"
            else:
                # Fallback to raw content if parsing failed
                analysis_content = f"File Type: {ext.upper()}\n"
                analysis_content += f"Parsing Status: {parsing_info}\n\n"
                analysis_content += f"Raw Content Preview:\n{content_str[:3000]}"
                if len(content_str) > 3000:
                    analysis_content += "\n\n[Content truncated]"
            
            return analysis_content
            
        except Exception as e:
            return f"Error processing structured data file: {str(e)}"
        
    def _handle_docx_file(self, file_key: str) -> str:
        """Handle Microsoft Word .docx files"""
        import io
        
        try:
            analysis_id = self.chat_information.get('analysisId')
            binary_content = self.api.read_file_from_storage(
                file_key=file_key, 
                analysis_id=analysis_id
            )

            if not binary_content:
                return "Error: Could not read DOCX file from storage"
                
            extracted_text = ""
            
            try:
                import docx
                
                doc = docx.Document(io.BytesIO(binary_content))
                
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        extracted_text += paragraph.text + "\n"
                
                for table in doc.tables:
                    extracted_text += "\n--- Table ---\n"
                    for row in table.rows:
                        row_text = " | ".join([cell.text.strip() for cell in row.cells])
                        if row_text.strip():
                            extracted_text += row_text + "\n"
                    extracted_text += "--- End Table ---\n\n"
                
                if extracted_text.strip():
                    if len(extracted_text) > 15000:
                        extracted_text = extracted_text[:15000] + f"\n\n[Content truncated. Total extracted length: {len(extracted_text)} characters]"
                    return extracted_text
                else:
                    return "DOCX file appears to be empty or text extraction failed."
                    
            except ImportError:
                return "Error: python-docx library not available. Please install: pip install python-docx"
            except Exception as e:
                return f"Error extracting text from DOCX: {str(e)}"
                
        except Exception as e:
            return f"Error processing DOCX file: {str(e)}"
        
    
    def _handle_notebook_file(self, file_key: str) -> str:
        """Handle Jupyter notebook .ipynb files"""
        import json

        try:
            analysis_id = self.chat_information.get('analysisId')
            raw_content = self.api.read_file_from_storage(
                file_key=file_key, 
                analysis_id=analysis_id
            )

            if not raw_content:
                return "Error: Could not read notebook file from storage"

            try:
                content_str = raw_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content_str = raw_content.decode('utf-16')
                except UnicodeDecodeError:
                    content_str = raw_content.decode('latin1')

            try:
                notebook = json.loads(content_str)
            except json.JSONDecodeError as e:
                return f"Error: Invalid notebook JSON format - {str(e)}"

            if not isinstance(notebook, dict) or 'cells' not in notebook:
                return "Error: Invalid notebook structure - missing 'cells' field"

            cells = notebook.get('cells', [])
            metadata = notebook.get('metadata', {})
            nbformat = notebook.get('nbformat', 'unknown')

            analysis_content = f"Jupyter Notebook Analysis\n"
            analysis_content += f"========================\n"
            analysis_content += f"Format Version: {nbformat}\n"
            analysis_content += f"Total Cells: {len(cells)}\n"

            kernel_info = metadata.get('kernelspec', {})
            if kernel_info:
                analysis_content += f"Kernel: {kernel_info.get('display_name', 'Unknown')} ({kernel_info.get('language', 'unknown')})\n"

            analysis_content += "\n"

            code_cells = sum(1 for cell in cells if cell.get('cell_type') == 'code')
            markdown_cells = sum(1 for cell in cells if cell.get('cell_type') == 'markdown')
            raw_cells = sum(1 for cell in cells if cell.get('cell_type') == 'raw')

            analysis_content += f"Cell Distribution:\n"
            analysis_content += f"- Code cells: {code_cells}\n"
            analysis_content += f"- Markdown cells: {markdown_cells}\n"
            analysis_content += f"- Raw cells: {raw_cells}\n\n"

            analysis_content += "Cell Contents:\n"
            analysis_content += "==============\n\n"

            for i, cell in enumerate(cells, 1):
                cell_type = cell.get('cell_type', 'unknown')
                source = cell.get('source', [])

                if isinstance(source, list):
                    source_text = ''.join(source)
                else:
                    source_text = str(source)

                analysis_content += f"Cell {i} ({cell_type.upper()}):\n"
                analysis_content += "-" * 30 + "\n"

                if source_text.strip():
                    if len(source_text) > 1000:
                        analysis_content += source_text[:1000] + f"\n\n[Cell content truncated - {len(source_text)} total characters]\n"
                    else:
                        analysis_content += source_text + "\n"
                else:
                    analysis_content += "[Empty cell]\n"

                if cell_type == 'code' and 'outputs' in cell:
                    outputs = cell.get('outputs', [])
                    if outputs:
                        analysis_content += "\nOutputs:\n"
                        for j, output in enumerate(outputs):
                            output_type = output.get('output_type', 'unknown')
                            analysis_content += f"  Output {j+1} ({output_type}): "

                            if output_type == 'stream':
                                stream_text = ''.join(output.get('text', []))
                                if len(stream_text) > 200:
                                    analysis_content += stream_text[:200] + "...\n"
                                else:
                                    analysis_content += stream_text + "\n"
                            elif output_type in ['execute_result', 'display_data']:
                                data = output.get('data', {})
                                if 'text/plain' in data:
                                    plain_text = ''.join(data['text/plain'])
                                    if len(plain_text) > 200:
                                        analysis_content += plain_text[:200] + "...\n"
                                    else:
                                        analysis_content += plain_text + "\n"
                                elif 'image/png' in data:
                                    analysis_content += "[PNG Image Output]\n"
                                elif 'text/html' in data:
                                    analysis_content += "[HTML Output]\n"
                                else:
                                    analysis_content += f"[{', '.join(data.keys())} Output]\n"
                            elif output_type == 'error':
                                error_name = output.get('ename', 'Error')
                                error_value = output.get('evalue', '')
                                analysis_content += f"{error_name}: {error_value}\n"
                            else:
                                analysis_content += "[Unknown output type]\n"
                        analysis_content += "\n"

                if cell_type == 'code' and 'execution_count' in cell:
                    exec_count = cell.get('execution_count')
                    if exec_count is not None:
                        analysis_content += f"Execution count: {exec_count}\n"

                analysis_content += "\n"

                if len(analysis_content) > 15000:
                    analysis_content += f"\n[Notebook analysis truncated - showing first {i} of {len(cells)} cells]\n"
                    break

            return analysis_content

        except Exception as e:
            return f"Error processing notebook file: {str(e)}"
        
    def _analyze_file_content(self, content: str, file_type: str, user_request: str = None) -> str:
        """Analyze file content based on user request using LLM"""
        analysis_prompt = f"Please analyze the following {file_type} file"
        
        if user_request:
            analysis_prompt += f" based on this user request: '{user_request}'"
        else:
            analysis_prompt += " and provide a comprehensive analysis"
            
        analysis_prompt += "\n\nPlease provide:\n"
        analysis_prompt += "1. A concise summary of the file\n"
        analysis_prompt += "2. Key findings or important elements\n"
        analysis_prompt += "3. Any relevant insights based on the user's request\n"
        analysis_prompt += "4. Suggestions or recommendations if applicable"
        
        try:
            if file_type == "image" and content.startswith("data:image/"):
                messages = [{
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": analysis_prompt},
                        {"type": "image_url", "image_url": {"url": content}}
                    ]
                }]
            else:
                analysis_prompt += f"\n\nFile content:\n{content}\n\n"
                messages = [{"role": "user", "content": analysis_prompt}]
                
            analysis_result, token_consumptions, model_time, tool_calls = self.api.chat_with_llm(
                messages,
                tools=[],
                model=self.chat_information.get("model", "gpt-4o-mini")
            )
            
            # Record LLM consumption
            prompt_tokens = token_consumptions.get("prompt_tokens", 0)
            completion_tokens = token_consumptions.get("completion_tokens", 0)
            total_tokens = prompt_tokens + completion_tokens
            consumption_data = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "model": self.chat_information.get("model", "gpt-4o-mini"),
                "functionality": "Chat",
                "functionality_task_id": self.chat_id,
                "node_id": None
            }
            self.api.record_llm_consumption(consumption_data)
            
            return analysis_result
        except Exception as e:
            if file_type == "image":
                return f"Analysis failed ({str(e)}). Image file processed."
            else:
                return f"Analysis failed ({str(e)}). Raw content:\n{content}"
    
    def _get_user_request_context(self) -> str:
        """Get the most recent user message to understand the request context"""
        try:
            all_messages = self.api.get_chat_messages(self.chat_id)
            
            for message in reversed(all_messages):
                if message.get("role") == MessageRole.USER:
                    user_content = message.get("content", "")
                    if user_content and user_content.strip():
                        return user_content.strip()
            
            return None
        except Exception as e:
            print(f"Error getting user request context: {str(e)}")
            return None
        
    def _import_and_process_h5ad_dataset(self, chat_sub_task_id: str, params: Dict[str, Any]) -> bool:
        # Step 1: Get file_key from params and validate
        file_key = params.get("file_key")
        if not file_key:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "status": "error",
                "message": "Parameter 'file_key' is required to preprocess h5ad file.",
                "data_frame_id": None
            }, indent=2))
            return False
        
        if not isinstance(file_key, str) or not file_key.strip():
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "status": "error",
                "message": "Parameter 'file_key' must be a non-empty string.",
                "data_frame_id": None
            }, indent=2))
            return False

        try:
            # Step 2: Create data frame entry
            file_name = file_key.split("/")[-1]
            data_from = "from uploaded directly"
            upload_type = "anndata"
            species = "Other species"
            description = "User Uploaded AnnData (h5ad) file"

            framework_result = self.api.create_data_framework(
                name=file_name,
                data_from=data_from,
                upload_type=upload_type,
                species=species,
                description=description
            )
            
            if not framework_result:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "Failed to create data framework for h5ad file",
                    "data_frame_id": None
                }, indent=2))
                return False
            
            data_frame_id = framework_result.get('id')
            if not data_frame_id:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "Data framework created but no ID returned",
                    "data_frame_id": None
                }, indent=2))
                return False

            # Step 3: Copy existing h5ad file to adata folder
            analysis_id = self.chat_information.get('analysisId')
            original_file_name = file_name
            workspace_prefix = f"v3-chat-workspace/{analysis_id}/" if analysis_id else ''
            file_copy_source_key = f"{workspace_prefix}{file_name}"
            file_copy_dest_key = f"adata/"
            copy_success, copied_destination_key = self.api.copy_files_between_s3_folders(
                file_name=original_file_name,
                source_key=file_copy_source_key,
                destination_key=file_copy_dest_key,
            )
            
            if not copy_success:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "Failed to copy file to adata folder",
                    "data_frame_id": data_frame_id
                }, indent=2))
                return False
            
            # Step 4: Rename the copied file with data_frame_id
            file_rename_source_key = copied_destination_key
            file_rename_new_name = f"{data_frame_id}.h5ad"
            
            rename_success = self.api.rename_file_in_s3_storage(
                source_key=file_rename_source_key,
                new_name=file_rename_new_name
            )

            if not rename_success:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "Failed to rename copied file",
                    "data_frame_id": data_frame_id
                }, indent=2))
                return False

            # Step 5: assemble user's file into components
            self.api.assemble_data_components(data_frame_id=data_frame_id)
            import time
            max_wait_time = 300
            wait_interval = 20
            elapsed_time = 0
            disassembled_folder_key = f"adata/{data_frame_id}-disassemble/"
            disassemble_success = False
            while elapsed_time < max_wait_time:
                time.sleep(wait_interval)
                elapsed_time += wait_interval
                if self.api.check_folder_exist_in_s3_storage(folder_key=disassembled_folder_key):
                    disassemble_success = True
                    break

            if not disassemble_success:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "Failed to disassemble h5ad file into components within expected time",
                    "data_frame_id": data_frame_id
                }, indent=2))
                return False
            
            # Step 6: Import asssembled dataset into a specific analysis
            analysis_id = self.chat_information.get('analysisId')
            if not analysis_id:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "No analysisId found in chat information",
                    "data_frame_id": data_frame_id
                }, indent=2))
                return False
            import_success = self.api.import_data_to_analysis(
                analysis_id=analysis_id,
                data_ids=[data_frame_id]
            )

            if not import_success:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "Failed to import h5ad data into analysis",
                    "data_frame_id": data_frame_id
                }, indent=2))
                return False
            
            # Step 7: Verify that the import was successful by checking imported data list
            import time
            max_wait_time = 30
            wait_interval = 5
            elapsed_time = 0
            data_confirmed = False
            while elapsed_time < max_wait_time:
                time.sleep(wait_interval)
                elapsed_time += wait_interval
                imported_data = self.api.get_available_imported_datasets(analysis_id=analysis_id)
                if any(d.get('id') == data_frame_id for d in imported_data):
                    data_confirmed = True
                    break

            if not data_confirmed:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "h5ad data not found in analysis after import",
                    "data_frame_id": data_frame_id
                }, indent=2))
                return False
            
            # Step 8: Create data node using the data frame id
            data_node = self.api.create_data_node(
                analysis_id=analysis_id,
                data_id=data_frame_id,
                node_name=file_name
            )
            if not data_node:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "Failed to create data node for h5ad data",
                    "data_frame_id": data_frame_id
                }, indent=2))
                return False

            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "status": "success",
                "message": "h5ad file preprocessed and imported successfully",
                "data_frame_id": data_frame_id
            }, indent=2))
            return True
        
        except Exception as e:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "status": "error",
                "message": f"Error preprocessing h5ad file: {str(e)}",
                "data_frame_id": None
            }, indent=2))
            return False
        
    def _import_and_process_general_input_folder(self, chat_sub_task_id: str, params: Dict[str, Any]) -> bool:
        # Step 1: Get file_key from params and validate
        file_key = params.get("file_key")
        if not file_key:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "status": "error",
                "message": "Parameter 'file_key' is required to preprocess input folder.",
                "data_frame_id": None
            }, indent=2))
            return False
        
        if not isinstance(file_key, str) or not file_key.strip():
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "status": "error",
                "message": "Parameter 'file_key' must be a non-empty string.",
                "data_frame_id": None
            }, indent=2))
            return False

        try:
            # Step 2: Create data frame entry
            folder_name = file_key.split("/")[-1]
            data_from = "from uploaded directly"
            upload_type = "general"
            species = "Other species"
            description = "User Uploaded General Input Folder"

            framework_result = self.api.create_data_framework(
                name=folder_name,
                data_from=data_from,
                upload_type=upload_type,
                species=species,
                description=description
            )

            if not framework_result:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "Failed to create data framework for input folder",
                    "data_frame_id": None
                }, indent=2))
                return False
            
            data_frame_id = framework_result.get('id')
            if not data_frame_id:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "Data framework created but no ID returned",
                    "data_frame_id": None
                }, indent=2))
                return False
            
            # Step 3: Loop to copy existing files in the folder to new folder and rename
            analysis_id = self.chat_information.get('analysisId')

            if not analysis_id:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "No analysisId found in chat information",
                    "data_frame_id": data_frame_id
                }, indent=2))
                return False
            
            file_list = self.api.list_files(
                prefix=file_key,
                analysis_id=analysis_id
            )

            if not file_list:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "No files found in the specified input folder",
                    "data_frame_id": data_frame_id
                }, indent=2))
                return False
        
            for file in file_list:
                file_key = file["id"]
                file_name = file["name"]
                file_copy_dest_key = f"adata/"
                copy_success, copied_destination_key = self.api.copy_files_between_s3_folders(
                    file_name=file_name,
                    source_key=file_key,
                    destination_key=file_copy_dest_key
                )
                file_rename_source_key = copied_destination_key
                file_rename_new_name = f"{data_frame_id}-general-s3-store/{file_name}"

                rename_success = self.api.rename_file_in_s3_storage(
                    source_key=file_rename_source_key,
                    new_name=file_rename_new_name
                )

                if not copy_success or not rename_success:
                    self.call_tool_feedback(chat_sub_task_id, json.dumps({
                        "status": "error",
                        "message": f"Failed to copy/rename file '{file_name}' in input folder",
                        "data_frame_id": data_frame_id
                    }, indent=2))
                    return False
                
            # Step 4: assemble user's folder into components
            self.api.assemble_data_components(data_frame_id=data_frame_id)
            import time
            wait_time = 120
            time.sleep(wait_time)

            # Step 5: Import asssembled dataset into a specific analysis           
            import_success = self.api.import_data_to_analysis(
                analysis_id=analysis_id,
                data_ids=[data_frame_id]
            )

            if not import_success:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "Failed to import input folder data into analysis",
                    "data_frame_id": data_frame_id
                }, indent=2))
                return False
            
            # Step 6: Verify that the import was successful by checking imported data list
            import time
            max_wait_time = 30
            wait_interval = 5
            elapsed_time = 0
            data_confirmed = False
            while elapsed_time < max_wait_time:
                time.sleep(wait_interval)
                elapsed_time += wait_interval
                imported_data = self.api.get_available_imported_datasets(analysis_id=analysis_id)
                if any(d.get('id') == data_frame_id for d in imported_data):
                    data_confirmed = True
                    break

            if not data_confirmed:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "Input folder data not found in analysis after import",
                    "data_frame_id": data_frame_id
                }, indent=2))
                return False
            
            # Step 7: Create data node using the data frame id
            data_node = self.api.create_data_node(
                analysis_id=analysis_id,
                data_id=data_frame_id,
                node_name=folder_name
            )

            if not data_node:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "status": "error",
                    "message": "Failed to create data node for input folder data",
                    "data_frame_id": data_frame_id
                }, indent=2))
                return False
            
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "status": "success",
                "message": "Input folder preprocessed and imported successfully",
                "data_frame_id": data_frame_id
            }, indent=2))
            return True
        
        except Exception as e:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "status": "error",
                "message": f"Error preprocessing input folder: {str(e)}",
                "data_frame_id": None
            }, indent=2))
            return False

    def _choose_autogenie_version(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:
        """Ask user to choose auto genie version and handle the response"""
        function_block_version_id = params.get("function_block_version_id")
        
        if not function_block_version_id:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": "function_block_version_id is required",
                "awaiting_user_input": False
            }, indent=2))
            return
        
        version_choice_message = {
            "success": True,
            "message": "Which version of auto genie would you like to use? Please reply with 'v1' or 'v2':",
            "options": ["v1", "v2"],
            "function_block_version_id": function_block_version_id,
            "awaiting_user_input": True,
            "input_type": "version_choice"
        }
        
        self.call_tool_feedback(chat_sub_task_id, json.dumps(version_choice_message, indent=2))

    def _handle_version_choice_response(self, chat_sub_task_id: str, params: Dict[str, Any]) -> str:
        """Handle user's version choice response"""
        function_block_version_id = params.get("function_block_version_id")
        user_choice = params.get("user_choice")
        
        if not function_block_version_id or not user_choice:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": "Both function_block_version_id and user_choice are required",
                "version": None
            }, indent=2))
            return
        
        user_choice = user_choice.lower().strip()
        
        if user_choice == "v1":
            success = self.api.update_function_block_version_is_v2(function_block_version_id, False)
            if success:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "success": True,
                    "message": "Successfully set auto genie version to v1",
                    "version": "v1",
                    "function_block_version_id": function_block_version_id,
                    "is_v2": False
                }, indent=2))
            else:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "success": False,
                    "message": "Failed to update version to v1",
                    "version": None
                }, indent=2))
                
        elif user_choice == "v2":
            success = self.api.update_function_block_version_is_v2(function_block_version_id, True)
            if success:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "success": True,
                    "message": "Successfully set auto genie version to v2",
                    "version": "v2", 
                    "function_block_version_id": function_block_version_id,
                    "is_v2": True
                }, indent=2))
            else:
                self.call_tool_feedback(chat_sub_task_id, json.dumps({
                    "success": False,
                    "message": "Failed to update version to v2",
                    "version": None
                }, indent=2))
        else:
            self.call_tool_feedback(chat_sub_task_id, json.dumps({
                "success": False,
                "message": f"Invalid choice: '{user_choice}'. Please choose 'v1' or 'v2'",
                "version": None
            }, indent=2))
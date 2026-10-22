# Chat Agent Module Design

## System Architecture

The system consists of three main parts:
- **Frontend**: displays chat messages and the UI for triggering tool calls
- **Backend**: the chat agent maintains message state and calls system APIs
- **LLM gateway server**: forwards messages to the LLM and records token consumption and model time

## Database Schema

### chat table
```sql
chat(
    id,                 -- chat ID
    name,              -- chat name
    analysis_id,       -- analysis ID
    current_node_id,   -- current node ID
    model,             -- model in use
    status,            -- chat status
    created_time,      -- creation time
    updated_time       -- update time
)
```

### chat_message table
```sql
chat_message(
    id,                 -- message ID
    role,              -- message role
    chat_id,           -- chat ID (foreign key)
    tool_calls,        -- tool call information
    content,           -- message content
    created_time,      -- creation time
    model,             -- model in use
    model_time,        -- model response time
    prompt_tokens,     -- number of prompt tokens
    completion_tokens  -- number of completion tokens
)
```

### chat_sub_task table
```sql
chat_sub_task(
    id,                -- sub-task ID
    chat_id,           -- chat ID (foreign key)
    chat_message_id,   -- message ID (foreign key)
    tool_name,         -- tool name
    tool_params,       -- tool parameters
    system_task_id,    -- system task ID
    outputs,           -- output results
    status,            -- task status
    created_time,      -- creation time
    start_time,        -- start time
    end_time           -- end time
)
```

## Frontend Chat Synchronization Strategy

The frontend polls the backend with `/v3.0/chat/heartbeat` requests; if `updated_time` has changed, it calls the chat information endpoints to load the latest chat state, including:
- syncing messages
- syncing chat.status, etc.

## Core Enumerations

### ChatSubTaskStatus
- `running`: running
- `finished`: finished
- `failed`: execution failed

### ChatStatus
- `normal`: normal state
- `executing`: a sub-task is being executed
- `responsing`: a reply is being generated (to be decided)

### Role
- `user`: user text
- `tool`: call_tool record
- `assistant`: LLM answer

## Repository URL Mapping

| Service | URL Prefix |
|-----------|------------|
| backend API (`backend/`) | MAIN_SERVER_PREFIX |
| computation worker (`worker/`) | COMPUTATION_SERVER_PREFIX |
| data service | DATA_SERVER_PREFIX |
| LLM gateway service | GPT_SERVER_PREFIX |

## Existing Exposed APIs

### backend API
- `{MAIN_SERVER_PREFIX}/analysis/get-info?analysis_id={analysis_id}`

## Server API Design

### New backend API Endpoints

#### Frontend-facing Endpoints
- `/v3.0/chat/create`
- `/v3.0/chat/send-message`
- `/v3.0/chat/call-tool`
- `/v3.0/chat/heartbeat`
- `/v3.0/chat/delete`
- `/v3.0/chat/update` (currently only the model attribute may be updated)

#### Endpoints for the Frontend and the ChatAgent
- `/v3.0/chat/get-information`
- `/v3.0/chat/get-messages`
- `/v3.0/chat/update-chat-information`

#### ChatAgent-facing Endpoints
- `/v3.0/chat/create-chat-sub-task`
- `/v3.0/chat/update-chat-sub-task`
- `/v3.0/chat/create-message`
- `/v3.0/chat/update-message`

### New LLM gateway service Endpoints

#### ChatAgent-facing Endpoints
- `/v3.0/chat`

## ServerAgent Utility Class

```python
class ServerAPIInvoker:
    @staticmethod
    def get_chat_information(chat_id):
        # TODO: request http://{MAIN_SERVER}/v3.0/chat/get-information?chat_id={chat_id} to get basic information
        return chat_information

    @staticmethod
    def update_chat_information(chat_id, updated_chat_attrs):
        # TODO: request http://{MAIN_SERVER}/v3.0/chat/update-information?chat_id={chat_id} to update chat_information | json: updated_chat_attrs
        return True

    @staticmethod
    def get_chat_messages(chat_id):
        # TODO: request http://{MAIN_SERVER}/v3.0/chat/get-messages?chat_id={chat_id} to get the conversation history
        return chat_history_messages

    @staticmethod
    def create_chat_message(chat_id, new_message):
        # TODO: request http://{MAIN_SERVER}/v3.0/chat/create-message?chat_id={chat_id} to create a new message, json: message
        return new_chat_message

    @staticmethod
    def update_chat_message(chat_message_id, updated_message_attrs):
        # TODO: request http://{MAIN_SERVER}/v3.0/chat/update-message?chat_message_id={chat_message_id} to update the message content, json: updated_message_attrs

    @staticmethod
    def create_chat_sub_task(chat_id, chat_sub_task_attrs):
        # TODO: request http://{MAIN_SERVER}/v3.0/chat/create-chat-sub-task?chat_id={chat_id} to create a new sub-task, json: chat_sub_task_attrs
        return new_chat_sub_task
    
    @staticmethod
    def update_chat_sub_task(chat_sub_task_id, updated_chat_sub_task_attrs):
        # TODO: request http://{MAIN_SERVER}/v3.0/chat/update-chat-sub-task?chat_id={chat_id} to update sub-task information, json: chat_sub_task_attrs
        return True

    @staticmethod
    def get_chat_sub_task(chat_sub_task_id):
        # TODO: request http://{MAIN_SERVER}/v3.0/chat/get-chat-sub-task?chat_sub_task_id={chat_sub_task_id} to get sub-task information
        return chat_sub_task

    @staticmethod
    def chat_with_llm(post_messages, tools, model="gpt-4o-mini"):
        # TODO: request http://{LLM_TRANSFER_SERVER}/v3.0/chat, json: messages
        return new_message, token_consumptions, model_time, tool_calls
```

## ChatAgent Framework Design

```python
class ChatAgent:
    def __init__(self, chat_id, user_id):
        self.chat_id = chat_id
        self.user_id = user_id
        self.chat_information = ServerAPIInvoker.get_chat_information(chat_id)

    def init(self):
        pass

    def send_message(self, message):
        # Create the user message
        ServerAPIInvoker.create_chat_message(self.chat_id, {
            "chat_id": self.chat_id,
            "content": new_message,
            "role": "user",
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": None,
            "model_time": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0
        })
        
        # Set chat status to responding
        ServerAPIInvoker.update_chat_information(self.chat_id, {
            "status": ChatStatus.RESPONSING.value,
            "updated_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Get history messages and send them to the LLM
        history_messages = ServerAPIInvoker.get_history_messages(chat_id)
        post_history_messages = [{"role": history_message["role"], "content": history_message["content"]} for history_message in history_messages]
        new_message, token_consumptions, model_time, tool_calls = ServerAPIInvoker.chat_with_llm(post_messages, [], model=self.chat_information["model"])
        
        # Save the LLM reply
        ServerAPIInvoker.create_chat_message(self.chat_id, {
            "chat_id": self.chat_id,
            "content": new_message,
            "tool_calls": json.dumps(tool_calls),
            "role": "assistant",
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": self.chat_information["model"],
            "model_time": model_time,
            "prompt_tokens": token_consumptions["prompt_tokens"],
            "completion_tokens": token_consumptions["completion_tokens"]
        })
        
        # Set chat status back to normal
        ServerAPIInvoker.update_chat_information(self.chat_id, {
            "status": ChatStatus.NORMAL.value,
            "updated_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    def call_tool(self, tool_name, tool_params):
        # Create the tool call message
        chat_message = ServerAPIInvoker.create_chat_message(self.chat_id, {
            "chat_id": self.chat_id,
            "content": new_message,
            "role": "tool",
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": None,
            "model_time": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0
        })
        
        # Create the sub-task
        chat_sub_task = ServerAPIInvoker.create_chat_sub_task(self.chat_id, {
            "chat_id": self.chat_id, 
            "chat_message_id": chat_message["id"], 
            "tool_name": tool_name, 
            "tool_params": json.dumps(tool_params), 
            "system_task_id": None, 
            "output": None, 
            "status": ChatSubTaskStatus.RUNNING.value, 
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            "end_time": None
        })
        
        # Set chat status to executing
        ServerAPIInvoker.update_chat_information(self.chat_id, {
            "status": ChatStatus.EXECUTING.value,
            "updated_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # TODO: dispatch the task to the corresponding tool function based on tool_name
        # TODO: if available, obtain system_task_id, i.e. the unique identifier of a long-running task such as dynamic_generation_id or retry_process_id
        # TODO: and update: ServerAPIInvoker.update_chat_sub_task(chat_sub_task["id"], {"system_task_id": system_task_id})

    def call_tool_feedback(self, chat_sub_task_id, output):
        # Get the sub-task information and update the message content
        chat_sub_task = ServerAPIInvoker.get_chat_sub_task(chat_sub_task_id)
        ServerAPIInvoker.update_chat_message(self.chat_id, {
            "content": chat_sub_task["output"]
        })
        
        # Set chat status to responding
        ServerAPIInvoker.update_chat_information(self.chat_id, {
            "status": ChatStatus.RESPONSING.value,
            "updated_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Get history messages and send them to the LLM
        history_messages = ServerAPIInvoker.get_history_messages(chat_id)
        post_history_messages = [{"role": history_message["role"], "content": history_message["content"]} for history_message in history_messages]
        new_message, token_consumptions, model_time, tool_calls = ServerAPIInvoker.chat_with_llm(post_messages, [], model=self.chat_information["model"])
        
        # Save the LLM reply
        ServerAPIInvoker.create_chat_message(self.chat_id, {
            "chat_id": self.chat_id,
            "content": new_message,
            "tool_calls": json.dumps(tool_calls),
            "role": "assistant",
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": self.chat_information["model"],
            "model_time": model_time,
            "prompt_tokens": token_consumptions["prompt_tokens"],
            "completion_tokens": token_consumptions["completion_tokens"]
        })
        
        # Set chat status back to normal
        ServerAPIInvoker.update_chat_information(self.chat_id, {
            "status": ChatStatus.NORMAL.value,
            "updated_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    # Tool functions - to be implemented
    def _get_analysis_info(self, chat_sub_task_id, params):
        pass

    def _get_current_node_info(self, chat_sub_task_id, params):
        pass

    def _get_whole_tree_info(self, chat_sub_task_id, params):
        pass
    
    def _get_whole_branch_info(self, chat_sub_task_id, params):
        pass
    
    def _get_dataset_list(self, chat_sub_task_id, params):
        pass

    def _capture_data(self, chat_sub_task_id, params):
        pass

    def _autogenie(self, chat_sub_task_id, params):
        pass

    def _fix_bug(self, chat_sub_task_id, params):
        pass
```

## Core Module Workflows

### 1. Creating a New Chat
1. The user clicks the create button in the frontend, which calls the backend `/v3.0/chat/create` endpoint with the parameters `analysis_id` and `current_node_id` (optional)
2. The `/v3.0/chat/create` endpoint uses `datetime.now()` to obtain `created_time` and `updated_time`, sets `name` to `Analysis-{analysis_id}`, sets `current_node_id` to `None` if absent, sets `status` to `"normal"` and `model` to `"gpt-4o-mini"`, then creates a chat database entity with these attributes and inserts it into the database
3. It calls `chat_agent = ChatAgent(chat.id)` + `chat_agent.init()` to initialize the chat; the init function can be a `pass` placeholder for now
4. The chat information is returned to the frontend
5. The frontend initializes the chat UI with the chat information

### 2. User Sends a Message
1. The user types a new message in the input box and clicks send; the send button and input box then show a pending/disabled state, the message is pushed into the conversation view, and the frontend calls `/v3.0/chat/send-message?chat_id={chat_id}` with method=POST and the JSON request parameter `message`
2. With the chat.id, the backend calls `chat_agent = ChatAgent(chat.id)` + `chat_agent.send_message(message)`
3. `chat_agent.send_message` first updates the chat status, then saves new_message, then fetches the history messages and sends them to the LLM gateway server
4. The LLM gateway server calls chat_completion and returns the LLM reply + tool calls + model time + token consumption
5. After receiving the LLM response, `chat_agent.send_message` saves the response message and updates chat.updated_time
6. The `/v3.0/chat/send` endpoint does not need to return content; the frontend simply waits until `/v3.0/chat/heartbeat?chat_id={chat_id}` detects that the chat has been updated and then syncs messages and status

### 3. User Triggers a Tool
1. The user clicks a tool option; the frontend pushes a placeholder message for that tool indicating work in progress into the conversation view and sends the tool call to the backend: it calls `/v3.0/chat/call-tool?chat_id={chat_id}` with method=POST and the JSON request parameters `tool_name`, `tool_params`
2. The backend starts `chat_agent = ChatAgent(chat.id)` + `chat_agent.call_tool(tool_name, tool_params)` to invoke the tool; the chat_agent dispatches the task based on tool_name
3. In the call_tool implementation, every tool must create a sub-task and bind chat.id to its chat_id attribute so that the chat status can be synchronized. After creating and starting the chat_sub_task, call_tool must still create a message containing the chat_sub_task reference or other necessary information (id, name, etc.), synchronize the chat status with the chat_sub_task, and update chat.updated_time

### 4. Frontend Syncs the Chat from the Backend
1. From the moment the chat is opened, the frontend keeps track of updated_time, keeps sending heartbeats and fetches the backend's updated_time
2. If the backend updated_time differs from the frontend's, the frontend fetches the latest chat information and chat messages
3. After each message update, the frontend checks whether the latest message contains tool calls; if so, it shows the list of tools to the user, who can click a button to trigger a tool call

### 5. Synchronous and Asynchronous Tool Calls
1. Inside `chat_agent.call_tool`, after the corresponding tool function is invoked, a synchronous tool call calls `call_tool_feedback` immediately once it finishes
2. An asynchronous tool call only calls the system API to start the corresponding task. Only tasks that have callback support in the system are made into asynchronous tool calls, and the system callback must be extended to look up the chat_sub_task by tool_name and system_task_id, then start the chat agent with `chat_agent=ChatAgent(chat_sub_task.chat_id)` and call `chat_agent.call_tool_feedback(chat_sub_task.id, custom_output)`

### 6. Updating Chat Information
Users can update information such as the model via `/v3.0/chat/update`

## Callable Tools

1. **Query the current analysis information** - `_get_analysis_info`
2. **Query the current node information** - `_get_current_node_info`
3. **Query details of the current branch** - `_get_whole_branch_info`
4. **Recommend datasets** - `_get_dataset_list`
5. **Start a computation** - `_capture_data`
6. **Fix errors** - `_fix_bug`
7. **Automated analysis** - `_autogenie`
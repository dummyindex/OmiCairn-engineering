# Chat Agent API Reference

Based on the architecture described in chat_agent_design.md, this is the complete list of API endpoints of the Chat Agent module.

> **How parameters are read**: all endpoints read their parameters as follows; no parameters are passed in the URI:
> - GET requests: `request.args.get()`
> - POST requests: `request.json().get()` or `request.form.get()`

## 1. Frontend-facing Endpoints

### 1.1 Create Chat
```
POST /v3.0/chat/create
```

**Request parameters (request.json().get()):**
```json
{
    "analysis_id": "analysis ID",
    "current_node_id": "current node ID (optional)"
}
```

**Response:**
```json
{
    "code": 200,
    "data": {
        "id": "chat_id",
        "name": "Analysis-{analysis_id}",
        "analysis_id": "analysis ID",
        "current_node_id": "current node ID",
        "model": "gpt-4o-mini",
        "status": "normal",
        "created_time": "creation time",
        "updated_time": "update time"
    }
}
```

### 1.2 Send Message
```
POST /v3.0/chat/send-message
```

**Request parameters (request.json().get()):**
```json
{
    "chat_id": "unique chat identifier",
    "message": "user message content"
}
```

**Response:**
```json
{
    "code": 200,
    "message": "Message sent successfully"
}
```

### 1.3 Call Tool
```
POST /v3.0/chat/call-tool
```

**Request parameters (request.json().get()):**
```json
{
    "chat_id": "unique chat identifier",
    "tool_name": "tool name",
    "tool_params": {
        "param1": "parameter value 1",
        "param2": "parameter value 2"
    }
}
```

**Response:**
```json
{
    "code": 200,
    "data": {
        "sub_task_id": "sub-task ID",
        "status": "running",
        "message": "Tool call started"
    }
}
```

### 1.4 Heartbeat
```
GET /v3.0/chat/heartbeat
```

**Request parameters (request.args.get()):**
- `chat_id`: unique chat identifier

**Response:**
```json
{
    "code": 200,
    "data": {
        "updated_time": "latest update time",
    }
}
```

### 1.5 Delete Chat
```
POST /v3.0/chat/delete
```

**Request parameters (request.json().get()):**
```json
{
    "chat_id": "unique chat identifier"
}
```

**Response:**
```json
{
    "code": 200,
    "message": "Deleted successfully"
}
```

### 1.6 Update Chat
```
POST /v3.0/chat/update
```

**Request parameters (request.json().get()):**
```json
{
    "chat_id": "unique chat identifier",
    "model": "new model name (currently only the model attribute can be updated)"
}
```

**Response:**
```json
{
    "code": 200,
    "message": "Updated successfully"
}
```

## 2. Endpoints for the Frontend and the ChatAgent

### 2.1 Get Chat Information
```
GET /v3.0/chat/get-information
```

**Request parameters (request.args.get()):**
- `chat_id`: unique chat identifier

**Response:**
```json
{
    "code": 200,
    "data": {
        "id": "chat_id",
        "name": "chat name",
        "analysis_id": "analysis ID",
        "current_node_id": "current node ID",
        "model": "model in use",
        "status": "chat status",
        "created_time": "creation time",
        "updated_time": "update time"
    }
}
```

### 2.2 Get Chat Messages
```
GET /v3.0/chat/get-messages
```

**Request parameters (request.args.get()):**
- `chat_id`: unique chat identifier

**Response:**
```json
{
    "code": 200,
    "data": {
        "messages": [
            {
                "id": "message ID",
                "role": "user|assistant|tool",
                "chat_id": "chat ID",
                "tool_calls": "tool call information (JSON string)",
                "content": "message content",
                "created_time": "creation time",
                "model": "model in use",
                "model_time": "model response time",
                "prompt_tokens": "number of prompt tokens",
                "completion_tokens": "number of completion tokens"
            }
        ]
    }
}
```

### 2.3 Update Chat Information
```
POST /v3.0/chat/update-chat-information
```

**Request parameters (request.json().get()):**
```json
{
    "chat_id": "unique chat identifier",
    "updated_chat_attrs": {
        "status": "new status",
        "updated_time": "update time"
    }
}
```

**Response:**
```json
{
    "code": 200,
    "message": "Updated successfully"
}
```

## 3. ChatAgent-facing Endpoints

### 3.1 Create Chat Sub-task
```
POST /v3.0/chat/create-chat-sub-task
```

**Request parameters (request.json().get()):**
```json
{
    "chat_id": "unique chat identifier",
    "chat_sub_task_attrs": {
        "chat_id": "chat ID",
        "chat_message_id": "message ID",
        "tool_name": "tool name",
        "tool_params": "tool parameters (JSON string)",
        "system_task_id": "system task ID",
        "outputs": "output results",
        "status": "task status",
        "created_time": "creation time",
        "start_time": "start time",
        "end_time": "end time"
    }
}
```

**Response:**
```json
{
    "code": 200,
    "data": {
        "id": "sub-task ID",
        "chat_id": "chat ID",
        "chat_message_id": "message ID",
        "tool_name": "tool name",
        "tool_params": "tool parameters",
        "system_task_id": "system task ID",
        "outputs": "output results",
        "status": "task status",
        "created_time": "creation time",
        "start_time": "start time",
        "end_time": "end time"
    }
}
```

### 3.2 Update Chat Sub-task
```
POST /v3.0/chat/update-chat-sub-task
```

**Request parameters (request.json().get()):**
```json
{
    "chat_sub_task_id": "sub-task ID",
    "updated_chat_sub_task_attrs": {
        "system_task_id": "system task ID",
        "outputs": "output results",
        "status": "task status",
        "end_time": "end time"
    }
}
```

**Response:**
```json
{
    "code": 200,
    "message": "Updated successfully"
}
```

### 3.3 Get Chat Sub-task
```
GET /v3.0/chat/get-chat-sub-task
```

**Request parameters (request.args.get()):**
- `chat_sub_task_id`: sub-task ID

**Response:**
```json
{
    "code": 200,
    "data": {
        "id": "sub-task ID",
        "chat_id": "chat ID",
        "chat_message_id": "message ID",
        "tool_name": "tool name",
        "tool_params": "tool parameters",
        "system_task_id": "system task ID",
        "outputs": "output results",
        "status": "task status",
        "created_time": "creation time",
        "start_time": "start time",
        "end_time": "end time"
    }
}
```

### 3.4 Create Message
```
POST /v3.0/chat/create-message
```

**Request parameters (request.json().get()):**
```json
{
    "chat_id": "unique chat identifier",
    "message": {
        "chat_id": "chat ID",
        "content": "message content",
        "role": "user|assistant|tool",
        "tool_calls": "tool call information (JSON string, optional)",
        "created_time": "creation time",
        "model": "model in use",
        "model_time": "model response time",
        "prompt_tokens": "number of prompt tokens",
        "completion_tokens": "number of completion tokens"
    }
}
```

**Response:**
```json
{
    "code": 200,
    "data": {
        "id": "message ID",
        "chat_id": "chat ID",
        "role": "message role",
        "content": "message content",
        "created_time": "creation time"
    }
}
```

### 3.5 Update Message
```
POST /v3.0/chat/update-message
```

**Request parameters (request.json().get()):**
```json
{
    "chat_message_id": "message ID",
    "updated_message_attrs": {
        "content": "updated message content",
        "tool_calls": "tool call information",
        "model_time": "model response time",
        "prompt_tokens": "number of prompt tokens",
        "completion_tokens": "number of completion tokens"
    }
}
```

**Response:**
```json
{
    "code": 200,
    "message": "Updated successfully"
}
```

## 4. LLM Gateway Service Endpoints

### 4.1 Chat with the LLM
```
POST /v3.0/chat
```

**Request parameters (request.json().get()):**
```json
{
    "messages": [
        {
            "role": "user|assistant|system",
            "content": "message content"
        }
    ],
    "model": "gpt-4o-mini"
}
```

**Response:**
```json
{
    "code": 200,
    "data": {
        "message": "LLM reply content",
        "token_consumptions": {
            "prompt_tokens": 100,
            "completion_tokens": 50
        },
        "model_time": "model response time (seconds)",
        "tool_calls": [
            {
                "name": "tool name",
                "parameters": "tool parameters"
            }
        ]
    }
}
```

## 5. Enumerations

### ChatStatus (chat status)
- `normal`: normal state
- `executing`: a sub-task is being executed
- `responsing`: a reply is being generated (to be decided)

### ChatSubTaskStatus (sub-task status)
- `running`: running
- `finished`: finished
- `failed`: execution failed

### Role (message role)
- `user`: user text
- `tool`: call_tool record
- `assistant`: LLM answer

## 6. Available Tools

| Tool name | Description | Internal function |
|---------|------|----------|
| `get_analysis_info` | Query the current analysis information | `_get_analysis_info` |
| `get_current_node_info` | Query the current node information | `_get_current_node_info` |
| `get_whole_tree_info` | Query information about the whole tree | `_get_whole_tree_info` |
| `get_whole_branch_info` | Query details of the current branch | `_get_whole_branch_info` |
| `get_dataset_list` | Recommend datasets | `_get_dataset_list` |
| `capture_data` | Start a computation | `_capture_data` |
| `fix_bug` | Fix errors | `_fix_bug` |
| `autogenie` | Automated analysis | `_autogenie` |

## 7. Error Codes

| Error code | Description |
|-------|------|
| 200 | Success |
| 400 | Invalid request parameters |
| 404 | Chat does not exist |
| 500 | Internal server error |
| 503 | LLM service unavailable |
| 600 | Tool execution failed |
| 601 | Asynchronous task in progress |

## 8. Database Schema Reference

### chat table
| Field | Type | Description |
|-----|------|------|
| id | VARCHAR | Chat ID (primary key) |
| name | VARCHAR | Chat name |
| analysis_id | VARCHAR | Analysis ID |
| current_node_id | VARCHAR | Current node ID |
| model | VARCHAR | Model in use |
| status | VARCHAR | Chat status |
| created_time | DATETIME | Creation time |
| updated_time | DATETIME | Update time |

### chat_message table
| Field | Type | Description |
|-----|------|------|
| id | VARCHAR | Message ID (primary key) |
| role | VARCHAR | Message role |
| chat_id | VARCHAR | Chat ID (foreign key) |
| tool_calls | TEXT | Tool call information |
| content | TEXT | Message content |
| created_time | DATETIME | Creation time |
| model | VARCHAR | Model in use |
| model_time | FLOAT | Model response time |
| prompt_tokens | INT | Number of prompt tokens |
| completion_tokens | INT | Number of completion tokens |

### chat_sub_task table
| Field | Type | Description |
|-----|------|------|
| id | VARCHAR | Sub-task ID (primary key) |
| chat_id | VARCHAR | Chat ID (foreign key) |
| chat_message_id | VARCHAR | Message ID (foreign key) |
| tool_name | VARCHAR | Tool name |
| tool_params | TEXT | Tool parameters |
| system_task_id | VARCHAR | System task ID |
| outputs | TEXT | Output results |
| status | VARCHAR | Task status |
| created_time | DATETIME | Creation time |
| start_time | DATETIME | Start time |
| end_time | DATETIME | End time |

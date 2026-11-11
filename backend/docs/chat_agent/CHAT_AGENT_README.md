# Chat Agent Implementation

This document describes the Chat Agent implementation in omicairn-backend, following the specifications in `chat_agent_design.md`.

## Overview

The Chat Agent system enables interactive conversations with LLMs and tool execution within the omicairn analysis platform. It consists of:

1. **Database Models**: Chat, ChatMessage, and ChatSubTask
2. **Service Layer**: Chat management and operations
3. **API Layer**: RESTful endpoints for frontend integration
4. **Chat Agent**: Standalone Python module for LLM interaction and tool execution
5. **Subprocess Integration**: API server communicates with Chat Agent via command line

## Architecture

```
Frontend → API Controller → Chat Service → Chat Agent (subprocess) → LLM Server
                         ↓
                   Database Models
```

## Components

### Database Models

Located in `server/model/`:

- `chat.py` - Main chat entity
- `chat_message.py` - Individual messages in chats
- `chat_sub_task.py` - Tool execution tasks

### Service Layer

- `server/service/chat.py` - Business logic for chat operations
- `server/dao/chat*.py` - Data access objects

### API Layer

- `server/controller/chat.py` - RESTful API endpoints
- Follows v3.0 API specification from `docs/chat_agent_api.md`

### Chat Agent

Located in `chat_agent/`:

- `chat_agent.py` - Main ChatAgent class
- `server_api_invoker.py` - API client for server communication
- `main.py` - Command line interface

## Installation & Setup

### 1. Database Setup

Add the new tables to your database schema:

```sql
-- Run migrations to create chat, chat_message, and chat_sub_task tables
-- The models will be auto-created by SQLAlchemy
```

### 2. Server Configuration

Add the chat blueprint to your Flask app:

```python
from server.controller.chat import chat_bp

app.register_blueprint(chat_bp)
```

### 3. Dependencies

Install required Python packages:

```bash
pip install requests  # For chat agent HTTP communication
```

## API Endpoints

### Frontend APIs

- `POST /v3.0/chat/create` - Create new chat
- `POST /v3.0/chat/send-message` - Send user message
- `POST /v3.0/chat/call-tool` - Execute tool
- `GET /v3.0/chat/heartbeat` - Check for updates
- `POST /v3.0/chat/delete` - Delete chat
- `POST /v3.0/chat/update` - Update chat settings

### Management APIs

- `GET /v3.0/chat/get-information` - Get chat details
- `GET /v3.0/chat/get-messages` - Get message history
- `POST /v3.0/chat/update-chat-information` - Update chat info

### Internal APIs (ChatAgent)

- `POST /v3.0/chat/create-message` - Create message
- `POST /v3.0/chat/update-message` - Update message
- `POST /v3.0/chat/create-chat-sub-task` - Create sub task
- `POST /v3.0/chat/update-chat-sub-task` - Update sub task
- `GET /v3.0/chat/get-chat-sub-task` - Get sub task

## Chat Agent Usage

### Command Line Interface

```bash
# Initialize chat agent
python chat_agent/main.py init --chat_id <chat_id>  --user_id <user_id>

# Send message
python chat_agent/main.py send_message --chat_id <chat_id> --message "Hello" --user_id <user_id>

# Call tool
python chat_agent/main.py call_tool --chat_id <chat_id> --tool_name get_analysis_info --tool_params '{}'  --user_id <user_id>

# Process tool feedback (for async tools)
python chat_agent/main.py call_tool_feedback --chat_id <chat_id> --chat_sub_task_id <task_id> --output "result"  --user_id <user_id>
```

### Programmatic Usage

```python
from chat_agent.chat_agent import ChatAgent

# Create agent
agent = ChatAgent("chat-id-123", "user-id-123")

# Send message
agent.send_message("What is the current analysis status?")

# Call tool
agent.call_tool("get_analysis_info", {"analysis_id": analysis_id})
```

## Available Tools

The following tools are implemented in ChatAgent:

- **get_analysis_info** - Get current analysis information
- **get_current_node_branch** / **get_current_node_info** / **change_current_node** - Inspect or switch the current node
- **capture_data** - Recommend datasets matching the user request
- **plan_autogenie** / **run_autogenie** - Plan and run automated analysis (AutoGenie)
- **get_computation_details** - Get computation status and logs
- **create_data_node** / **create_computation_node** / **create_report** - Build the analysis graph
- **get_function_block_codes** / **get_available_function_blocks** - Inspect function blocks
- **read_file** - Read a result file from storage
- **import_and_process_h5ad_dataset** / **import_and_process_general_input_folder** - Import data

See `_get_tools()` in `chat_agent/chat_agent.py` for the authoritative list.

Tool calls are executed against the backend API through `chat_agent/server_api_invoker.py`.

## Testing

Dedicated chat-agent tests are not yet included in this early research release.
The backend unit tests can be run with:

```bash
# from the backend root (pytest.ini lives here)
pytest server/tests/unit/ -v
```

## Configuration

### Server URLs

Configure the server URLs in your environment:

- `MAIN_SERVER_HOST` - omicairn-backend server
- `GPT_WORKFLOW_SERVER_HOST` - LLM workflow/gateway service

### Chat Agent Configuration

The ChatAgent can be configured via constructor parameters:

```python
agent = ChatAgent(
    chat_id="chat-123",
    user_id="user-123"
)
```

## Error Handling

The system includes comprehensive error handling:

- **API Level**: HTTP status codes and error messages
- **Service Level**: Exception handling and logging
- **Chat Agent**: Graceful error recovery and status updates
- **Subprocess**: Timeout handling and error propagation

## Security

- All API endpoints require proper authentication
- Authority checks ensure users can only access their own chats
- Subprocess calls include timeout limits
- Input validation on all parameters

## Performance Considerations

- Database indexes on chat_id and analysis_id fields
- Message pagination for large conversations
- Subprocess timeout limits (30s for init, 120s for messages, 300s for tools)
- Connection pooling for HTTP requests

## Future Enhancements

1. **Async Tool Support**: Implement proper async task management
2. **Streaming Responses**: Support real-time message streaming
3. **Chat Persistence**: Add conversation export/import
4. **Multi-model Support**: Support different LLM models per chat

## Troubleshooting

### Common Issues

1. **Subprocess Timeout**: Increase timeout values in controller
2. **Database Connection**: Ensure proper database setup and migrations
3. **API Communication**: Check server URLs and network connectivity
4. **Tool Execution**: Verify tool implementations and parameters

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

Test system components:

```bash
# Test chat creation
curl -X POST http://localhost:5000/v3.0/chat/create -H "Content-Type: application/json" -d '{"analysis_id": "test"}'

# Test chat agent CLI
python chat_agent/main.py init --chat_id test-chat --user_id test-user
```

## Contributing

When adding new features:

1. Update database models if needed
2. Add service layer methods
3. Create API endpoints
4. Implement chat agent functionality
5. Add comprehensive tests
6. Update documentation
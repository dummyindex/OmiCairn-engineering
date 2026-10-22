# OmiCairn-backend API Documentation

## Overview

> Note: This is an early-stage, possibly incomplete API reference; the source code under `server/controller/` is authoritative.

OmiCairn-backend is the backend service of a bioinformatics analysis platform built on the Flask-RESTful architecture. This document describes all available API endpoints, request parameters, response formats and usage examples.

## Basic Information

- **Base URL**: `http://localhost:5000` (development environment)
- **Authentication**: token authentication (request header `token: <your-token>`)
- **Content type**: `application/json`
- **Character encoding**: UTF-8

## API Authentication

Most APIs require an authentication token in the request header:

```http
token: <your-token>
Content-Type: application/json
```

## API Endpoint Categories

### 1. User Management API

#### 1.1 Password Login
```http
POST /user/login-by-password
```

**Request parameters**:
```json
{
  "phone_number": "<PHONE_NUMBER>",
  "password": "your_password"
}
```

**Response example**:
```json
{
  "code": 200,
  "message": "Login successful",
  "data": "<token>"
}
```

#### 1.2 System Login (internal services only)
```http
POST /user/login-by-system?user_id=<user_id>
X-System-Agent-Key: <SYSTEM_AGENT_KEY>
```

**Query parameters**:
- `user_id`: user ID

The system agent key is passed in the `X-System-Agent-Key` request header (for compatibility with older clients, the `system_agent_key` query parameter is still accepted). If `SYSTEM_AGENT_KEY` is not configured, this endpoint rejects all requests.

#### 1.3 Token Validation
```http
GET /user/validate-token
```

**Request headers**: `token: <token>`

#### 1.4 User Registration
```http
POST /user/register
```

**Request parameters**:
```json
{
  "phone_number": "<PHONE_NUMBER>",
  "password": "your_password",
  "user_name": "Jane Doe",
  "email": "jane.doe@example.com"
}
```

#### 1.5 Get User Info
```http
GET /user/info/get
```

**Response example**:
```json
{
  "code": 200,
  "data": {
    "user_id": 12345,
    "user_name": "Jane Doe",
    "phone_number": "<PHONE_NUMBER>",
    "email": "jane.doe@example.com",
    "account_type": "personal",
    "created_time": 1640995200000
  }
}
```

#### 1.6 Search Users
```http
GET /user/search
```

**Query parameters**:
- `keyword`: search keyword
- `offset`: offset (default: 0)
- `limit`: maximum number of results (default: 20)

#### 1.7 Edit User Info
```http
POST /user/edit
```

**Request parameters**:
```json
{
  "user_name": "John Smith",
  "email": "john.smith@example.com",
  "phone_number": "<PHONE_NUMBER_2>"
}
```

### 2. Analysis Project Management API

#### 2.1 Get Public Analysis Info
```http
GET /analysis/public/get-info
```

**Query parameters**:
- `analysis_id`: analysis project ID

#### 2.2 Get Analysis Info
```http
GET /analysis/get-info
```

**Query parameters**:
- `analysis_id`: analysis project ID

**Response example**:
```json
{
  "code": 200,
  "data": {
    "analysis_id": 1001,
    "name": "Single-cell RNA-seq analysis",
    "description": "Single-cell analysis pipeline for 10x Genomics data",
    "created_time": 1640995200000,
    "owner_id": 12345,
    "share_to_all": true,
    "data_count": 5,
    "node_count": 15
  }
}
```

#### 2.3 Get Public Analysis List
```http
GET /analysis/public/get-list
```

#### 2.4 Get User Analysis List
```http
GET /analysis/get-list
```

**Response example**:
```json
{
  "code": 200,
  "data": [
    {
      "analysis_id": 1001,
      "name": "Single-cell RNA-seq analysis",
      "description": "Single-cell analysis pipeline for 10x Genomics data",
      "created_time": 1640995200000,
      "permission": "owner",
      "data_count": 5
    }
  ]
}
```

#### 2.5 Create Analysis Project
```http
POST /analysis/create
```

**Request parameters**:
```json
{
  "name": "New analysis project",
  "description": "Project description",
  "password": "access_password"
}
```

#### 2.6 Validate Analysis Access
```http
GET /analysis/validate
```

**Query parameters**:
- `analysis_id`: analysis project ID
- `password`: access password (optional)

#### 2.7 Import Data into Analysis
```http
POST /analysis/data/import
```

**Request parameters**:
```json
{
  "data_ids": [2001, 2002, 2003],
  "analysis_id": 1001
}
```

#### 2.8 Remove Data from Analysis
```http
DELETE /analysis/data/unimport
```

**Request parameters**:
```json
{
  "data_id": 2001,
  "analysis_id": 1001
}
```

#### 2.9 Copy Analysis Project
```http
POST /analysis/copy
```

**Request parameters**:
```json
{
  "analysis_id": 1001,
  "name": "Copied analysis project",
  "description": "Description of the copied project"
}
```

#### 2.10 Edit Analysis Project
```http
POST /analysis/edit
```

**Request parameters**:
```json
{
  "analysis_id": 1001,
  "name": "Updated project name",
  "description": "Updated project description"
}
```

#### 2.11 Delete Analysis Project
```http
DELETE /analysis/delete
```

**Request parameters**:
```json
{
  "analysis_id": 1001
}
```

#### 2.12 Toggle Public Sharing
```http
POST /analysis/toggle-sharing-for-all
```

**Request parameters**:
```json
{
  "analysis_id": 1001,
  "share_to_all": true
}
```

#### 2.13 Invite Collaborators
```http
POST /analysis/invite-collaborator
```

**Request parameters**:
```json
{
  "analysis_id": 1001,
  "receiver_id_list": [12346, 12347],
  "permission": "editor"
}
```

#### 2.14 Get Collaboration List
```http
GET /analysis/get-collaboration-list
```

**Query parameters**:
- `analysis_id`: analysis project ID

#### 2.15 Get Invitation List
```http
GET /analysis/get-invitation-list
```

**Query parameters**:
- `offset`: offset (optional)
- `limit`: maximum number of results (optional)

#### 2.16 Accept/Reject Invitation
```http
GET /analysis/accept-invitation
GET /analysis/reject-invitation
```

**Query parameters**:
- `invitation_id`: invitation ID

### 3. Data Management API

#### 3.1 Validate Data Creation Form
```http
POST /data/validate-creation-form
```

**Request parameters**:
```json
{
  "species": "human",
  "description": "Single-cell RNA-seq data"
}
```

#### 3.2 Create Data Framework
```http
POST /data/framework/create
```

**Request parameters**:
```json
{
  "upload_type": "single_cell",
  "name": "10x Genomics data",
  "species": "human",
  "description": "Single-cell transcriptome data from PBMCs"
}
```

#### 3.3 Get Upload Info
```http
GET /data/upload/info/get
```

**Query parameters**:
- `data_id`: data ID
- `file_size`: file size

**Response example**:
```json
{
  "code": 200,
  "data": {
    "upload_url": "https://s3.amazonaws.com/...",
    "fields": {
      "key": "data/12345/matrix.h5",
      "policy": "...",
      "signature": "..."
    }
  }
}
```

#### 3.4 Get Component Upload Info
```http
GET /data/component/upload/info/get
```

**Query parameters**:
- `data_id`: data ID
- `component_type`: component type
- `file_suffix`: file suffix
- `file_size`: file size

#### 3.5 Remove Data Component
```http
DELETE /data/remove-component
```

**Request parameters**:
```json
{
  "data_id": 2001,
  "component_type": "matrix"
}
```

#### 3.6 Get Component List
```http
GET /data/component/list/get
```

**Query parameters**:
- `data_id`: data ID
- `upload_type`: upload type

#### 3.7 Get Data List
```http
GET /data/list/get
```

**Query parameters**:
- `mode`: mode (all, my, shared)
- `search_key`: search keyword (optional)
- `analysis_id`: analysis project ID (optional)
- `state`: data state (optional)
- `page`: page number (default: 1)
- `page_size`: page size (default: 20)
- `only_ok`: show only data in OK state (optional)

**Response example**:
```json
{
  "code": 200,
  "data": {
    "total": 100,
    "data": [
      {
        "data_id": 2001,
        "name": "PBMC dataset",
        "species": "human",
        "state": "ok",
        "created_time": 1640995200000,
        "file_size": 1073741824,
        "description": "Peripheral blood mononuclear cells from healthy donors"
      }
    ]
  }
}
```

#### 3.8 Get Data Index
```http
GET /data/get-data-index
```

**Query parameters**:
- `data_id`: data ID
- `search_key`: search keyword
- `only_ok`: show only data in OK state

#### 3.9 Get Download Info
```http
GET /data/download/info/get
```

**Query parameters**:
- `data_id`: data ID

#### 3.10 Delete Data
```http
DELETE /data/remove
```

**Request parameters**:
```json
{
  "data_id": 2001
}
```

#### 3.11 Get Species List
```http
GET /data/species/list/get
```

**Response example**:
```json
{
  "code": 200,
  "data": [
    {
      "species": "human",
      "display_name": "Human",
      "genome_version": "GRCh38"
    },
    {
      "species": "mouse",
      "display_name": "Mouse",
      "genome_version": "GRCm38"
    }
  ]
}
```

### 4. Computation Management API

#### 4.1 Get Latest Computation for Node
```http
GET /computation/latest-by-node/get
```

**Query parameters**:
- `node_id`: node ID

**Response example**:
```json
{
  "code": 200,
  "data": {
    "computation_id": 3001,
    "node_id": 4001,
    "state": "finished",
    "start_time": 1640995200000,
    "end_time": 1640995800000,
    "duration": 600,
    "cpu_usage": 85.5,
    "memory_usage": 4096
  }
}
```

#### 4.2 Get Computation List
```http
GET /computation/list
```

**Query parameters**:
- `mode`: mode (all, my, analysis)
- `node_id`: node ID (optional)
- `task_id`: task ID (optional)
- `analysis_id`: analysis project ID (optional)
- `show_node`: include node info (optional)
- `show_user`: include user info (optional)
- `show_data`: include data info (optional)
- `limit`: maximum number of results (optional)
- `offset`: offset (optional)

#### 4.3 Get Figure List
```http
GET /computation/figure-list/get
```

**Query parameters**:
- `computation_id`: computation ID

**Response example**:
```json
{
  "code": 200,
  "data": [
    {
      "figure_id": "umap",
      "title": "UMAP embedding",
      "type": "scatter",
      "url": "https://s3.amazonaws.com/figures/umap.png"
    },
    {
      "figure_id": "violin",
      "title": "Gene expression violin plot",
      "type": "violin",
      "url": "https://s3.amazonaws.com/figures/violin.png"
    }
  ]
}
```

### 5. Node Management API

#### 5.1 Edit Node
```http
POST /node/edit
```

**Request parameters**:
```json
{
  "node_id": 4001,
  "name": "Quality control",
  "x": 100,
  "y": 200,
  "params": {
    "min_genes": 200,
    "max_genes": 5000
  }
}
```

#### 5.2 Batch Edit Nodes
```http
POST /node/batch-edit
```

**Request parameters**:
```json
{
  "node_id_list": [4001, 4002, 4003],
  "attrs": {
    "state": "ready"
  }
}
```

#### 5.3 Create Node
```http
POST /node/create
```

**Request parameters**:
```json
{
  "analysis_id": 1001,
  "x": 300,
  "y": 400,
  "name": "Data preprocessing",
  "data_id": 2001,
  "function_block_id": 5001
}
```

#### 5.4 Get Node List
```http
GET /node/list/get
```

**Query parameters**:
- `mode`: mode (analysis, computation)
- `analysis_id`: analysis project ID (optional)
- `computation_id`: computation ID (optional)

**Response example**:
```json
{
  "code": 200,
  "data": [
    {
      "node_id": 4001,
      "name": "Quality control",
      "type": "computation",
      "x": 100,
      "y": 200,
      "state": "finished",
      "function_block_id": 5001,
      "function_block_name": "Quality Control"
    }
  ]
}
```

#### 5.5 Delete Node
```http
DELETE /node/delete
```

**Request parameters**:
```json
{
  "node_id": 4001
}
```

#### 5.6 Batch Delete Nodes
```http
DELETE /node/batch-delete
```

**Request parameters**:
```json
{
  "node_id_list": [4001, 4002, 4003]
}
```

#### 5.7 Copy Node
```http
POST /node/copy
```

**Request parameters**:
```json
{
  "node_id": 4001,
  "x": 500,
  "y": 600,
  "analysis_id": 1001
}
```

### 6. AI/GPT API

#### 6.1 Send Chat Message
```http
POST /gpt/chat/send
```

**Request parameters**:
```json
{
  "message": "How should I perform quality control for single-cell RNA-seq?",
  "context": "single_cell_analysis",
  "analysis_id": 1001
}
```

#### 6.2 Initialize Chat
```http
POST /gpt/chat/init
```

**Request parameters**:
```json
{
  "analysis_id": 1001,
  "context_type": "analysis"
}
```

#### 6.3 Get Chat History
```http
GET /gpt/chat/history
```

**Query parameters**:
- `analysis_id`: analysis project ID
- `limit`: maximum number of results (default: 50)

#### 6.4 Recommend Pipeline
```http
POST /gpt/recommend-pipeline
```

**Request parameters**:
```json
{
  "data_type": "single_cell_rna_seq",
  "analysis_goal": "clustering",
  "species": "human"
}
```

#### 6.5 Fill Parameters
```http
POST /gpt/fill-params
```

**Request parameters**:
```json
{
  "node_id": 4001,
  "function_block_id": 5001,
  "data_info": {
    "species": "human",
    "cell_count": 5000
  }
}
```

### 7. Chatbot API

#### 7.1 Create Chat Session
```http
POST /api/v1/analysis/{analysis_id}/chat/sessions
```

**Request parameters**:
```json
{
  "title": "Single-cell analysis discussion"
}
```

#### 7.2 Get Chat Session History
```http
GET /api/v1/analysis/{analysis_id}/chat/sessions
```

#### 7.3 Delete Chat Session
```http
DELETE /api/v1/chat/sessions/{session_id}
```

#### 7.4 Send Message
```http
POST /api/v1/chat/sessions/{session_id}/messages
```

**Request parameters**:
```json
{
  "content": "What do the clustering results in this UMAP plot show?",
  "contextType": "node",
  "nodeId": 4001,
  "model": "gpt-4"
}
```

## Error Handling

### Common Error Codes

- `200`: success
- `400`: invalid request parameters
- `401`: unauthorized (token invalid or expired)
- `403`: insufficient permissions
- `404`: resource not found
- `500`: internal server error

### Error Response Format

```json
{
  "code": 400,
  "message": "Invalid request parameters",
  "error": "missing required parameter: analysis_id"
}
```

## Usage Examples

### Python Example

```python
import requests

# Log in to obtain a token
login_response = requests.post('http://localhost:5000/user/login-by-password', 
    json={
        'phone_number': '<PHONE_NUMBER>',
        'password': 'your_password'
    })

token = login_response.json()['data']
headers = {
    'token': token,
    'Content-Type': 'application/json'
}

# Get the analysis list
analysis_response = requests.get('http://localhost:5000/analysis/get-list', 
    headers=headers)

print(analysis_response.json())
```

### JavaScript Example

```javascript
// Log in to obtain a token
const loginResponse = await fetch('http://localhost:5000/user/login-by-password', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        phone_number: '<PHONE_NUMBER>',
        password: 'your_password'
    })
});

const loginData = await loginResponse.json();
const token = loginData.data;

// Create an analysis project
const createAnalysisResponse = await fetch('http://localhost:5000/analysis/create', {
    method: 'POST',
    headers: {
        'token': token,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        name: 'New single-cell analysis',
        description: '10x Genomics data analysis pipeline'
    })
});

const analysisData = await createAnalysisResponse.json();
console.log(analysisData);
```

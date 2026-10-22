# omicairn-claude-code Design Document

## Executive Summary

**omicairn-claude-code** is a Docker-based orchestration system that enables Claude AI (via Claude Code CLI) to execute complex, multi-step genomic analysis pipelines. It solves the timeout problem for long-running bioinformatics jobs through a pause-resume pattern with built-in checkpointing and incremental S3 uploads.

---

## 1. Project Structure

```
omicairn-claude-code/
├── Dockerfile                    # Container definition (Ubuntu 22.04 + R + Python + Node.js)
├── build-image.sh               # Docker build (optional push to your own registry)
├── CLAUDE.md                    # Execution rules for Claude code
├── requirements.txt             # Python: boto3, requests
│
├── scripts/                     # Core orchestration
│   ├── start_claude_code.sh    # ENTRYPOINT - Main orchestrator
│   ├── run_job.py              # Long-running job executor
│   ├── all_steps_done.py       # Progress status checker
│   ├── parse_todo_progress.py  # Todo state parser from logs
│   ├── upload_step.py          # Incremental S3 uploader
│   ├── upload_conversation.py  # Real-time log monitor
│   └── upload_orchestration_logs.py  # Control file archiver
│
├── previous_app/                # Phase 1: Input preparation
│   ├── main.py                 # Prepares metadata & node info (on-demand loading)
│   ├── server_api_invoker.py   # Server API client for node/computation data
│   ├── constants.py            # Shared environment variable constants
│   ├── timepiece.py            # Duration tracking utility
│   └── log/logger_factory.py   # Logging factory
│
├── close_out_app/               # Phase 3: Output finalization
│   ├── main.py                 # Uploads results & notifies backend
│   ├── api_client.py           # REST API client
│   ├── constants.py            # Shared environment variable constants
│   └── utils.py                # Thumbnail generation utilities
│
├── skills/                      # Claude Code skills
│   └── ragtool-usage/SKILL.md  # ragtool utility documentation
│
├── claude_code_agent/           # Empty agent placeholder
│   └── __init__.py
│
└── tests/                       # Integration-test scaffold (pytest + moto)
```

---

## 2. Three-Phase Execution Model

### Phase 1: Input Preparation (`previous_app/main.py`)

Prepares metadata and node information for on-demand file loading:

| Action | API/Source | Output |
|--------|------------|--------|
| Get node information | `GET /node/get-info` | `/app/current_node_info.json` |
| Get branch path (upstream nodes) | `GET /node/get-previous-path` | `/app/inputs-dict.json` |
| Get Auto Genie plan | `GET /dynamic-generation/get-plan` + presigned URL | `/app/auto-genie-current-plan.json` |

### Phase 2: Claude Code Orchestration Loop (`start_claude_code.sh`)

The core execution engine with up to 50 iterations:

```
┌──────────────────────────────────────────────────────────────────┐
│                    Orchestration Loop                            │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │ Start Claude │───▶│ Claude runs  │───▶│ Claude pauses│        │
│  │ Code session │    │ analysis     │    │              │        │
│  └──────────────┘    └──────────────┘    └───────┬──────┘        │
│                                                  │               │
│                                 ┌────────────────▼────────────┐  │
│                                 │ job_request.json generated? │  │
│                                 └────────────────┬────────────┘  │
│                                                  │               │
│                           ┌──────────────────────┴────────────┐  │
│                           │                                   │  │
│                      YES  ▼                              NO   ▼  │
│                 ┌─────────────────┐              ┌──────────────┐│
│                 │ Execute job     │              │ Check status ││
│                 │ (run_job.py)    │              │ all_steps_   ││
│                 └────────┬────────┘              │ done.py      ││
│                          │                       └──────┬───────┘│
│                          │                              │        │
│                          ▼                              ▼        │
│                 ┌────────────────┐     ┌────────────────────────┐│
│                 │ Write result   │     │ Exit 0: COMPLETED      ││
│                 │ Resume Claude  │     │ Exit 1: Continue loop  ││
│                 │ with --continue│     │ Exit 2: FAILED         ││
│                 └────────────────┘     └────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

### Phase 3: Output Finalization (`close_out_app/main.py`)

1. Fetches computation details to get `resultDataId` via API
2. Uploads charts from `/omicairn/outputs/charts/` with auto-generated thumbnails
3. Uploads all files from `/omicairn/outputs/**` to S3 at `adata/{resultDataId}-general-s3-store/`
4. Notifies backend via API (`/task/finished-report` or `/task/failed-report`)

---

## 3. Control File System

State management uses a combination of JSON files in `/omicairn/control/` and TodoWrite state parsed from Claude's session log.

### Progress Tracking via TodoWrite

Instead of a separate state file, the orchestrator tracks progress by parsing TodoWrite entries from `/omicairn/outputs/claude_code.log`. The `parse_todo_progress.py` script extracts the latest todo state:

```python
# Example TodoWrite state extracted from log
[
  {"content": "Load input data", "status": "completed", "activeForm": "Loading input data"},
  {"content": "Run quality control", "status": "in_progress", "activeForm": "Running quality control"},
  {"content": "Perform differential expression", "status": "pending", "activeForm": "Performing differential expression"}
]
```

The orchestrator uses `all_steps_done.py` to check completion:
- Exit code `0`: All tasks completed (exit loop)
- Exit code `1`: Tasks remaining (continue loop)
- Exit code `2`: Pipeline failed (exit loop)

### `job_request.json` - Job Submission (Claude → Orchestrator)

```json
{
  "request_id": "uuid-string",
  "timestamp": "2026-02-03T12:00:00Z",
  "command": "cellranger count --id=sample1 ...",
  "working_directory": "/omicairn/outputs/step_02_cellranger",
  "description": "Cell Ranger count for sample N2_1",
  "expected_outputs": ["/path/to/web_summary.html", "/path/to/matrix.h5"]
}
```

### `job_result.json` - Job Result (Orchestrator → Claude)

```json
{
  "request_id": "uuid-string",
  "exit_code": 0,
  "success": true,
  "duration_seconds": 3600,
  "log_file": "/omicairn/control/logs/job_uuid.log",
  "outputs_found": ["/path/to/web_summary.html"],
  "outputs_missing": [],
  "error_message": null
}
```

---

## 4. On-Demand File Loading (ragtool)

Claude accesses input files using the `ragtool` utility instead of reading from pre-downloaded locations.

### Commands

| Command | Description |
|---------|-------------|
| `ragtool load_file <node_key> <path>` | Download a specific file on-demand |
| `ragtool get_parent_node_folder` | Download all files from parent node |

### Workflow

```python
# Load specific file on-demand
result = subprocess.run(['ragtool', 'load_file', 'node_1', 'data.h5ad'],
                       capture_output=True, text=True, check=True)
file_path = result.stdout.strip()

# Process the file
import scanpy as sc
adata = sc.read_h5ad(file_path)
```

### Benefits

- **Reduced startup time**: No upfront downloads
- **Memory efficient**: Only load what's needed
- **Caching**: Downloaded files are cached for reuse

---

## 5. Key Design Patterns

### Pattern 1: Incremental Upload for Fault Tolerance

Each step uploads immediately after completion:

```python
# After completing step_01
subprocess.run(["python3", "/app/scripts/upload_step.py", "step_01_data_loading"])

# Even if job times out now, step_01 outputs are preserved in S3!
```

### Pattern 2: Background Monitoring

Real-time visibility without interfering with execution:

- `upload_conversation.py` runs in background
- Uploads `claude_code.log` to S3 every 5 minutes
- Users can monitor progress without waiting for completion
  - `/omicairn/outputs/orchestration_logs/` - All orchestration state snapshots
  - `/omicairn/control/logs/` - Individual job execution logs
  - `/omicairn/outputs/claude_code.log` - Complete Claude session transcript

---

## 6. Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `COMPUTATION_ID` | Unique identifier for this job |
| `BUCKET_NAME` | S3 bucket for I/O |
| `NODE_ID` | Graph node identifier |
| `ANTHROPIC_API_KEY` | Claude authentication (supported credential for server deployments; `CLAUDE_CODE_OAUTH_TOKEN` is only for local single-user testing) |
| `COMPUTATION_SERVER_HOST` | Gateway base URL for the worker API (`/computation-server/...`); used for status reporting |
| `MAIN_SERVER_HOST` | Gateway base URL for the backend API (`/server/...`); used for login and node/function-block calls |
| `SYSTEM_AGENT_KEY` | Shared secret sent as the `X-System-Agent-Key` header to `/server/user/login-by-system` |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `USER_ID` | - | User identifier for API authentication |
| `CLAUDE_MODEL` | sonnet | Model to use |
| `MAX_ITERATIONS` | 100 | Claude turns per session |
| `MAX_LOOP_ITERATIONS` | 50 | Orchestrator loop limit |
| `UPLOAD_INTERVAL` | 300 | Log upload interval (seconds) |
| `PIPE_MESSAGE_PATH` | /tmp/pipe-message | Path for inter-process communication |

---

## 7. Docker Container

### Base: Ubuntu 22.04

### Installed Tools

**R Packages (Bioconductor)**:
- limma, DESeq2, edgeR (differential expression)
- clusterProfiler, enrichplot, DOSE, pathview (functional enrichment)
- org.Hs.eg.db (annotations)
- survival, survminer (survival analysis)
- ggplot2, dplyr, tidyr, readr (data manipulation/visualization)

**Python Packages**:
- numpy, pandas, scipy, scikit-learn, statsmodels (data science)
- scanpy, anndata, biopython (bioinformatics)
- matplotlib, seaborn, plotly (visualization)
- openpyxl, xlrd, pyarrow, h5py (file I/O)
- boto3, requests (AWS and HTTP)

**System**:
- Node.js 20 + Claude Code CLI
- R 4.x with development tools
- jq (JSON parser)

**Skills** (copied to `/home/claudeuser/.claude/skills/`):
- `ragtool-usage/SKILL.md` - Documentation for the ragtool file loading utility

### Security

- Non-root user: `claudeuser`
- IAM roles for S3 access (no embedded credentials)
- API authentication with retry logic

---

## 8. Building the Image

```bash
./build-image.sh v1.0.0                                   # local build only
REGISTRY=<YOUR_REGISTRY> PUSH=1 ./build-image.sh v1.0.0   # build and push to your own registry
```

No CI/CD deployment pipeline is included in this release.

---

## 9. Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                              S3 Bucket                              │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐ │
│  │ adata/{data_id}-general-     │  │ dynamic_generation/          │ │
│  │ s3-store/**                  │  │ {id}/plan.json               │ │
│  └──────────────┬───────────────┘  └────────────┬─────────────────┘ │
└─────────────────┼───────────────────────────────┼───────────────────┘
                  │                               │
                  │  ┌────────────────────────────┘
                  │  │
                  ▼  ▼
    ┌───────────────────────────────────────────────────────────────┐
    │                Phase 1: Metadata Preparation                  │
    │                   previous_app/main.py                        │
    │                                                               │
    │  • Get node info from API → /app/current_node_info.json       │
    │  • Build file metadata   → /app/inputs-dict.json              │
    │  • Get Auto Genie plan   → /app/auto-genie-current-plan.json  │
    │  (No file downloads - metadata only)                          │
    └───────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
    ┌───────────────────────────────────────────────────────────────┐
    │                   Phase 2: Claude Code Loop                   │
    │                                                               │
    │  Claude uses ragtool to load files on-demand from S3          │
    │  ┌─────────────────────────────────────────────────────────┐  │
    │  │ ragtool load_file node_1 data.h5ad  →  Downloads file   │  │
    │  └─────────────────────────────────────────────────────────┘  │
    │                         ↓                                     │
    │  /omicairn/outputs/step_01_*/ ──────▶ upload_step.py ──▶ S3   │
    │  /omicairn/outputs/step_02_*/ ──────▶ upload_step.py ──▶ S3   │
    └───────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
    ┌───────────────────────────────────────────────────────────────┐
    │                 Phase 3: Output Finalization                  │
    │                   close_out_app/main.py                       │
    │                                                               │
    │  Get resultDataId from API                                    │
    │  Upload outputs ──▶ S3: adata/{resultDataId}-general-s3-store/│
    │  Notify backend ──▶ /task/finished-report                     │
    └───────────────────────────────────────────────────────────────┘
```
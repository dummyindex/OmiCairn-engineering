# OmiCairn backend (Flask API)

> **Early-stage research software.** This is the backend API of the OmiCairn web platform
> for multi-omics analysis, released together with the accompanying publication. It is a
> research prototype: interfaces may change, parts of the test suite are incomplete, and it
> has not been hardened for production or multi-tenant use. See "Known limitations" below.

The backend orchestrates analysis workflows (graphs of data, computation, notebook,
agent and report nodes), manages datasets and function blocks (reusable analysis tools),
stores files in S3-compatible object storage, and forwards LLM-assisted features
(chat agent, pipeline recommendation, parameter filling, report generation) to a separate
LLM workflow service configured via `GPT_WORKFLOW_SERVER_HOST`.

## Architecture

Code lives under `server/`:

- **controller**: Flask-RESTful endpoints (one blueprint per resource)
- **service**: business logic
- **dao**: database access (SQLAlchemy)
- **model**: ORM entities
- **dto**: data-transfer objects
- **authority**: token-based authentication and per-analysis authorization
- **sss**: object-storage abstraction (S3 implementation)
- **waiter**: file services built on top of `sss`
- **llm**: client for the LLM workflow service
- **tool**: shared utilities

Other directories:

- `chat_agent/`: LLM tool-calling chat agent that drives analyses through the backend API
- `data_uploading_check/`: small service that marks timed-out uploads as failed
- `omicairn_scripts/`: container entrypoint and environment scripts
- `docs/`: API and chat-agent documentation

### Core entities

Analysis, Data, Function Block (and versions), Node, Edge, Pipeline Template,
Report / Workflow Report, Chat session.

## Quick start

### Prerequisites

- Python 3.10
- MySQL 8
- S3 or an S3-compatible object store (e.g. MinIO)
- The LLM workflow service (for LLM-assisted features)

### Install and run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then edit the values
set -a; source .env; set +a

bash omicairn_scripts/omicairn_prepare-store.sh   # creates the local store folders
cd server
gunicorn -w 2 --timeout 600 -b 0.0.0.0:8000 "main:create_app()"
```

### Docker

```bash
docker build -t omicairn-backend .
docker run --env-file .env -p 8000:80 omicairn-backend
```

Credentials (database, AWS) are passed at runtime through environment variables; they are
never baked into the image.

## Configuration

All configuration is read from environment variables. `.env.example` lists every variable
with a placeholder value. The most important ones:

| Variable | Purpose |
|---|---|
| `MYSQL_IP`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` | MySQL connection |
| `BUCKET_NAME`, `AWS_REGION`, `S3_ENDPOINT_URL` | Object storage |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | AWS credentials (standard boto3 chain) |
| `GPT_WORKFLOW_SERVER_HOST`, `GPT_WORKFLOW_SERVER_PORT` | LLM workflow service |
| `SYSTEM_AGENT_KEY` | Shared secret used by internal agents/workers to act on behalf of a user (sent in the `X-System-Agent-Key` header); system login is disabled while unset |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins |
| `LOG_LEVEL` | Python logging level (default `INFO`) |

Routes are served without a prefix (e.g. `/user/login-by-password`). In a full deployment the
frontend, worker and claude-code reach the backend through an HTTP gateway that maps `/server/*`
to this service and `/computation-server/*` to the worker (see "Service topology" in
`../frontend/README.md`).

## Testing

```bash
cd server
pytest tests/unit/ -v
```

Tests use mocks for the database and object storage. Some test modules were written
against earlier versions of the service layer and still fail; they are kept as a starting
point and are listed as known limitations.

## Known limitations

- Accounts are identified by phone number + password; there is no e-mail verification or
  password reset flow.
- Several endpoints authorize only at the analysis level; fine-grained checks on raw
  object-storage keys are incomplete.
- Per-analysis share passwords and API keys are stored in plain text in the database.
- Preprocessing jobs and notebook/agent execution assume AWS Batch.

## License

See the `LICENSE` file at the repository root. Copyright The OmiCairn Authors.

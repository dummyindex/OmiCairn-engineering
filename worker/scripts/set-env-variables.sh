export OMICAIRN_STORE="/omicairn/store"
export OMICAIRN_CODE_SPACE="/omicairn/code_space"

export OPENBLAS_NUM_THREADS=1
export PYTHONIOENCODING="utf-8"

export LOCAL_JOB_QUEUE="/tmp/local-job-queue"

mkdir -p $LOCAL_JOB_QUEUE

export LOCAL_JOB_SIGNAL="/tmp/job-signal"
mkdir -p $LOCAL_JOB_SIGNAL

export PORTER_TYPE="${PORTER_TYPE:-s3-porter}"

# Shared secret for /server/user/login-by-system (sent as the X-System-Agent-Key header).
# Must equal the backend's SYSTEM_AGENT_KEY; no default on purpose.
export SYSTEM_AGENT_KEY="${SYSTEM_AGENT_KEY:-}"
if [ -z "$SYSTEM_AGENT_KEY" ]; then
    echo "WARNING: SYSTEM_AGENT_KEY is not set; worker agents cannot log in to the backend." >&2
fi

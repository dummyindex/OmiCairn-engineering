# Example deployment settings. Every value can be overridden by an
# environment variable of the same name that is already set.

# MySQL
export MYSQL_IP="${MYSQL_IP:-localhost}"
export MYSQL_PORT="${MYSQL_PORT:-3306}"
export MYSQL_DATABASE="${MYSQL_DATABASE:-omicairn}"
export MYSQL_USER="${MYSQL_USER:-root}"
export MYSQL_PASSWORD="${MYSQL_PASSWORD:-<YOUR_MYSQL_PASSWORD>}"

# Object storage (S3 or S3-compatible such as MinIO)
export BUCKET_NAME="${BUCKET_NAME:-<YOUR_BUCKET_NAME>}"
export AWS_REGION="${AWS_REGION:-<YOUR_AWS_REGION>}"
# export S3_ENDPOINT_URL="http://localhost:9000"

export COMPUTATION_IP="${COMPUTATION_IP:-localhost}"

# LLM gateway / workflow services
export GPT_SERVER_HOST="${GPT_SERVER_HOST:-localhost}"
export GPT_SERVER_PORT="${GPT_SERVER_PORT:-5000}"

export GPT_WORKFLOW_SERVER_HOST="${GPT_WORKFLOW_SERVER_HOST:-localhost}"
export GPT_WORKFLOW_SERVER_PORT="${GPT_WORKFLOW_SERVER_PORT:-5000}"

# Optional outbound HTTP proxy (leave unset for direct connections)
# export NETWORK_PROXY_HOST="host.docker.internal"
# export NETWORK_PROXY_PORT="3128"

# AWS Batch queues / job definitions used for preprocessing jobs
export FB_PP_QUEUE="${FB_PP_QUEUE:-<YOUR_FB_PREPROCESS_QUEUE>}"

export DATA_PREPROCESSOR_JOB_DEFINITION="${DATA_PREPROCESSOR_JOB_DEFINITION:-<YOUR_DATA_PREPROCESSOR_JOB_DEFINITION>}"
export DATA_PREPROCESSOR_QUEUE="${DATA_PREPROCESSOR_QUEUE:-<YOUR_DATA_PREPROCESSOR_QUEUE>}"

export DATA_VITESSCE_PREPROCESSOR_JOB_DEFINITION="${DATA_VITESSCE_PREPROCESSOR_JOB_DEFINITION:-<YOUR_VITESSCE_PREPROCESSOR_JOB_DEFINITION>}"
export DATA_VITESSCE_PREPROCESSOR_QUEUE="${DATA_VITESSCE_PREPROCESSOR_QUEUE:-<YOUR_VITESSCE_PREPROCESSOR_QUEUE>}"

export MAIN_SERVER_HOST="${MAIN_SERVER_HOST:-http://localhost:80}"
export COMPUTATION_SERVER_HOST="${COMPUTATION_SERVER_HOST:-http://localhost:8099/computation-server}"
export DATA_SERVER_HOST="${DATA_SERVER_HOST:-http://localhost:8099/data}"

# Allowed browser origins for the API (comma separated)
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000}"

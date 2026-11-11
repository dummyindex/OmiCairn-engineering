#!/bin/bash
# Default service endpoints for local development.
# Override by exporting the variables before the container starts.

if [ -z "$MAIN_SERVER_HOST" ]; then
    export MAIN_SERVER_HOST="http://localhost:8080"
    echo "MAIN_SERVER_HOST set to default: $MAIN_SERVER_HOST"
fi

if [ -z "$COMPUTATION_SERVER_HOST" ]; then
    export COMPUTATION_SERVER_HOST="http://localhost:8080"
    echo "COMPUTATION_SERVER_HOST set to default: $COMPUTATION_SERVER_HOST"
fi

if [ -z "$SYSTEM_AGENT_KEY" ]; then
    echo "WARNING: SYSTEM_AGENT_KEY is not set; backend authentication will fail." >&2
fi

echo "Server configuration:"
echo "  MAIN_SERVER_HOST=$MAIN_SERVER_HOST"
echo "  COMPUTATION_SERVER_HOST=$COMPUTATION_SERVER_HOST"

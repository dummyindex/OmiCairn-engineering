store_path="$HOME/omicairn-store"

export OMICAIRN_STORE_FOLDER=$store_path

export COMPUTION_ENV_ROOT="$store_path/compution_env/"

export ATTACHED_DATA_FOLDER="$store_path/attached_data"

export DATA_FOLDER="$store_path/adata"

export TEMP_FOLDER_PATH="$store_path/temps"

export GRAPH_SNAPSHOT_IMAGE_FOLDER="$store_path/graph_snapshot/image"

export GRAPH_SNAPSHOT_SCENE_ENVIRONMENT_FOLDER="$store_path/graph_snapshot/scene-environment"

# Shared secret for internal service-to-service login (/user/login-by-system).
# Generate one, e.g. `python3 -c "import secrets; print(secrets.token_hex(16))"`,
# and use the same value in the worker and agent-runner components.
# No default on purpose: system login is rejected while it is unset.
export SYSTEM_AGENT_KEY="${SYSTEM_AGENT_KEY:-}"

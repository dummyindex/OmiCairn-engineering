import os

##################################################
# object storage related
##################################################

BUCKET_NAME = os.environ.get("BUCKET_NAME")
ADATA_FOLDER_PREFIX = "adata"
COMPUTATION_OUTPUT_FOLDER_PREFIX = "computation-output"
DATA_SPACE_FOLDER_PREFIX = "data-space"
NODE_SPACE_FOLDER_PREFIX = "node-space"
FIGURE_FOLDER_PREFIX = "figure"
FUNCTION_BLOCK_VERSION_PREFIX = "function-block-version"
GRAPH_SNAPSHOT_IMAGE_PREFIX = "graph-snapshot-image"
GRAPH_SNAPSHOT_ENVIRONMENT_PREFIX = "graph-snapshot-environment"
EXAMPLE_ADATA_ID = "example-anndata"
USER_SPACE_FOLDER_PREFIX = "user-space"

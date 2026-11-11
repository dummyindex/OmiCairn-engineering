import os
from constants.common import AugmentedEnum,create_folder_if_not_exist
##################################################
# hw obs related
##################################################
DATA_FOLDER_PREFIX = "adata"
FIGURE_FOLDER_PREFIX = "figure"
FUNCTION_BLOCK_PREFIX = "function-block"

BUCKET_NAME = os.environ.get("BUCKET_NAME")

OMICAIRN_STORE = os.environ.get("OMICAIRN_STORE")

DATA_LOCAL_FOLDER = os.path.join(OMICAIRN_STORE, "data")
create_folder_if_not_exist(DATA_LOCAL_FOLDER)

DEFAULT_FIGURE_SUFFIX = "png"

##############################################

class PorterType(AugmentedEnum):
    S3_PORTER = "s3-porter"

PORTER_TYPE = os.environ.get("PORTER_TYPE", PorterType.S3_PORTER.value)

COMPUTATION_OUTPUT_FOLDER_PREFIX = "computation_output_file"

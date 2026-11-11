import os

OMICAIRN_CODE_SPACE = os.environ.get('OMICAIRN_CODE_SPACE')
OMICAIRN_STORE = os.environ.get('OMICAIRN_STORE')
INTERPRETER_PATH = os.path.join(OMICAIRN_STORE, "computation/bin/python3")

COMPUTATION_SCRIPT_ENTRY = os.path.join(
    OMICAIRN_CODE_SPACE, "computation_script/index.py")

from enum import Enum
import os

LONG_TEXT_MAX_LEN = 1073741823


class AugmentedEnum(Enum):
    def __hash__(self):
        return self.value.__hash__()

    def __eq__(self, other):
        if isinstance(other, type(self)) or isinstance(other, str):
            return self.value == other
        return False

    def __str__(self) -> str:
        return self.value


def create_folder_if_not_exist(folder_path):
    # Create the folder if it does not exist
    os.makedirs(folder_path, exist_ok=True)


class GenerationMode(AugmentedEnum):
    MIXED = "mixed"
    ONLY_EXISTING = "only_existing"
    ONLY_NEW = "only_new"


DEPLOY_ENV = os.environ.get("DEPLOY_ENV", "dev")
MAIN_SERVER_HOST = os.environ.get("MAIN_SERVER_HOST")
COMPUTATION_SERVER_HOST = os.environ.get("COMPUTATION_SERVER_HOST")
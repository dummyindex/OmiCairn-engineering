from enum import Enum
import os


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
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)


COMPUTATION_ID = os.getenv("COMPUTATION_ID")

BUCKET_NAME = os.environ.get("BUCKET_NAME")

NODE_ID = os.environ.get("NODE_ID")

USER_ID = os.getenv("USER_ID", None)
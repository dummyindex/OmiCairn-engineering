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

class DataState(AugmentedEnum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PREHANDLING = "prehandling"
    ERROR = "error"
    OK = "ok"

class PorterType(AugmentedEnum):
    S3_PORTER = "s3-porter"

class CreatedFrom(AugmentedEnum):
    UPLOAD = "upload"
    COMPUTATION = "computation"

class UploadType(AugmentedEnum):
    FASTQ = "fastq"
    TEN_X = "10x"
    ASSEMBLED = "assembled"
    ANNDATA = "anndata"
    GENERAL = "general"


PORTER_TYPE = PorterType.S3_PORTER.value

BUCKET_NAME = os.environ.get("BUCKET_NAME")

DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")
DB_PORT = os.environ.get("DB_PORT")

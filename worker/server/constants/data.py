from constants.common import AugmentedEnum


class Species(AugmentedEnum):
    FISH = "Fish"
    MOUSE = "Mus musculus (Mouse)"
    HUMAN = "Homo sapiens (Human)"


class UploadType(AugmentedEnum):
    FASTQ = "fastq"
    ASSEMBLED = "assembled"
    ANNDATA = "anndata"
    GENERAL = "general"


class CreatedFrom(AugmentedEnum):
    UPLOAD = "upload"
    COMPUTATION = "computation"


class DataListFetchMode(AugmentedEnum):
    ALL = "all"
    COLLECTED = "collected"
    UPLOADED = "uploaded"
    IMPORTED = "imported"
    PUBLIC = "public"


class DataState(AugmentedEnum):
    UPLOADING = "uploading"
    WAITING = "waiting"
    PREHANDLING = "prehandling"
    ERROR = "error"
    OK = "ok"

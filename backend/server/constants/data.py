from constants.common import AugmentedEnum


class Species(AugmentedEnum):
    FISH = "Fish"
    MOUSE = "Mus musculus (Mouse)"
    HUMAN = "Homo sapiens (Human)"
    OTHER = "Other species"


class UploadType(AugmentedEnum):
    FASTQ = "fastq"
    TEN_X = "10x"
    ASSEMBLED = "assembled"
    ANNDATA = "anndata"
    GENERAL = "general"

class UploadFromType(AugmentedEnum):
    FROMASSEMBLED = 'from assembled'
    FROMUPLOADEDDIRECTLY = 'from uploaded directly'
    FROMFASTQ = 'from fastq'
    FROM10X = 'from 10x'
    FROM_SPACERANGER_COUNT = 'from space ranger count'
    FROM_SPACERANGER_AGGR = 'from space ranger aggr'
    THIRD_PARTY_DATA = 'third_party_data'
    FROMSEURATOBJECTRDS = 'from seurat object rds'

class CreatedFrom(AugmentedEnum):
    UPLOAD = "upload"
    COMPUTATION = "computation"


class DataListFetchMode(AugmentedEnum):
    ALL = "all"
    COLLECTED = "collected"
    UPLOADED = "uploaded"
    IMPORTED = "imported"
    PUBLIC = "public"
    STATE = "state"
    PAGE_OF_ALL = "page-of-all"

class DataState(AugmentedEnum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PREHANDLING = "prehandling"
    ERROR = "error"
    OK = "ok"

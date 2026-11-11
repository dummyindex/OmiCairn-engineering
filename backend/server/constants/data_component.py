from constants.common import AugmentedEnum


class ToBeAssembleDataComponentType(AugmentedEnum):
    X = "X"
    LAYERS = "layers"
    LAYER_UNSPLICED = "unspliced"
    LAYER_SPLICED = "spliced"
    OBS = "obs"
    OBSM = "obsm"
    OBSP = "obsp"
    VAR = "var"
    VARP = "varp"
    VARM = "varm"
    UNS = "uns"

class TenXOutsComponentType(AugmentedEnum):
    pass

class DataComponentUploadState(AugmentedEnum):
    NOT_IPLOADED = "not uploaded"
    UPLOADED = "uploaded"
    UPLOADING = "uploading"

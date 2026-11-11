from sss.porter import Porter
from constants.sss import PORTER_TYPE, PorterType
from sss.porter_impl.s3_porter import S3Porter


class PorterFactory:
    @staticmethod
    def create_porter() -> Porter:
        if PORTER_TYPE == PorterType.S3_PORTER.value:
            return S3Porter()
        else:
            raise NotImplementedError("porter type not implemented")

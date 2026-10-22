from sss.porter import Porter
from sss.porter_impl.s3_porter import S3Porter

class PorterFactory:
    @staticmethod
    def create_porter() -> Porter:
        return S3Porter()

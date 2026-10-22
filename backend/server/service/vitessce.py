from sss.porter_factory import PorterFactory
from constants.sss import BUCKET_NAME
class VitessceService:
    
    def prepare_presigned_url_from_raw_url(self, raw_url: str):
        porter = PorterFactory.create_porter()
        # parse object_key from raw_url; raw_url format: https://[BUCKET_NAME].s3.amazonaws.com/[object_key]
        object_key = raw_url.split(BUCKET_NAME + '.s3.amazonaws.com/')[1]
        porter.set_operation_target(object_key)
        return porter.get_presigned_url(60 * 60)
    
vitessce_service = VitessceService()
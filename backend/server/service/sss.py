from sss.porter_factory import PorterFactory
from uuid import uuid4

class SssService:
    def complete_multipart_upload(self, object_key, upload_id, part_list):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        porter.complete_multipart_upload(upload_id, part_list)

    def abort_multipart_upload(self, object_key, upload_id):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        porter.abort_multipart_upload(upload_id)

    def generate_temp_upload_info(self, file_name, file_size):
        temp_object_key = f"temp-upload/{uuid4()}/{file_name}"
        porter = PorterFactory.create_porter()
        porter.set_operation_target(temp_object_key)
        return porter.get_presigned_post(file_size=file_size, expiration=60 * 60 * 24)

sss_service = SssService()

from constants.sss import BUCKET_NAME
from sss.porter_factory import PorterFactory

class UserSpaceWaiter:
    def __init__(self, user_id):
        self.user_id = user_id

    def delete_file(self, prefix: str, file_name: str):
        prefix = prefix.strip("/")
        if len(prefix) == 0:
            object_key = f"user-space/{self.user_id}/{file_name}"
        else:
            object_key = f"user-space/{self.user_id}/{prefix}/{file_name}"
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        porter.remove_file()

    def list_folder(self, prefix: str):
        prefix = prefix.strip("/")
        if len(prefix) == 0:
            object_key = f"user-space/{self.user_id}/"
        else:
            object_key = f"user-space/{self.user_id}/{prefix}/"
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        return porter.list_files('', 1000, False)

    def delete_folder(self, prefix: str, folder_name: str):
        prefix = prefix.strip("/")
        if len(prefix) == 0:
            object_key = f"user-space/{self.user_id}/{folder_name}"
        else:
            object_key = f"user-space/{self.user_id}/{prefix}/{folder_name}"
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        file_list = porter.list_files()
        for file_name in file_list:
            self.delete_file(prefix, file_name)

    def fetch_upload_info(self, prefix: str, file_name: str, file_size):
        prefix = prefix.strip("/")
        if len(prefix) == 0:
            object_key = f"user-space/{self.user_id}/{file_name}"
        else:
            object_key = f"user-space/{self.user_id}/{prefix}/{file_name}"
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        return porter.get_presigned_post(file_size, 60 * 60)

    def fetch_download_info(self, prefix: str, file_name: str):
        prefix = prefix.strip("/")
        if len(prefix) == 0:
            object_key = f"user-space/{self.user_id}/{file_name}"
        else:
            object_key = f"user-space/{self.user_id}/{prefix}/{file_name}"
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        return porter.get_presigned_url(60 * 60)

    def collect_file(self, prefix: str, file_name: str):
        prefix = prefix.strip("/")
        if len(prefix) == 0:
            object_key = f"user-space/{self.user_id}/{file_name}"
        else:
            object_key = f"user-space/{self.user_id}/{prefix}/{file_name}"
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        porter.update_metadata(object_key, {"collected": True})

    def get_file_information(self, prefix, file_name):
        prefix = prefix.strip("/")
        if len(prefix) == 0:
            object_key = f"user-space/{self.user_id}/{file_name}"
        else:
            object_key = f"user-space/{self.user_id}/{prefix}/{file_name}"
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        return porter.get_head(object_key)

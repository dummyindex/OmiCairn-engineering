import os

from constants.sss import ADATA_FOLDER_PREFIX, BUCKET_NAME, DATA_SPACE_FOLDER_PREFIX, FIGURE_FOLDER_PREFIX
from constants.local_store import DATA_FOLDER
from sss.porter_factory import PorterFactory
from log.logger_factory import logger_factory

logger = logger_factory.create_logger("DataWaiter")



class DataWaiter:
    def __init__(self, adata_id) -> None:
        self.adata_id = adata_id

    def _generate_local_path(self):
        return os.path.join(DATA_FOLDER, f"{self.adata_id}.h5ad")

    def get_local_path(self):
        return self._generate_local_path()

    def remove_data(self):
        local_path = self._generate_local_path()
        if os.path.exists(local_path):
            os.remove(local_path)
        porter = PorterFactory.create_porter()
        # Delete the h5ad file
        porter.set_operation_target(f"{ADATA_FOLDER_PREFIX}/{self.adata_id}.h5ad")
        if porter.check_file():
            porter.remove_file()

        # Delete scattered data: data components + loose files
        component_key_prefix = f"{ADATA_FOLDER_PREFIX}/{self.adata_id}-"
        porter.set_operation_target(component_key_prefix)
        finished = False
        max_keys = 1000
        while not finished:
            component_key_list = porter.list_files(
                start_after=component_key_prefix,
                max_keys=max_keys,
                recursive=True
            )
            component_key_list = component_key_list if component_key_list is not None else []
            for component_key in component_key_list:
                porter.set_operation_target(component_key)
                porter.remove_file()
            if len(component_key_list) < max_keys:
                finished = True
            else:
                porter.set_operation_target(component_key_list[-1])

        # Delete the data space
        porter.set_operation_target(f"{DATA_SPACE_FOLDER_PREFIX}/{self.adata_id}/")
        finished = False
        max_keys = 1000
        while not finished:
            component_key_list = porter.list_files(
                start_after=f"{DATA_SPACE_FOLDER_PREFIX}/{self.adata_id}/",
                max_keys=max_keys,
                recursive=True
            )
            component_key_list = component_key_list if component_key_list is not None else []
            for component_key in component_key_list:
                porter.set_operation_target(component_key)
                porter.remove_file()
            if len(component_key_list) < max_keys:
                finished = True
            else:
                porter.set_operation_target(component_key_list[-1])

    def remove_data_component(self, upload_type, component_type):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{ADATA_FOLDER_PREFIX}/{self.adata_id}-{upload_type}-{component_type}")
        fitable_object_keys = porter.list_files()
        for fitable_object_key in fitable_object_keys:
            porter.set_operation_target(fitable_object_key)
            porter.remove_file()


    def fetch_h5ad_upload_info(self, file_size):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{ADATA_FOLDER_PREFIX}/{self.adata_id}.h5ad")
        return porter.get_multipart_upload_presigned_url(
            file_size,
            13 * 60 * 60
        )

    def fetch_h5ad_download_info(self):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{ADATA_FOLDER_PREFIX}/{self.adata_id}.h5ad")
        return porter.get_presigned_url(60 * 60)

    def fetch_data_component_upload_info(self, file_size, upload_type, component_type, filename_suffix):
        filename_suffix = "" if not filename_suffix or filename_suffix == "." else (f".{filename_suffix}" if filename_suffix[0] != "." else filename_suffix)
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{ADATA_FOLDER_PREFIX}/{self.adata_id}-{upload_type}-{component_type}{filename_suffix}")
        return porter.get_presigned_post(file_size, 24 * 60 * 60)

    def fetch_data_component_download_info(self, upload_type, component_type):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{ADATA_FOLDER_PREFIX}/{self.adata_id}-{upload_type}-{component_type}")
        fitable_object_keys = porter.list_files()
        if len(fitable_object_keys) == 0:
            return None
        porter.set_operation_target(fitable_object_keys[0])
        return porter.get_presigned_url(60 * 60)

    def fetch_component_list(self, upload_type):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{ADATA_FOLDER_PREFIX}/{self.adata_id}-{upload_type}-")
        return porter.list_files()

    def edit_data_component_type(self, upload_type, component_type, new_component_type):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{ADATA_FOLDER_PREFIX}/{self.adata_id}-{upload_type}-{component_type}")
        fitable_object_keys = porter.list_files()
        result = []
        for fitable_object_key in fitable_object_keys:
            new_object_key = fitable_object_key.replace(f"-{component_type}", f"-{new_component_type}")
            porter.set_operation_target(new_object_key)
            porter.copy_file(BUCKET_NAME, fitable_object_key)
            porter.set_operation_target(fitable_object_key)
            porter.remove_file()
            result.append({
                "old_object_key": fitable_object_key,
                "new_object_key": new_object_key
            })
        return result

    def is_exist(self):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{ADATA_FOLDER_PREFIX}/{self.adata_id}.h5ad")
        return porter.check_file()

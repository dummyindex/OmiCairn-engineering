import os

from constants.sss import ADATA_FOLDER_PREFIX, BUCKET_NAME, NODE_SPACE_FOLDER_PREFIX, FIGURE_FOLDER_PREFIX
from constants.local_store import DATA_FOLDER
from sss.porter_factory import PorterFactory
from log.logger_factory import logger_factory

logger = logger_factory.create_logger("NodeSpaceWaiter")

class NodeSpaceWaiter():
    def __init__(self, node_id) -> None:
        self.node_id = node_id

    def list_params_files(self):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{NODE_SPACE_FOLDER_PREFIX}/{self.node_id}/params-files/")
        result = porter.list_file_infos()
        files = result.get("Contents", [])
        return files

    def info_param_file_key(self, file_name):
        return f"{NODE_SPACE_FOLDER_PREFIX}/{self.node_id}/params-files/{file_name}"

    def generate_param_file_presigned_post(self, file_name, file_size):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{NODE_SPACE_FOLDER_PREFIX}/{self.node_id}/params-files/{file_name}")
        return porter.get_presigned_post(file_size, 60 * 60)

    def generate_param_file_presigned_url(self, file_name):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{NODE_SPACE_FOLDER_PREFIX}/{self.node_id}/params-files/{file_name}")
        return porter.get_presigned_url(60 * 60)
    
    def delete_param_file(self, file_name):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{NODE_SPACE_FOLDER_PREFIX}/{self.node_id}/params-files/{file_name}")
        porter.remove_file()

    def is_param_file_exist(self, file_name):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{NODE_SPACE_FOLDER_PREFIX}/{self.node_id}/params-files/{file_name}")
        return porter.check_file()
    
    def copy_from_another_node_space(self, another_node_id):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{NODE_SPACE_FOLDER_PREFIX}/{another_node_id}/")
        source_files = porter.list_files(recursive=True)
        for source_file in source_files:
            new_key = source_file.replace(f"{NODE_SPACE_FOLDER_PREFIX}/{another_node_id}/", f"{NODE_SPACE_FOLDER_PREFIX}/{self.node_id}/")
            porter.set_operation_target(new_key)
            porter.copy_file(BUCKET_NAME, source_file)

    def delete_all_files(self):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{NODE_SPACE_FOLDER_PREFIX}/{self.node_id}/")
        file_list = porter.list_files(recursive=True)
        for file in file_list:
            porter.set_operation_target(file)
            porter.remove_file()


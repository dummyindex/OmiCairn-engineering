from dao.data import data_dao
from dao.computation import computation_dao
from sss.porter import Porter
from sss.porter_factory import PorterFactory
from constants.sss import ADATA_FOLDER_PREFIX
from constants.sss import FIGURE_FOLDER_PREFIX
from constants.sss import COMPUTATION_OUTPUT_FOLDER_PREFIX
from constants.sss import DATA_SPACE_FOLDER_PREFIX
from constants.sss import FUNCTION_BLOCK_VERSION_PREFIX
from log.logger_factory import logger_factory
from tool.gpt_space_manager import GptSpaceManager
import tempfile

logger = logger_factory.create_logger("system_file_service")


class SystemFileService:

    def _handle_file_name(self, file_name: str):
        if file_name is None or len(file_name) == 0:
            return ''
        file_name = file_name.strip("/")
        return file_name

    def get_information(self, object_key, porter: Porter):
        head = porter.get_head(object_key)
        metadata = head.get("Metadata")
        if object_key.endswith("/"):
            folder_name = object_key[:-1].split("/")[-1]
            return {
                "object_key": object_key,
                "size": "-",
                "last_modified": "-",
                "collected": False,
                "mime_type": "folder",
                "file_name": folder_name
            }
        else:
            file_name = object_key.split("/")[-1]
            return {
                "object_key": object_key,
                "size": head.get("ContentLength"),
                "last_modified": head.get("LastModified"),
                "collected": metadata.get("collected", False),
                "mime_type": file_name.split(".")[-1] if "." in file_name else "-",
                "file_name": file_name
            }

    def get_data_files_view(self, user_id, prefix: str, start_after_file_name: str = None):
        start_after_file_name = self._handle_file_name(start_after_file_name)
        if prefix is None or not prefix or prefix == "/":
            data_user_relation_list = data_dao.find_user_relation_by_user_id(user_id)
            suitable_prefix_set = [f"{ADATA_FOLDER_PREFIX}/{data_user_relation.data_id}" for data_user_relation in data_user_relation_list]
            start_after_object_key = f"{ADATA_FOLDER_PREFIX}/{prefix}/{start_after_file_name}"
            result_object_key_list = []
            result_counts = 0
            max_keys = 50
            porter = PorterFactory.create_porter()
            porter.set_operation_target(f"{ADATA_FOLDER_PREFIX}/")
            while True:
                object_key_list = porter.list_files(start_after=start_after_object_key, max_keys=max_keys, recursive=False)
                if len(object_key_list) == 0:
                    break
                for object_key in object_key_list:
                    start_after_object_key = object_key
                    if object_key.startswith(tuple(suitable_prefix_set)):
                        result_object_key_list.append(object_key)
                        result_counts += 1
                    if result_counts == max_keys:
                        break
                if result_counts == max_keys:
                    break
            has_more = len(result_object_key_list) == max_keys
            result_object_list = [
                self.get_information(object_key)
                for object_key in result_object_key_list
            ]
            return {
                "objects": result_object_list,
                "next_start_after": start_after_object_key if has_more else None,
                "has_more": has_more,
                "total": len(result_object_key_list)
            }
        else:
            porter = PorterFactory.create_porter()
            porter.set_operation_target(f"{ADATA_FOLDER_PREFIX}/{prefix}/")
            max_keys = 50
            start_after_object_key = f"{ADATA_FOLDER_PREFIX}/{prefix}/{start_after_file_name}"
            object_key_list = porter.list_files(start_after=start_after_object_key, max_keys=max_keys, recursive=False)
            object_list = [
                self.get_information(object_key) for object_key in object_key_list
            ]
            has_more = len(object_key_list) == max_keys
            return {
                "objects": object_list,
                "next_start_after": None if not has_more else object_key_list[-1],
                "has_more": has_more,
                "total": len(object_key_list)
            }

    def get_data_space_files_view(self, user_id, prefix: str, start_after_file_name: str = None):
        start_after_file_name = self._handle_file_name(start_after_file_name)
        if prefix is None or not prefix or prefix == "/":
            data_user_relation_list = data_dao.find_user_relation_by_user_id(user_id)
            suitable_prefix_set = [f"{DATA_SPACE_FOLDER_PREFIX}/{data_user_relation.data_id}" for data_user_relation in data_user_relation_list]
            start_after_object_key = f"{DATA_SPACE_FOLDER_PREFIX}/{prefix}/{start_after_file_name}"
            result_object_key_list = []
            result_counts = 0
            max_keys = 50
            porter = PorterFactory.create_porter()
            porter.set_operation_target(f"{DATA_SPACE_FOLDER_PREFIX}/")
            while True:
                object_key_list = porter.list_files(start_after=start_after_object_key, max_keys=max_keys, recursive=False)
                if len(object_key_list) == 0:
                    break
                for object_key in object_key_list:
                    start_after_object_key = object_key
                    if object_key.startswith(tuple(suitable_prefix_set)):
                        result_object_key_list.append(object_key)
                        result_counts += 1
                    if result_counts == max_keys:
                        break
                if result_counts == max_keys:
                    break
            has_more = len(result_object_key_list) == max_keys
            result_object_list = [
                self.get_information(object_key)
                for object_key in result_object_key_list
            ]
            return {
                "objects": result_object_list,
                "next_start_after": start_after_object_key if has_more else None,
                "has_more": has_more,
                "total": len(result_object_key_list)
            }
        else:
            porter = PorterFactory.create_porter()
            porter.set_operation_target(f"{DATA_SPACE_FOLDER_PREFIX}/{prefix}/")
            max_keys = 50
            start_after_object_key = f"{DATA_SPACE_FOLDER_PREFIX}/{prefix}/{start_after_file_name}"
            object_key_list = porter.list_files(start_after=start_after_object_key, max_keys=max_keys, recursive=False)
            has_more = len(object_key_list) == max_keys
            object_list = [
                self.get_information(object_key) for object_key in object_key_list
            ]
            return {
                "objects": object_list,
                "next_start_after": None if not has_more else object_key_list[-1],
                "has_more": has_more,
                "total": len(object_key_list)
            }

    def get_presigned_url(self, object_key):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        return porter.get_presigned_url(60 * 60)

    def get_computation_output_files_view(self, user_id, prefix: str, start_after_file_name: str = None):
        start_after_file_name = self._handle_file_name(start_after_file_name)
        if prefix is None or not prefix or prefix == "/":
            computation_user_relation_list = computation_dao.find_user_relation_by_user_id(user_id)
            suitable_prefix_set = [f"{COMPUTATION_OUTPUT_FOLDER_PREFIX}/{computation_user_relation.computation_id}" for computation_user_relation in computation_user_relation_list]
            start_after_object_key = f"{COMPUTATION_OUTPUT_FOLDER_PREFIX}/{prefix}/{start_after_file_name}"
            result_object_key_list = []
            result_counts = 0
            max_keys = 50
            porter = PorterFactory.create_porter()
            porter.set_operation_target(f"{COMPUTATION_OUTPUT_FOLDER_PREFIX}/")
            while True:
                object_key_list = porter.list_files(start_after=start_after_object_key, max_keys=max_keys, recursive=False)
                if len(object_key_list) == 0:
                    break
                for object_key in object_key_list:
                    start_after_object_key = object_key
                    if object_key.startswith(tuple(suitable_prefix_set)):
                        result_object_key_list.append(object_key)
                        result_counts += 1
                    if result_counts == max_keys:
                        break
                if result_counts == max_keys:
                    break
            has_more = len(result_object_key_list) == max_keys
            result_object_list = [
                self.get_information(object_key)
                for object_key in result_object_key_list
            ]
            return {
                "objects": result_object_list,
                "next_start_after": start_after_object_key if has_more else None,
                "has_more": has_more,
                "total": len(result_object_key_list)
            }
        else:
            porter = PorterFactory.create_porter()
            porter.set_operation_target(f"{COMPUTATION_OUTPUT_FOLDER_PREFIX}/{prefix}/")
            max_keys = 50
            start_after_object_key = f"{COMPUTATION_OUTPUT_FOLDER_PREFIX}/{prefix}/{start_after_file_name}"
            object_key_list = porter.list_files(start_after=start_after_object_key, max_keys=max_keys, recursive=False)
            has_more = len(object_key_list) == max_keys
            object_list = [
                self.get_information(object_key) for object_key in object_key_list
            ]
            return {
                "objects": object_list,
                "next_start_after": None if not has_more else object_key_list[-1],
                "has_more": has_more,
                "total": len(object_key_list)
            }

    def get_gpt_space_files_view(self, user_id, prefix: str, search_key: str = None):
        gpt_space_manager = GptSpaceManager()
        file_list = gpt_space_manager.list_files(user_id, prefix, search_key, False)
        return file_list

    def upload_gpt_space_file(self, user_id, prefix: str, file_name: str, file):
        gpt_space_manager = GptSpaceManager()
        gpt_space_manager.upload_file(user_id, file, prefix, file_name)

    def download_gpt_space_file(self, user_id, prefix, file_name: str):
        gpt_space_manager = GptSpaceManager()
        return gpt_space_manager.download_file(user_id, prefix, file_name)

    def delete_gpt_space_file(self, user_id, prefix, file_name: str):
        gpt_space_manager = GptSpaceManager()
        gpt_space_manager.delete_file(user_id, prefix, file_name)

    def copy_to_gpt_space(self, user_id, prefix, source_object_key):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(source_object_key)
        temp_path = tempfile.mkdtemp()
        porter.fetch_file(temp_path)
        gpt_space_manager = GptSpaceManager()
        gpt_space_manager.upload_file(user_id, temp_path, prefix, source_object_key.split("/")[-1])

    def collect(self, object_key):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        porter.update_metadata(object_key, {"collected": True})

system_file_service = SystemFileService()

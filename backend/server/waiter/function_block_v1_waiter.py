from sss.porter_factory import PorterFactory
from constants.sss import FUNCTION_BLOCK_VERSION_PREFIX, BUCKET_NAME
import json

from log.logger_factory import logger_factory

logger = logger_factory.create_logger("FunctionBlockV1Waiter")

class FunctionBlockV1Waiter:
    def __init__(
        self,
        function_block_version_id,
        programming_language=None,
    ) -> None:
        if programming_language is None:
            logger.warning(
                f"Programming language is not specified for function block version {function_block_version_id}. Defaulting to None.")
        self.function_block_version_id = function_block_version_id
        self.programming_language = programming_language
        self.requirements_file_name = "requirements.txt" if programming_language == "Python" else "libs.R"
        self.core_code_file_name = "function_block.py" if programming_language == "Python" else "function_block.R"
        self.install_script_file_name = "install.sh"
        self.static_config_file_name = "static-config.json"


    def fetch_static_config(self):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/static-config.json")
        buffer = porter.fetch_file_stream()
        content = str(buffer, "utf-8")
        return json.loads(content)
    
    def fetch_core_code(self):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/{self.core_code_file_name}")
        buffer = porter.fetch_file_stream()
        content = str(buffer, "utf-8")
        return content
        
    def fetch_requirement_content(self):
        try:
            porter = PorterFactory.create_porter()
            porter.set_operation_target(f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/{self.requirements_file_name}")
            buffer = porter.fetch_file_stream()
            content = str(buffer, "utf-8")
            return content
        except Exception as e:
            if "NoSuchKey" in str(e):
                return None
    
    def fetch_install_script(self):
        try:
            porter = PorterFactory.create_porter()
            porter.set_operation_target(f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/{self.install_script_file_name}")
            buffer = porter.fetch_file_stream()
            content = str(buffer, "utf-8")
            return content
        except Exception as e:
            if "NoSuchKey" in str(e):
                return None

    def get_raw_fb_zip_upload_info(self, file_size):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}.raw-fb-zip")
        return porter.get_presigned_post(file_size, 60 * 60)

    def fetch_doc(self):
        pass

    def fetch_preview_images_list(self):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/preview-images/")
        images = porter.list_files(recursive=False)
        image_urls = []
        for image_object_key in images:
            porter.set_operation_target(image_object_key)
            image_urls.append(porter.get_presigned_url(60 * 60))
        return image_urls
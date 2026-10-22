from sss.porter_factory import PorterFactory
from constants import FUNCTION_BLOCK_VERSION_PREFIX, BUCKET_NAME
import json
from logger_factory import LoggerFactory

logger = LoggerFactory.get_logger(
    "FunctionBlockV1Waiter In HandleDynamicGeneration")


class FunctionBlockV1Waiter:
    def __init__(
        self,
        function_block_version_id,
        program_language="Python"
    ) -> None:
        self.function_block_version_id = function_block_version_id
        self.programming_language = program_language

    def rewrite_core_code(self, code):
        porter = PorterFactory.create_porter()
        # Check if the code is python or R
        try:
            if self.programming_language == "Python":
                porter.set_operation_target(
                    f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/function_block.py")
            elif self.programming_language == "R":
                porter.set_operation_target(
                    f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/function_block.R")
            elif self.programming_language == "Bash":
                porter.set_operation_target(
                    f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/function_block.sh")
            else:
                raise ValueError("Unsupported programming language")
            porter.save_file_text(code)
        except Exception as e:
            logger.error(e)

    def rewrite_static_config(self, config):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/static-config.json")
        porter.save_file_text(json.dumps(config))

    def rewrite_requirement_file(self, requirements_content):
        porter = PorterFactory.create_porter()
        try:
            if self.programming_language == "Python":
                porter.set_operation_target(
                    f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/requirements.txt")
            elif self.programming_language == "R":
                porter.set_operation_target(
                    f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/libs.R")
            elif self.programming_language == "Bash":
                porter.set_operation_target(
                    f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/libs.sh")
            else:
                raise ValueError("Unsupported programming language")
            porter.save_file_text(requirements_content)
        except Exception as e:
            logger.error(e)

    def fetch_doc(self):
        pass

    def copy(self, source_fbv_id):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{source_fbv_id}/")
        file_list = porter.list_files(recursive=True)
        for file in file_list:
            new_key = file.replace(
                '/' + str(source_fbv_id) + '/', '/' + str(self.function_block_version_id) + '/')
            porter.set_operation_target(new_key)
            porter.copy_file(file)

    def add_file(self, file_name, content):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"{FUNCTION_BLOCK_VERSION_PREFIX}/{self.function_block_version_id}/{file_name}")
        porter.save_file_text(content)
from sss.porter_factory import PorterFactory
from constants.sss import BUCKET_NAME
from log.logger_factory import LoggerFactory
import json

logger = LoggerFactory.get_logger("DynamicGenerationWaiter")


class DynamicGenerationWaiter:
    def __init__(self, dynamic_generation_id) -> None:
        self.dynamic_generation_id = dynamic_generation_id

    def save_log(self, node_id, prompt, output):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"dynamic_generation/{self.dynamic_generation_id}/{node_id}/prompt.json")
        porter.save_file_text(prompt)
        porter.set_operation_target(
            f"dynamic_generation/{self.dynamic_generation_id}/{node_id}/output.json")
        porter.save_file_text(output)

    def fetch_log(self, node_id):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"dynamic_generation/{self.dynamic_generation_id}/{node_id}/prompt.json")
        prompt = porter.fetch_file_text()
        porter.set_operation_target(
            f"dynamic_generation/{self.dynamic_generation_id}/{node_id}/output.json")
        output = porter.fetch_file_text()
        return prompt, output

    def get_files(self):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"dynamic_generation/{self.dynamic_generation_id}/files/")
        file_list = porter.list_files()
        result = []
        for file_key in file_list:
            if file_key.endswith("/"):
                continue
            porter.set_operation_target(file_key)
            presigned_link = porter.get_presigned_url(expiration=3600)
            link = presigned_link
            file_name = file_key.split("/")[-1]
            file_info = {
                "name": file_name,
                "link": link
            }
            result.append(file_info)

        return result

    def catch_files(self, file_list):
        porter = PorterFactory.create_porter()
        for file_info in file_list:
            # Handle both string (object key directly) and dict formats
            if isinstance(file_info, str):
                source_key = file_info
            else:
                source_key = file_info.get("object_key")
            if not source_key:
                continue
            file_name = source_key.split("/")[-1]
            porter.set_operation_target(
                f"dynamic_generation/{self.dynamic_generation_id}/files/{file_name}"
            )
            try:
                porter.copy_file(BUCKET_NAME, source_key)
            except Exception as e:
                logger.warning(f"Failed to copy file {source_key}: {e}. Skipping.")

    def store_plan(self, node_id, plan_data):
        try:
            porter = PorterFactory.create_porter()
            porter.set_operation_target(
                f"dynamic_generation/{self.dynamic_generation_id}/{node_id}/plan.json"
            )
            plan_json = json.dumps(plan_data, indent=2)
            porter.save_file_text(plan_json)
        except Exception as e:
            raise e
        
    def retrieve_plan(self, node_id):
        try:
            porter = PorterFactory.create_porter()
            porter.set_operation_target(
                f"dynamic_generation/{self.dynamic_generation_id}/{node_id}/plan.json"
            )
            plan_json = porter.fetch_file_text()
            plan_data = json.loads(plan_json)
            return plan_data
        except Exception as e:
            raise e
        
    def retrieve_plan_url(self, node_id):
        try:
            porter = PorterFactory.create_porter()
            porter.set_operation_target(
                f"dynamic_generation/{self.dynamic_generation_id}/{node_id}/plan.json"
            )
            presigned_url = porter.get_presigned_url(expiration=3600)
            return {
                "presigned_url": presigned_url,
            }
        except Exception as e:
            raise e

    def delete_plan(self, node_id):
        """Delete the plan file from S3."""
        try:
            porter = PorterFactory.create_porter()
            porter.set_operation_target(
                f"dynamic_generation/{self.dynamic_generation_id}/{node_id}/plan.json"
            )
            porter.remove_file()
        except Exception as e:
            raise e
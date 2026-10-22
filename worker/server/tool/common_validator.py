import json
import re
from log.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("common_validator")


class CommonValidator:
    @staticmethod
    def validate_dynamic_generation_plan_output_json(json_data_text):
        """
        Parse-level check of the LLM plan response.

        NOTE: this only verifies that the response is a JSON object; it does not
        validate the plan schema. `is_valid` recorded in session logs therefore
        means "parseable JSON object", not "schema-valid plan".

        Returns:
            tuple: (is_valid: bool, errors: list)
        """
        try:
            json_data = json.loads(json_data_text)
        except Exception as e:
            return False, [f"JSON decode error: {str(e)} - {json_data_text}"]

        if not isinstance(json_data, dict):
            return False, ["Plan response is not a JSON object"]
        return True, []

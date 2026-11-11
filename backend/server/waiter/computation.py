import json
from sss.porter_factory import PorterFactory


class ComputationWaiter:
    def __init__(self, computation_id) -> None:
        self.computation_id = computation_id

    def check_options_exists(self):
        porter = PorterFactory.create_porter()
        object_key = f"computation_options/{self.computation_id}"
        porter.set_operation_target(object_key)
        return porter.check_file()

    def save_options(self, options: dict):
        options = options or {}
        porter = PorterFactory.create_porter()
        object_key = f"computation_options/{self.computation_id}"
        porter.set_operation_target(object_key)
        porter.save_file_text(json.dumps(options))

    def get_options(self):
        porter = PorterFactory.create_porter()
        object_key = f"computation_options/{self.computation_id}"
        porter.set_operation_target(object_key)
        buffer = porter.fetch_file_stream()
        string = str(buffer, "utf-8")
        return json.loads(string) if string else {}

    def check_result_exists(self):
        porter = PorterFactory.create_porter()
        object_key = f"computation_result/{self.computation_id}"
        porter.set_operation_target(object_key)
        return porter.check_file()

    def save_result(self, result: dict):
        result = result or {}
        porter = PorterFactory.create_porter()
        object_key = f"computation_result/{self.computation_id}"
        porter.set_operation_target(object_key)
        porter.save_file_text(json.dumps(result))

    def get_result(self):
        porter = PorterFactory.create_porter()
        object_key = f"computation_result/{self.computation_id}"
        porter.set_operation_target(object_key)
        exists = porter.check_file()
        if not exists:
            return dict()
        buffer = porter.fetch_file_stream()
        string = str(buffer, "utf-8")
        return json.loads(string) if string else {}

    def save_log(self, log: str):
        porter = PorterFactory.create_porter()
        object_key = f"computation_log/{self.computation_id}"
        porter.set_operation_target(object_key)
        porter.save_file_text(log)

    def get_log(self, only_message=False, tail_n=None):

        porter = PorterFactory.create_porter()
        object_key = f"computation_log/{self.computation_id}"
        porter.set_operation_target(object_key)
        try:
            buffer = porter.fetch_file_stream()
            logs = str(buffer, "utf-8") if buffer else "[]"
            log_list = json.loads(logs) if logs else []
            if tail_n is not None:
                log_list = log_list[-tail_n:]
            if only_message:
                log_list = [log["message"] for log in log_list]
            return log_list
        except Exception as e:
            return []

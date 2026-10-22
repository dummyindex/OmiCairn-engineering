import json
from sss.porter_factory import PorterFactory

class ComputationOptionsWaiter:
    def __init__(self, computation_id:int) -> None:
        self.computation_id = computation_id
        self.porter = PorterFactory.create_porter()
        self.object_key = f"computation_options/{computation_id}"
        self.porter.set_operation_target(self.object_key)

    def check_file(self):
        return self.porter.check_file()
    
    def save_computation_options(self, options:dict):
        options = options or {}
        self.porter.save_file_text(json.dumps(options))

    def get_computation_options(self):
        buffer = self.porter.fetch_file_stream()
        string = str(buffer, "utf-8")
        return json.loads(string) if string else {}
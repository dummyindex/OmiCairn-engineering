from sss.porter_factory import PorterFactory
import json


class RetryProcessWaiter:
    def __init__(self, retry_process_id) -> None:
        self.retry_process_id = retry_process_id

    def save_node_computation_information(self, computation_id, node_computation_information):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"retry_process/{self.retry_process_id}/{computation_id}/node_computation_information.json")
        porter.save_file_text(json.dumps(node_computation_information))

    def save_parameters_fix_solution(self, computation_id, solution):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"retry_process/{self.retry_process_id}/{computation_id}/parameters-fix-solution.json")
        porter.save_file_text(json.dumps(solution))

    def save_code_fix_solution(self, computation_id, solution):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"retry_process/{self.retry_process_id}/{computation_id}/code-fix-solution.json")
        porter.save_file_text(json.dumps(solution))

    def save_result(self, computation_id, result):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"retry_process/{self.retry_process_id}/{computation_id}/result.json")
        porter.save_file_text(json.dumps(result))

    def save_a_session(self, bug_fixer_session_id, input_prompt, raw_response):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"retry_process/{self.retry_process_id}/{bug_fixer_session_id}/session.json")
        porter.save_file_text(json.dumps({
            "input_prompt": input_prompt,
            "raw_response": raw_response
        }))

    def get_one_stage_details(self, computation_id):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"retry_process/{self.retry_process_id}/{computation_id}/node_computation_information.json")
        node_computation_information_txt = porter.fetch_file_text()
        node_computation_information = json.loads(
            node_computation_information_txt) if node_computation_information_txt else None
        porter.set_operation_target(
            f"retry_process/{self.retry_process_id}/{computation_id}/input_prompt.txt")
        input_prompt = porter.fetch_file_text()
        porter.set_operation_target(
            f"retry_process/{self.retry_process_id}/{computation_id}/parameters-fix-solution.json")
        parameters_fix_solution_txt = porter.fetch_file_text()
        parameters_fix_solution = json.loads(
            parameters_fix_solution_txt) if parameters_fix_solution_txt else None
        porter.set_operation_target(
            f"retry_process/{self.retry_process_id}/{computation_id}/code-fix-solution.json")
        code_fix_solution_txt = porter.fetch_file_text()
        code_fix_solution = json.loads(
            code_fix_solution_txt) if code_fix_solution_txt else None
        porter.set_operation_target(
            f"retry_process/{self.retry_process_id}/{computation_id}/result.json")
        result_txt = porter.fetch_file_text()
        result = json.loads(result_txt) if result_txt else None
        return node_computation_information, input_prompt, parameters_fix_solution, code_fix_solution, result

    def get_prompt(self, computation_id):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"retry_process/{self.retry_process_id}/{computation_id}/input_prompt.txt")
        input_prompt = porter.fetch_file_text()
        return input_prompt

    def get_a_session(self, bug_fixer_session_id):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(
            f"retry_process/{self.retry_process_id}/{bug_fixer_session_id}/session.json")
        try:
            return porter.get_presigned_url(60 * 10)
        except Exception as e:
            return None
import json
from datetime import datetime, timedelta
from dao.data import data_dao
from dao.analysis import analysis_dao
from dao.task import task_dao
from dao.computation import computation_dao
from dao.llm_consumption import llm_consumption_dao
from dao.node import node_dao
from sss.porter_factory import PorterFactory
from model.computation_file_size import ComputationFileSize
from typing import List
from model.computation import Computation
from model.llm_consumption import LLMConsumption

from dao.computation import computation_dao
from dao.llm import llm_dao

def sum_computation_file_size(computation_file_size: ComputationFileSize):
    return sum([
        computation_file_size.log_size or 0,
        computation_file_size.options_size or 0,
        computation_file_size.report_size or 0,
        computation_file_size.result_size or 0,
        computation_file_size.output_size or 0,
        computation_file_size.review_error_size or 0,
        computation_file_size.figures_size or 0
    ])

class ConsumptionService:
    def get_s3_file_size_total_by_user(self, user_id):
        # Get the S3 file size details for a specific user
        # Computation related
        computation_file_size_list = computation_dao.find_computation_file_size_list_by_user_id(user_id)
        computation_total_size = sum([
            sum_computation_file_size(item) for item in computation_file_size_list
        ])

        # Group computation by month
        computation_by_month = {}
        for item in computation_file_size_list:
            if item.created_time:
                month_key = item.created_time.strftime("%Y-%m")
                if month_key not in computation_by_month:
                    computation_by_month[month_key] = 0
                computation_by_month[month_key] += sum_computation_file_size(item)

        # Data related
        data_size_list = data_dao.find_by_user_id(user_id)
        data_total_size = sum([
            data_item.data_size or 0 for data_item in data_size_list
        ])

        # Group data by month
        data_by_month = {}
        for data_item in data_size_list:
            if data_item.created_time:
                month_key = data_item.created_time.strftime("%Y-%m")
                if month_key not in data_by_month:
                    data_by_month[month_key] = 0
                data_by_month[month_key] += data_item.data_size or 0

        return {
            "total_computation_size": computation_total_size,
            "total_data_size": data_total_size,
            "computation_by_month": computation_by_month,
            "data_by_month": data_by_month
        }
    
    
    def get_s3_file_size_details_by_analysis(self, analysis_id, month):
        # computation
        computation_file_size_list = computation_dao.find_computation_file_size_list_by_analysis_id(analysis_id, month)
        # data
        data_list = data_dao.find_computation_result_by_analysis_id(analysis_id, month)
        return {
            "total_computation_size": sum([
                sum_computation_file_size(item) for item in computation_file_size_list
            ]),
            "total_data_size": sum([
                data_item.data_size or 0 for data_item in data_list
            ])
        }

    def get_s3_file_size_details_by_user(self, user_id, month):
        analysis_list = analysis_dao.find_by_user_id(user_id)
        result = []
        for analysis in analysis_list:
            result.append({
                "analysis_id": analysis.id,
                "analysis_name": analysis.name,
                "consumptions": self.get_s3_file_size_details_by_analysis(analysis.id, month)
            })
        return result

    def get_llm_consumptions_total_by_user(self, user_id):
        # Get the token details for a specific user
        consumption_list = llm_dao.list_consumptions(user_id)

        # Calculate total consumptions grouped by functionality and model
        result_dict = {}
        for consumption in consumption_list:
            if consumption.functionality not in result_dict:
                result_dict[consumption.functionality] = {}
            if consumption.model not in result_dict[consumption.functionality]:
                result_dict[consumption.functionality][consumption.model] = {
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "reasoning_tokens": 0,
                    "total_cost": 0.0
                }
            result_dict[consumption.functionality][consumption.model]["total_tokens"] += consumption.total_tokens or 0
            result_dict[consumption.functionality][consumption.model]["prompt_tokens"] += consumption.prompt_tokens or 0
            result_dict[consumption.functionality][consumption.model]["completion_tokens"] += consumption.completion_tokens or 0
            result_dict[consumption.functionality][consumption.model]["reasoning_tokens"] += consumption.reasoning_tokens or 0
            result_dict[consumption.functionality][consumption.model]["total_cost"] += float(consumption.cost) if consumption.cost else 0.0

        # Group consumptions by month
        consumptions_by_month = {}
        for consumption in consumption_list:
            if consumption.created_at:
                month_key = consumption.created_at.strftime("%Y-%m")
                if month_key not in consumptions_by_month:
                    consumptions_by_month[month_key] = {}

                functionality = consumption.functionality
                model = consumption.model

                if functionality not in consumptions_by_month[month_key]:
                    consumptions_by_month[month_key][functionality] = {}
                if model not in consumptions_by_month[month_key][functionality]:
                    consumptions_by_month[month_key][functionality][model] = {
                        "total_tokens": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "reasoning_tokens": 0,
                        "total_cost": 0.0
                    }

                consumptions_by_month[month_key][functionality][model]["total_tokens"] += consumption.total_tokens or 0
                consumptions_by_month[month_key][functionality][model]["prompt_tokens"] += consumption.prompt_tokens or 0
                consumptions_by_month[month_key][functionality][model]["completion_tokens"] += consumption.completion_tokens or 0
                consumptions_by_month[month_key][functionality][model]["reasoning_tokens"] += consumption.reasoning_tokens or 0
                consumptions_by_month[month_key][functionality][model]["total_cost"] += float(consumption.cost) if consumption.cost else 0.0

        return {
            "total_consumptions": result_dict,
            "consumptions_by_month": consumptions_by_month
        }
    
    def get_llm_consumptions_details_by_analysis(self, analysis_id, month):
        # DynamicGeneration
        dynamic_generation_consumptions = llm_consumption_dao.find_autogenie_consumptions_by_analysis(analysis_id, month)
        # BugFixer
        bugfixer_consumptions = llm_consumption_dao.find_bugfixer_consumptions_by_analysis(analysis_id, month)
        # Agent
        agent_consumptions_raw = llm_consumption_dao.find_agent_consumptions_by_analysis(analysis_id, month)
        # NodeInterpreter
        node_interpreter_consumptions = llm_consumption_dao.find_node_interpreter_consumptions_by_analysis(analysis_id, month)
        # BranchReport
        branch_report_consumptions = llm_consumption_dao.find_branch_report_consumptions_by_analysis(analysis_id, month)

        statistic_dict = {}

        # Process DynamicGeneration and BugFixer consumptions
        consumptions = []
        consumptions.extend(dynamic_generation_consumptions)
        consumptions.extend(bugfixer_consumptions)

        for consumption in consumptions:
            func = consumption.functionality
            if func not in statistic_dict:
                statistic_dict[func] = {}
            if consumption.model not in statistic_dict[func]:
                statistic_dict[func][consumption.model] = {
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "reasoning_tokens": 0
                }
            statistic_dict[func][consumption.model]["total_tokens"] += consumption.total_tokens or 0
            statistic_dict[func][consumption.model]["prompt_tokens"] += consumption.prompt_tokens or 0
            statistic_dict[func][consumption.model]["completion_tokens"] += consumption.completion_tokens or 0
            statistic_dict[func][consumption.model]["reasoning_tokens"] += consumption.reasoning_tokens or 0

        # Process Agent consumptions (they are tuples)
        for agent_consumption in agent_consumptions_raw:
            agent_type = agent_consumption.agent_type
            model = agent_consumption.model
            functionality = agent_consumption.functionality
            func = f"{functionality}-{agent_type}" if agent_type is not None else functionality

            if func not in statistic_dict:
                statistic_dict[func] = {}
            if model not in statistic_dict[func]:
                statistic_dict[func][model] = {
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "reasoning_tokens": 0
                }
            statistic_dict[func][model]["total_tokens"] += agent_consumption.total_tokens or 0
            statistic_dict[func][model]["prompt_tokens"] += agent_consumption.prompt_tokens or 0
            statistic_dict[func][model]["completion_tokens"] += agent_consumption.completion_tokens or 0
            statistic_dict[func][model]["reasoning_tokens"] += agent_consumption.reasoning_tokens or 0

        # NodeInterpreter
        for node_interpreter_consumption in node_interpreter_consumptions:
            model = node_interpreter_consumption.model
            functionality = node_interpreter_consumption.functionality
            func = f"NodeInterpreter"
            if func not in statistic_dict:
                statistic_dict[func] = {}
            if model not in statistic_dict[func]:
                statistic_dict[func][model] = {
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "reasoning_tokens": 0
                }
            statistic_dict[func][model]["total_tokens"] += node_interpreter_consumption.total_tokens or 0
            statistic_dict[func][model]["prompt_tokens"] += node_interpreter_consumption.prompt_tokens or 0
            statistic_dict[func][model]["completion_tokens"] += node_interpreter_consumption.completion_tokens or 0
            statistic_dict[func][model]["reasoning_tokens"] += node_interpreter_consumption.reasoning_tokens or 0

        # BranchReport
        for branch_report_consumption in branch_report_consumptions:
            model = branch_report_consumption.model
            functionality = branch_report_consumption.functionality
            func = functionality
            if func not in statistic_dict:
                statistic_dict[func] = {}
            if model not in statistic_dict[func]:
                statistic_dict[func][model] = {
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "reasoning_tokens": 0
                }
            statistic_dict[func][model]["total_tokens"] += branch_report_consumption.total_tokens or 0
            statistic_dict[func][model]["prompt_tokens"] += branch_report_consumption.prompt_tokens or 0
            statistic_dict[func][model]["completion_tokens"] += branch_report_consumption.completion_tokens or 0
            statistic_dict[func][model]["reasoning_tokens"] += branch_report_consumption.reasoning_tokens or 0

        return statistic_dict

    def get_llm_consumptions_details_by_user(self, user_id, month):
        analysis_list = analysis_dao.find_by_user_id(user_id)
        result = []
        for analysis in analysis_list:
            result.append({
                "analysis_id": analysis.id,
                "analysis_name": analysis.name,
                "consumptions": self.get_llm_consumptions_details_by_analysis(analysis.id, month)
            })
        return result
    
    def get_computation_configuration_key(self, computation:Computation):
        default = '{"vcpu": 0,"ram": 0,"timeout": 0,"gpu": 0}'
        computation_resource_configure = computation.computation_resource_configure or default
        computation_resource_configure = json.loads(computation_resource_configure)
        vcpu = computation_resource_configure.get('vcpu', 0)
        ram = computation_resource_configure.get('ram', 0)
        gpu = computation_resource_configure.get('gpu', 0)
        return f"{vcpu}-{ram}-{gpu}"


    def get_computation_consumptions_total_by_user(self, user_id):
        computation_list = computation_dao.find_by_user_id(user_id)

        # Calculate total duration grouped by system_env
        total_by_system_env = {}
        for computation in computation_list:
            system_env = computation.system_env or "unknown"
            if system_env not in total_by_system_env:
                total_by_system_env[system_env] = 0
            total_by_system_env[system_env] += computation.duration or 0

        # Group by month and system_env
        consumptions_by_month = {}
        for computation in computation_list:
            if computation.created_time:
                month_key = computation.created_time.strftime("%Y-%m")
                system_env = computation.system_env or "unknown"
                configuration_key = self.get_computation_configuration_key(computation)
                if month_key not in consumptions_by_month:
                    consumptions_by_month[month_key] = {}
                if system_env not in consumptions_by_month[month_key]:
                    consumptions_by_month[month_key][system_env] = {}
                if configuration_key not in consumptions_by_month[month_key][system_env]:
                    consumptions_by_month[month_key][system_env][configuration_key] = 0

                consumptions_by_month[month_key][system_env][configuration_key] += computation.duration or 0

        return {
            "total_by_system_env": total_by_system_env,
            "consumptions_by_month": consumptions_by_month,
            "configuration_key_format": "vcpu-ram-gpu"
        }
    
    def get_computation_consumptions_details_by_analysis(self, analysis_id, month):
        computation_list = computation_dao.find_by_analysis_id_and_month(analysis_id, month)
        # Calculate total duration grouped by system_env
        total_by_system_env = {}
        for computation in computation_list:
            system_env = computation.system_env or "unknown"
            configuration_key = self.get_computation_configuration_key(computation)
            if system_env not in total_by_system_env:
                total_by_system_env[system_env] = {}
            if configuration_key not in total_by_system_env[system_env]:
                total_by_system_env[system_env][configuration_key] = 0
            total_by_system_env[system_env][configuration_key] += computation.duration or 0

        return total_by_system_env

    def get_computation_consumptions_details_by_user(self, user_id, month):
        analysis_list = analysis_dao.find_by_user_id(user_id)
        result = []
        for analysis in analysis_list:
            result.append({
                "analysis_id": analysis.id,
                "analysis_name": analysis.name,
                "consumptions": self.get_computation_consumptions_details_by_analysis(analysis.id, month)
            })
        return result

    def record_consumption(self, consumption: dict):
        llm_consumption = LLMConsumption(**consumption)
        llm_dao.insert_consumption(llm_consumption)

consumption_service = ConsumptionService()
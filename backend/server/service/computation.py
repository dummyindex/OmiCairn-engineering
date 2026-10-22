import json
from model.computation import Computation
from model.node import Node
from dao.computation import computation_dao
from dao.node import node_dao
from dao.analysis import analysis_dao
from dao.edge import edge_dao
from dao.data import data_dao
from dao.user import user_dao
from dao.function_block_v1 import function_block_v1_dao
from dao.figure import figure_dao
from llm.llm_interface import LlmInterface
from typing import List, Dict

from log.logger_factory import logger_factory
from constants.sss import BUCKET_NAME
from model.figure import Figure
from constants.node import NodeType
from constants.authority import Relation
from sss.porter_factory import PorterFactory
from waiter.function_block_v1_waiter import FunctionBlockV1Waiter
from waiter.computation import ComputationWaiter
from constants.preset_env import PRESET_ENV_DICT

logger = logger_factory.create_logger("Computation Service")

def reduct_params(arg_rules, params):
    for arg_rule in arg_rules:
        arg_name = arg_rule.get("name", None)
        arg_render_type = arg_rule.get("render_type", None)
        if arg_render_type in ["cells-selector", "genes-selector"]:
            if type(params.get(arg_name, None)) != list:
                params[arg_name] = []
            else:
                params[arg_name] = params[arg_name][:10]
    return params

class ComputationService:
    def get(self, computation_id) -> Computation:
        computation = computation_dao.find_by_id(computation_id)
        return computation

    def get_list_by_node(self, node_id) -> List[Computation]:
        computation_list = computation_dao.find_by_node_id(node_id)
        return computation_list

    def get_list_by_task(self, task_id) -> List[Computation]:
        computation_list = computation_dao.find_by_task_id(task_id)
        return computation_list

    def get_latest_by_node(self, node_id) -> Computation:
        computation = computation_dao.find_latest_by_node_id(node_id)
        return computation

    def refresh_optimized_error_description(self, computation_id, user_id) -> Computation:
        llm_interface = LlmInterface()
        llm_interface.apply_for_optimize_error_description(computation_id, user_id)
        computation = computation_dao.find_by_id(computation_id)
        return computation
    
    def get_figure_list_by_computation(self, computation_id) -> List[Figure]:
        figure_list = figure_dao.find_by_computation_id(computation_id)
        return figure_list

    
    def get_former_computation_steps(self, tail_node_id):
        """
        Get former computation steps as simple description strings.
        Returns a list of function block descriptions from the computation path.
        """
        node_id = tail_node_id
        # get the analysis this node belongs to
        node = node_dao.find_by_id(node_id)
        analysis_id = node.analysis_id
        # get all edges in this analysis
        edge_list = edge_dao.find_by_analysis_id(analysis_id)
        target_id_2_source_id = {}
        for edge in edge_list:
            target_id_2_source_id[edge.target_node_id] = edge.source_node_id
        # get the predecessor nodes of this node (reverse order)
        former_node_id_list = [node_id]
        former_node_id = node_id
        while former_node_id in target_id_2_source_id:
            former_node_id = target_id_2_source_id[former_node_id]
            former_node_id_list.append(former_node_id)
        # restore forward order
        former_node_id_list.reverse()
        # get the predecessor node entities
        node_list: List[Node] = node_dao.find_by_id_list(former_node_id_list)
        node_id_2_node: Dict[int, Node] = {}
        for node in node_list:
            node_id_2_node[node.id] = node
        former_node_list = [node_id_2_node.get(node_id) for node_id in former_node_id_list]

        # get the function block description of each node
        step_descriptions = []
        for node in former_node_list:
            if node.type != NodeType.COMPUTATION_NODE_V2.value:
                step_descriptions.append({
                    "node_id": node.id,
                    "description": f"Node {node.id} is a data node."
                })
                continue
            fb_vid_of_node = node.function_block_version_id
            fbv_of_node = function_block_v1_dao.find_version_by_id(fb_vid_of_node)
            if fbv_of_node and fbv_of_node.description:
                step_descriptions.append({
                    "node_id": node.id,
                    "description": fbv_of_node.description
                })

        return step_descriptions

    def get_former_computation_history(self, tail_node_id):
        node_id = tail_node_id
        # get the analysis this node belongs to
        node = node_dao.find_by_id(node_id)
        analysis_id = node.analysis_id
        # get all edges in this analysis
        edge_list = edge_dao.find_by_analysis_id(analysis_id)
        target_id_2_source_id = {}
        for edge in edge_list:
            target_id_2_source_id[edge.target_node_id] = edge.source_node_id
        # get the predecessor nodes of this node (reverse order)
        former_node_id_list = [node_id]
        former_node_id = node_id
        while former_node_id in target_id_2_source_id:
            former_node_id = target_id_2_source_id[former_node_id]
            former_node_id_list.append(former_node_id)
        # restore forward order
        former_node_id_list.reverse()
        # get the predecessor node entities
        node_list: List[Node] = node_dao.find_by_id_list(former_node_id_list)
        node_id_2_node: Dict[int, Node] = {}
        for node in node_list:
            node_id_2_node[node.id] = node
        former_node_list = [node_id_2_node.get(node_id) for node_id in former_node_id_list]
        # get the latest computation of each predecessor node
        computation_list = computation_dao.find_all_by_node_id_list(former_node_id_list)
        # count computations per node and find the latest computation
        computation_list.sort(key=lambda computation: computation.created_time)
        node_id_2_computation = {}
        node_id_2_computation_count = {}
        for computation in computation_list:
            node_id = computation.node_id
            node_id_2_computation[node_id] = computation
            node_id_2_computation_count[node_id] = node_id_2_computation_count.get(node_id, 0) + 1
        # get all figures related to the computation
        latest_computation_list = [node_id_2_computation.get(node.id, None) for node in former_node_list]
        latest_computation_id_list = [computation.id for computation in latest_computation_list if computation is not None]
        figure_list = figure_dao.find_by_computation_id_list(latest_computation_id_list)
        computation_id_2_figure_list = {}
        for figure in figure_list:
            computation_id = figure.computation_id
            if computation_id not in computation_id_2_figure_list:
                computation_id_2_figure_list[computation_id] = []
            computation_id_2_figure_list[computation_id].append(figure)
        # get data-related information
        data_id_list = [node.data_id for node in former_node_list if node.data_id is not None] + [computation.result_data_id for computation in latest_computation_list if computation is not None]
        data_list = data_dao.find_by_id_list(data_id_list)
        data_id_2_data = {}
        for data in data_list:
            data_id_2_data[data.id] = data
        # build the return value
        node_with_computation_list = []
        for node in former_node_list:
            latest_computation = node_id_2_computation.get(node.id, None)
            if node.type == NodeType.DATA_NODE.value:
                data_id = node.data_id
            else:
                data_id = latest_computation.result_data_id if latest_computation is not None else None
            data = data_id_2_data.get(data_id, None) if data_id is not None else None
            dataset_stats = json.loads(data.summary) if data is not None and data.summary is not None else {}
            computation_count = node_id_2_computation_count.get(node.id, 0)
            if latest_computation is not None:
                figure_list: List[Figure] = computation_id_2_figure_list.get(latest_computation.id, []) if latest_computation is not None else []
                figure_list = [{"bucket": BUCKET_NAME, "key": f"figure/{figure.figure_uuid}", "name": figure.figure_name} for figure in figure_list]
                fbv_of_computation = function_block_v1_dao.find_version_by_id(latest_computation.function_block_version_id)
                latest_computation_dict = latest_computation.to_dict()
                latest_computation_params = json.loads(latest_computation_dict.get("computationParams")) if latest_computation_dict.get("computationParams") is not None else {}
                arg_rules_of_computation = json.loads(fbv_of_computation.args) if fbv_of_computation is not None and fbv_of_computation.args is not None else []
                latest_computation_dict["computationParams"] = reduct_params(arg_rules_of_computation, latest_computation_params)
                
            else:
                figure_list = []
                fbv_of_computation = None
                latest_computation_dict = None
                
            fb_vid_of_node = node.function_block_version_id
            fbv_of_node = function_block_v1_dao.find_version_by_id(fb_vid_of_node)
            arg_rules_of_node = json.loads(fbv_of_node.args) if fbv_of_node is not None and fbv_of_node.args is not None else []
            
            node_dict = node.to_dict()
            node_params = json.loads(node_dict.get("computationParams")) if node_dict.get("computationParams") is not None else {}
            node_dict["computationParams"] = reduct_params(arg_rules_of_node, node_params)

            
            item = {
                "node": node_dict,
                "latestComputation": latest_computation_dict,
                "computationCount": computation_count,
                "computationLog": None,
                "figureList": figure_list,
                "data": data.to_dict() if data is not None else None,
                "dataset_stats": dataset_stats
            }
            if node.id == tail_node_id and node.type == NodeType.COMPUTATION_NODE.value:
                item["args"] = arg_rules_of_node
                item["preset_env"] = PRESET_ENV_DICT[fbv_of_node.preset_env] if fbv_of_node.preset_env in PRESET_ENV_DICT else None
                fb_waiter = FunctionBlockV1Waiter(fb_vid_of_node, fbv_of_node.program_language)
                item["code"] = fb_waiter.fetch_core_code()
                item["requirement_file"] = fb_waiter.fetch_requirement_content()
                item["static_config_file"] = fb_waiter.fetch_static_config()
                item["install_script"] = fb_waiter.fetch_install_script()
                item["program_language"] = fbv_of_node.program_language
                if latest_computation is not None:
                    computation_waiter = ComputationWaiter(latest_computation.id)
                    calculation_log = computation_waiter.get_log(only_message=True, tail_n=150)
                    calculation_log = "\n".join(calculation_log) if isinstance(calculation_log, list) else calculation_log
                    item["latestComputationLog"] = calculation_log
                
            node_with_computation_list.append(item)
        return node_with_computation_list
    
    def get_computation_details_by_node_id_list(self, node_id_list):
        node_list: List[Node] = node_dao.find_by_id_list(node_id_list)
        computation_list = computation_dao.find_all_by_node_id_list(node_id_list)
        # count computations per node and find the latest computation
        computation_list.sort(key=lambda computation: computation.created_time)
        node_id_2_computation = {}
        node_id_2_computation_count = {}
        for computation in computation_list:
            node_id = computation.node_id
            node_id_2_computation[node_id] = computation
            node_id_2_computation_count[node_id] = node_id_2_computation_count.get(node_id, 0) + 1
        latest_computation_list = [node_id_2_computation.get(node.id, None) for node in node_list]
        latest_computation_id_list = [computation.id for computation in latest_computation_list if computation is not None]
        figure_list = figure_dao.find_by_computation_id_list(latest_computation_id_list)
        computation_id_2_figure_list = {}
        for figure in figure_list:
            computation_id = figure.computation_id
            if computation_id not in computation_id_2_figure_list:
                computation_id_2_figure_list[computation_id] = []
            computation_id_2_figure_list[computation_id].append(figure)
        node_map = {node.id: node for node in node_list}
        result_list = []
        data_id_list = [node.data_id for node in node_list if node.data_id is not None] + [computation.result_data_id for computation in latest_computation_list if computation is not None]
        data_list = data_dao.find_by_id_list(data_id_list)
        data_id_2_data = {}
        for data in data_list:
            data_id_2_data[data.id] = data
        for node_id in node_id_list:
            node = node_map.get(node_id)
            if node is None:
                logger.error(f"Node not found: {node_id}")
                raise Exception(f"Node not found: {node_id}")
            else:
                latest_computation = node_id_2_computation.get(node_id, None)
                computation_count = node_id_2_computation_count.get(node_id, 0)
                figure_list: List[Figure] = computation_id_2_figure_list.get(latest_computation.id, []) if latest_computation is not None else []
                figure_list = [{"bucket": BUCKET_NAME, "key": f"figure/{figure.figure_uuid}", "name": figure.figure_name} for figure in figure_list]
                if node.type == NodeType.DATA_NODE.value:
                    data_id = node.data_id
                else:
                    data_id = latest_computation.result_data_id if latest_computation is not None else None
                data = data_id_2_data.get(data_id, None) if data_id is not None else None
                dataset_stats = json.loads(data.summary) if data is not None and data.summary is not None else {}
                item = {
                    "node": node,
                    "latestComputation": latest_computation,
                    "computationCount": computation_count,
                    "figureList": figure_list,
                    "data": data,
                    "dataset_stats": dataset_stats
                }
                if node.type == NodeType.COMPUTATION_NODE.value:
                    fb_vid = node.function_block_version_id
                    fb_v = function_block_v1_dao.find_version_by_id(fb_vid)
                    fb_waiter = FunctionBlockV1Waiter(fb_vid, fb_v.program_language)
                    static_config = fb_waiter.fetch_static_config()
                    item["args"] = static_config["args"] if "args" in static_config else []
                    core_code = fb_waiter.fetch_core_code()
                    item["code"] = core_code
                    item["preset_env"] = PRESET_ENV_DICT[fb_v.preset_env] if fb_v.preset_env in PRESET_ENV_DICT else None
                result_list.append(item)
        return result_list

    def get_computation_report_presigned_url(self, computation_id):
        porter = PorterFactory.create_porter()
        object_key = f"computation-report/report-{computation_id}.md"
        porter.set_operation_target(object_key)
        try:
            porter.get_head()
        except Exception as e:
            return None
        return porter.get_presigned_url(60 * 3)
    
    def get_retry_process_list_by_analysis_id(self, analysis_id):
        retry_process_list = computation_dao.find_retry_process_by_analysis_id(analysis_id)
        return retry_process_list
    
    def save_computation_report(self, computation_id, content):
        porter = PorterFactory.create_porter()
        object_key = f"computation-report/report-{computation_id}.md"
        porter.set_operation_target(object_key)
        porter.save_file_text(content)
        return object_key
    
    def get_retry_process_details(self, retry_process_id):
        retry_process = computation_dao.find_retry_process_by_id(retry_process_id)
        node = node_dao.find_by_id(retry_process.node_id)
        new_node = node_dao.find_by_id(retry_process.new_node_id)
        analysis = analysis_dao.find_by_id(retry_process.analysis_id)
        computations = computation_dao.find_by_retry_process_id(retry_process.id)
        result = {
            "retryProcess": retry_process,
            "node": node,
            "newNode": new_node,
            "analysis": analysis,
            "computations": computations
        }
        return result
    
    def get_list_by_analysis_id(self, analysis_id, show_node, show_user, show_source_data, limit, offset):
        node_list = node_dao.find_raw_by_analysis_id(analysis_id)
        node_map = {node.id: node for node in node_list}
        node_id_list = [node.id for node in node_list]
        computation_list = computation_dao.find_by_node_id_list(node_id_list, limit, offset)
        computation_list = [computation.to_dict() for computation in computation_list if computation is not None]
        for computation in computation_list:
            del computation["computationParams"]
        computation_id_list = [computation["id"] for computation in computation_list]
        if show_user:
            user_relations = computation_dao.find_user_relation_by_computation_id_list(computation_id_list, Relation.BELONG_TO.value)
            computation_id_2_user_id = {relation.computation_id: relation.user_id for relation in user_relations}
            user_id_list = [relation.user_id for relation in user_relations]
            user_list = user_dao.find_by_id_list(user_id_list)
            user_id_2_user = {user.id: user for user in user_list}
            for computation in computation_list:
                user_id = computation_id_2_user_id.get(computation["id"], None)
                if user_id is not None:
                    user = user_id_2_user.get(user_id, None)
                    user_dict = user.to_dict() if user is not None else None
                    if user_dict is not None:
                        # Do not expose other users' contact details to collaborators
                        user_dict.pop("phoneNumber", None)
                        user_dict.pop("email", None)
                    computation["user"] = user_dict
        if show_node:
            for computation in computation_list:
                node = node_map.get(computation["nodeId"], None)
                node_dict = node.to_dict() if node is not None else None
                if node_dict is not None:
                    del node_dict["computationParams"]
                computation["node"] = node_dict
        if show_source_data:
            all_source_data_id_list = []
            for computation in computation_list:
                if computation["sourceDataIds"] is not None:
                    all_source_data_id_list.extend([] if computation["sourceDataIds"] is None else computation["sourceDataIds"])
            all_source_data_id_list = list(set(all_source_data_id_list))
            source_data_list = data_dao.find_by_id_list(all_source_data_id_list)
            source_data_id_2_data = {data.id: data for data in source_data_list}
            for computation in computation_list:
                source_data_id_list = [] if computation["sourceDataIds"] is None else computation["sourceDataIds"]
                source_data_list = [source_data_id_2_data.get(data_id, None) for data_id in source_data_id_list]
                source_data_list = []
                for data_id in source_data_id_list:
                    data = source_data_id_2_data.get(data_id, None)
                    if data is not None:
                        data_dict = data.to_dict()
                        del data_dict["summary"]
                        source_data_list.append(data_dict)
                computation["sourceDataList"] = source_data_list
        return computation_list



        

        
computation_service = ComputationService()

from datetime import datetime
import json
from dao.node import node_dao
from dao.edge import edge_dao
from dao.data import data_dao
from dao.function_block_v1 import function_block_v1_dao
from dao.computation import computation_dao
from dao.task import task_dao
from model.edge import Edge
from model.node import Node
from model.node_user_relation import NodeUserRelation
from model.function_block_v1 import FunctionBlockV1
from model.function_block_version_v1 import FunctionBlockVersionV1
from constants.node import NodeType, NodeState
from constants.data import DataState
from exception.flow.not_creatable import NotCreatableException
from exception.common.not_operatable import NotOperatableException
from exception.flow.not_removable import NotRemovableException
from constants.authority import Relation, Permission,SpecialUserId
from constants.computation import SystemEnv
from tool.flow import FlowTool
from tool.function_block import FunctionBlockTool
from waiter.node_space_waiter import NodeSpaceWaiter
from constants.analysis import SpecialAnalysis
from constants.computation_resource import DEFAULT_VCPUS, DEFAULT_RAM, DEFAULT_TIMEOUT, DEFAULT_GPU

class FlowService:
    def get_node_by_id(self, node_id):
        return node_dao.find_by_id(node_id)
    
    def get_information(self, node_id):
        node = node_dao.get_information(node_id)
        if node is None:
            return None
        return node.to_dict()

    def get_node_list_by_analysis_id(self, analysis_id, with_computation: bool = True):
        if with_computation:
            return node_dao.find_by_analysis_id_with_computation(analysis_id)
        else:
            return node_dao.find_by_analysis_id(analysis_id)

    def get_node_list_by_idx(self, idx):
        return node_dao.find_by_id_list(idx)

    def get_node_previte_dict_by_analysis_id(self, analysis_id):
        previte_list = node_dao.find_previte_list_by_analysis_id(analysis_id)
        node_2_state_dict = {
            previte.node_id: previte.status for previte in previte_list
        }
        return node_2_state_dict

    def get_edge_list_by_analysis_id(self, analysis_id):
        return edge_dao.find_by_analysis_id(analysis_id)
    
    def get_previous_node_list_by_node_id(self, end_node_id, with_self: bool = False):
        if with_self:
            previous_node_list = [node_dao.find_by_id(end_node_id)]
        else:
            previous_node_list = []
        previous_edges = edge_dao.find_all_before_edges(end_node_id)
        previous_node_id_list = [edge.source_node_id for edge in previous_edges]
        previous_node_list =  node_dao.find_by_id_list(previous_node_id_list) + previous_node_list
        return previous_node_list
    
    def get_previous_path_by_node_id(self, end_node_id, with_self: bool = False):
        if with_self:
            previous_node_list = [node_dao.find_by_id(end_node_id)]
        else:
            previous_node_list = []
        path, previous_edges = node_dao.find_branch_path(node_id=end_node_id)
        previous_node_list = path + previous_node_list
        return previous_node_list, previous_edges

    def get_later_node_list_by_node_id(self, start_node_id, with_self: bool = False):
        if with_self:
            later_node_list = [node_dao.find_by_id(start_node_id)]
        else:
            later_node_list = []
        later_edges = edge_dao.find_all_after_edges(start_node_id)
        later_node_id_list = [edge.target_node_id for edge in later_edges]
        later_node_list = later_node_list + node_dao.find_by_id_list(later_node_id_list)
        return later_node_list
    
    def get_parent_node_list_by_node_id(self, node_id):
        before_edges = edge_dao.find_by_target_node_id(node_id)
        parent_node_id_list = [edge.source_node_id for edge in before_edges]
        parent_node_list = node_dao.find_by_id_list(parent_node_id_list)
        return parent_node_list

    def get_node_params(self, node_id):
        node: Node = node_dao.find_by_id(node_id)
        return json.loads(node.computation_params)

    def get_mini_tool_node(self, function_block_id, user_id):
        nodes = node_dao.find_by_analysis_id_and_fb_id_and_user_id(SpecialAnalysis.MINI_TOOL.value, function_block_id, user_id)
        node = nodes[0] if len(nodes) > 0 else None
        if node is None:
            fb = function_block_v1_dao.find_by_id(function_block_id)
            fb_v = function_block_v1_dao.find_version_by_id(fb.current_version_id)
            args = json.loads(fb_v.args)
            default_values = FunctionBlockTool.abstract_args_attr_dict_by_name(args, "default_value")
            default_values = json.dumps(default_values)
            node = self.create_computation_node(
                function_block_id,
                default_values,
                SpecialAnalysis.MINI_TOOL.value,
                0,
                0,
                fb.name,
                fb_v.tag,
                fb_v.id,
                user_id,
                SystemEnv.SERVER_LOCAL.value,
                node_type=NodeType.COMPUTATION_NODE.value
            )
        return node


    def create_data_node(self, analysis_id, data_id, x, y, name, owner_id):
        data = data_dao.find_by_id(data_id)
        if data.state != DataState.OK.value:
            raise NotCreatableException(
                "Data is not ready to be used."
            )
        node_type = NodeType.DATA_NODE_V2.value if data.upload_type == "general" else NodeType.DATA_NODE.value
        now = datetime.now()
        node = Node(
            created_time=now,
            name=name,
            x=x,
            y=y,
            type=node_type,
            data_id=data_id,
            analysis_id=analysis_id,
            state=NodeState.ORIGINAL.value,
            locked=False
        )
        node_dao.insert(node)
        node_user_relation = NodeUserRelation(
            node_id=node.id,
            user_id=owner_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        node_dao.insert_user_relation(node_user_relation)

        return node

    def create_computation_node(
        self,
        function_block_id,
        compution_params,
        analysis_id,
        x,
        y,
        name,
        tag,
        function_block_version_id,
        owner_id,
        system_env,
        node_type=NodeType.COMPUTATION_NODE.value,
        dynamic_generation_id=None,
        dynamic_generation_session_id=None,
        computation_resource_configure=None,
        replan_source_id=None
    ):
        now = datetime.now()
        default_computation_resource_configure = {
            "vcpu": DEFAULT_VCPUS,
            "ram": DEFAULT_RAM,
            "timeout": DEFAULT_TIMEOUT,
            "gpu": DEFAULT_GPU,
        }
        if computation_resource_configure is not None:
            if type(computation_resource_configure) == str:
                computation_resource_configure = json.loads(computation_resource_configure)
            if type(computation_resource_configure) == dict:
                default_computation_resource_configure.update(computation_resource_configure)
        default_computation_resource_configure = json.dumps(default_computation_resource_configure) if type(default_computation_resource_configure) == dict else default_computation_resource_configure

        avg_duration = node_dao.update_and_get_matching_average_duration(
            function_block_version_id,
            system_env,
            default_computation_resource_configure
        )

        node = Node(
            created_time=now,
            name=name,
            x=x,
            y=y,
            type=node_type,
            function_block_id=function_block_id,
            computation_params=compution_params if type(compution_params) == str or compution_params is None else json.dumps(compution_params),
            analysis_id=analysis_id,
            state=NodeState.ORIGINAL.value,
            locked=False,
            tag=tag,
            function_block_version_id=function_block_version_id,
            system_env=system_env,
            computation_resource_configure=default_computation_resource_configure,
            dynamic_generation_id=dynamic_generation_id,
            dynamic_generation_session_id=dynamic_generation_session_id,
            avg_duration=avg_duration,
            replan_source_id=replan_source_id
        )
        node_dao.insert(node)

        node_user_relation = NodeUserRelation(
            node_id=node.id,
            user_id=owner_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )

        node_dao.insert_user_relation(node_user_relation)
        return node

    def create_report_node(self, analysis_id, x, y, name, source_node_ids, owner_id):
        now = datetime.now()
        node = Node(
            created_time=now,
            name=name,
            x=x,
            y=y,
            type=NodeType.REPORT_NODE.value,
            analysis_id=analysis_id,
            state=NodeState.RUNNING.value,
            locked=False,
            computation_params=json.dumps({
                "source_node_ids": source_node_ids
            })
        )
        node_dao.insert(node)
        
        node_user_relation = NodeUserRelation(
            node_id=node.id,
            user_id=owner_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        
        node_dao.insert_user_relation(node_user_relation)
        return node
    
    def create_notebook_node(
        self,
        analysis_id,
        x,
        y,
        name,
        owner_id,
        system_env,
        dynamic_generation_id,
        computation_resource_configure=None
    ):
        now = datetime.now()
        default_computation_resource_configure = {
            "vcpu": DEFAULT_VCPUS,
            "ram": DEFAULT_RAM,
            "timeout": DEFAULT_TIMEOUT,
            "gpu": DEFAULT_GPU,
        }
        if computation_resource_configure is not None:
            if type(computation_resource_configure) == str:
                computation_resource_configure = json.loads(computation_resource_configure)
            if type(computation_resource_configure) == dict:
                default_computation_resource_configure.update(computation_resource_configure)
        default_computation_resource_configure = json.dumps(default_computation_resource_configure) if type(default_computation_resource_configure) == dict else default_computation_resource_configure

        node = Node(
            created_time=now,
            name=name,
            x=x,
            y=y,
            type=NodeType.NOTEBOOK_NODE.value,
            analysis_id=analysis_id,
            state=NodeState.ORIGINAL.value,
            locked=False,
            system_env=system_env,
            dynamic_generation_id=dynamic_generation_id,
            computation_resource_configure=default_computation_resource_configure
        )
        node_dao.insert(node)

        node_user_relation = NodeUserRelation(
            node_id=node.id,
            user_id=owner_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )

        node_dao.insert_user_relation(node_user_relation)
        return node

    def create_claude_code_node(
        self,
        analysis_id,
        x,
        y,
        name,
        owner_id,
        system_env,
        dynamic_generation_id,
        computation_resource_configure=None,
    ):
        now = datetime.now()
        default_computation_resource_configure = {
            "vcpu": DEFAULT_VCPUS,
            "ram": 16,
            "timeout": DEFAULT_TIMEOUT,
            "gpu": DEFAULT_GPU,
        }
        if computation_resource_configure is not None:
            if type(computation_resource_configure) == str:
                computation_resource_configure = json.loads(computation_resource_configure)
            if type(computation_resource_configure) == dict:
                default_computation_resource_configure.update(computation_resource_configure)
        default_computation_resource_configure = json.dumps(default_computation_resource_configure) if type(default_computation_resource_configure) == dict else default_computation_resource_configure

        node = Node(
            created_time=now,
            name=name,
            x=x,
            y=y,
            type=NodeType.CLAUDE_CODE_NODE.value,
            analysis_id=analysis_id,
            state=NodeState.ORIGINAL.value,
            locked=False,
            system_env=system_env,
            dynamic_generation_id=dynamic_generation_id,
            computation_resource_configure=default_computation_resource_configure
        )
        node_dao.insert(node)

        node_user_relation = NodeUserRelation(
            node_id=node.id,
            user_id=owner_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )

        node_dao.insert_user_relation(node_user_relation)
        return node

    def create_edge(
        self,
        source_node_id,
        target_node_id,
        analysis_id
    ):
        now = datetime.now()
        # NOTE: check if the target node has other source nodes
        source_edge_list = edge_dao.find_by_target_node_id(target_node_id)
        if len(source_edge_list) > 0:
            raise NotCreatableException(
                "Target node has already been connected."
            )
        edge_list = edge_dao.find_by_analysis_id(analysis_id)
        if FlowTool.check_edge_cycle(
            edge_list,
            source_node_id,
            target_node_id
        ):
            raise NotCreatableException(
                "Edge will cause cycle."
            )
        edge = Edge(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            analysis_id=analysis_id,
            created_time=now
        )
        edge_dao.insert(edge)
        return edge

    def edit_node(self, node_id, data):
        node = node_dao.find_by_id(node_id)
        next_edges = edge_dao.find_by_source_node_id(node_id)
        will_effect_computation = False
        for key in ["computation_params", "function_block_id", "function_block_version_id", "system_env", "computation_resource_configure", "state"]:
            if key in data:
                will_effect_computation = True
                break
        if will_effect_computation and node.locked and len(next_edges) > 0:
            raise NotOperatableException(f"Node {node_id} is locked")
        if "id" in data:
            del data["id"]
        if "computation_params" in data:
            if type(data["computation_params"]) == dict:
                data["computation_params"] = json.dumps(data["computation_params"])

        if "function_block_version_id" in data:
            function_block_version = function_block_v1_dao.find_version_by_id(data["function_block_version_id"])
            if "tag" not in data:
                data["tag"] = function_block_version.tag
            if "computation_params" not in data:
                args = json.loads(function_block_version.args)
                default_values = FunctionBlockTool.abstract_args_attr_dict_by_name(args, "default_value")
                data["computation_params"] = json.dumps(default_values)

        should_update_avg_duration = any(key in data for key in [
            "function_block_version_id", "system_env", "computation_resource_configure"
        ])

        if should_update_avg_duration:
            fb_version_id = data.get("function_block_version_id", node.function_block_version_id)
            sys_env = data.get("system_env", node.system_env)
            comp_resource = data.get("computation_resource_configure", node.computation_resource_configure)

            data["avg_duration"] = node_dao.update_and_get_matching_average_duration(
                fb_version_id,
                sys_env,
                comp_resource
            )

        node_dao.update_node(node_id, data)

        # Handle edit_node_params
        if will_effect_computation:
            after_edge_list = edge_dao.find_all_after_edges(node_id)
            after_node_id_list = [edge.target_node_id for edge in after_edge_list]
            node_dao.update_by_id_list(
                after_node_id_list,
                {"state": NodeState.ORIGINAL.value}
            )

    # def edit_node_name(self, node_id, name):
    #     node_dao.update(node_id, {"name": name})

    # def edit_node_tag(self, node_id, tag):
    #     node_dao.update(node_id, {"tag": tag})

    def edit_node_params(self, node_id, computation_params):
        node = node_dao.find_by_id(node_id)
        if node.locked:
            raise NotOperatableException(f"Node {node_id} is locked")
        after_edge_list = edge_dao.find_all_after_edges(node_id)
        after_node_id_list = [edge.target_node_id for edge in after_edge_list]
        node_dao.update_by_id_list(
            after_node_id_list,
            {"state": NodeState.ORIGINAL.value}
        )
        node_dao.update(
            node_id,
            {"computation_params": json.dumps(computation_params)}
        )

    # def edit_node_system_env(self, node_id, system_env):
    #     node = node_dao.find_by_id(node_id)
    #     if node.locked:
    #         raise NotOperatableException(f"Node {node_id} is locked")
    #     node_dao.update(node_id, {"system_env": system_env})


    def move_node(self, node_id, x, y):
        node_dao.update(node_id, {"x": x, "y": y})

    def copy_node(self, node_id, owner_id, updated_attrs: dict = None, with_edges: bool = False):
        node: Node = node_dao.find_by_id(node_id)
        attr_dict = {
            attr_name: getattr(node, attr_name) for attr_name in node.__table__.columns.keys()
            if attr_name not in ["id", "created_time", "locked"]
        }
        attr_dict["created_time"] = datetime.now()
        attr_dict["locked"] = False
        attr_dict["x"] = node.x + 100
        attr_dict["y"] = node.y + 50
        attr_dict["state"] = NodeState.ORIGINAL.value
        if updated_attrs is not None:
            attr_dict.update(updated_attrs)
        new_node = Node(**attr_dict)
        new_node = node_dao.insert(new_node)

        new_node_user_relation = NodeUserRelation(
            node_id=new_node.id,
            user_id=owner_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        node_dao.insert_user_relation(
            new_node_user_relation
        )
        if with_edges:
            before_edges = edge_dao.find_by_target_node_id(node_id)
            for edge in before_edges:
                new_edge = Edge(
                    source_node_id=edge.source_node_id,
                    target_node_id=new_node.id,
                    analysis_id=edge.analysis_id,
                    created_time=datetime.now()
                )
                edge_dao.insert(new_edge)
        node_space_waiter = NodeSpaceWaiter(new_node.id)
        node_space_waiter.copy_from_another_node_space(node_id)
        new_node_dict = new_node.to_dict()
        new_node_dict["previousEdges"] = [edge.to_dict() for edge in before_edges] if with_edges else []
        return new_node_dict

    def remove_node(self, node_id):
        node: Node = node_dao.find_by_id(node_id)
        if node.locked:
            raise NotRemovableException(f"Node {node_id} is locked")
        after_edge_list = edge_dao.find_all_after_edges(node_id)
        after_node_id_list = [edge.target_node_id for edge in after_edge_list]
        node_dao.update_by_id_list(
            after_node_id_list,
            {"state": NodeState.ORIGINAL.value}
        )
        node_dao.delete(node_id)
        task_dao.delete_task_node_relation_by_node_id(node_id)
        front_edges = edge_dao.find_by_target_node_id(node_id)
        for edge in front_edges:
            edge_dao.delete(edge.id)
            task_dao.delete_task_edge_relation_by_edge_id(edge.id)
        back_edges = edge_dao.find_by_source_node_id(node_id)
        for edge in back_edges:
            edge_dao.delete(edge.id)
            task_dao.delete_task_edge_relation_by_edge_id(edge.id)
        node_space_waiter = NodeSpaceWaiter(node_id)
        node_space_waiter.delete_all_files()

    def batch_remove_node(self, node_id_list):
        for node_id in node_id_list:
            self.remove_node(node_id)

    def remove_edge(self, edge_id):
        edge: Edge = edge_dao.find_by_id(edge_id)
        target_node = node_dao.find_by_id(edge.target_node_id)
        if target_node.locked:
            raise NotRemovableException(
                f"Target node {target_node.id} is locked")
        after_edge_list = edge_dao.find_all_after_edges(edge.target_node_id)
        after_node_id_list = [edge.target_node_id] + \
            [edge.target_node_id for edge in after_edge_list]
        node_dao.update_by_id_list(
            after_node_id_list,
            {"state": NodeState.ORIGINAL.value}
        )
        edge_dao.delete(edge_id)
        task_dao.delete_task_edge_relation_by_edge_id(edge_id)

    def get_node_tag_list(self, node_id_list):
        node_list = node_dao.find_by_id_list(node_id_list)
        return [node.tag for node in node_list]

    def validate_recommend_structure(self, recommend_structure: dict):
        keys = recommend_structure.keys()
        if len(keys) == 0:
            return False
        plus_function_block_list = function_block_v1_dao.find_fb_with_version_by_user_id(SpecialUserId.PUBLIC.value)
        plus_function_block_dict = {
            fb.function_block_version_name for fb in plus_function_block_list
        }
        for key in keys:
            fb_v_name = recommend_structure[key]
            if fb_v_name not in plus_function_block_dict:
                return False
        return True


    def generate_pipeline_by_gpt(self, recommend_structure: dict, analysis_id, user_id):
        serial_numbers = sorted([int(key) for key in recommend_structure.keys()])
        item_list = [
            recommend_structure[str(serial_number)]
            for serial_number in serial_numbers
        ]
        plus_function_block_list = function_block_v1_dao.find_fb_with_version_by_user_id(SpecialUserId.PUBLIC.value)
        plus_function_block_dict = {
            fb.function_block_version_name: fb for fb in plus_function_block_list
        }
        node_queue = []
        x = 0
        for version_name in item_list:
            if version_name in plus_function_block_dict:
                fb = plus_function_block_dict[version_name]
                fb_id = fb.function_block_id
                fb_v_id = fb.function_block_version_id,
                fb_name = fb.function_block_name
                fb_v_arg_ruls = json.loads(fb.function_block_version_args)
                fb_v_default_args = FunctionBlockTool.abstract_args_attr_dict_by_name(fb_v_arg_ruls, "default_value")
                fb_v_tag = fb.function_block_version_tag
                node_queue.append(self.create_computation_node(
                    fb_id,
                    fb_v_default_args,
                    analysis_id,
                    x,
                    -300,
                    fb_name,
                    fb_v_tag,
                    fb_v_id,
                    user_id,
                    system_env=SystemEnv.SERVER_LOCAL.value
                ))
                x += 400
            else:
                raise Exception(f"Function block version: {version_name} not found.")

        edge_queue = []
        for node_index in range(1, len(node_queue)):
            edge_queue.append(self.create_edge(
                node_queue[node_index - 1].id,
                node_queue[node_index].id,
                analysis_id
            ))
        return {
            "nodes": node_queue,
            "edges": edge_queue
        }

    def get_node_by_computation_id(self, computation_id):
        computation = computation_dao.find_by_id(computation_id)
        return node_dao.find_by_id(computation.node_id)

    def get_node_param_file_list(self, node_id):
        node_space_waiter = NodeSpaceWaiter(node_id)
        return node_space_waiter.list_params_files()

    def request_upload_node_param_file(self, node_id, file_name, file_size):
        node_space_waiter = NodeSpaceWaiter(node_id)
        return node_space_waiter.generate_param_file_presigned_post(file_name, file_size)

    def request_download_node_param_file(self, node_id, file_name):
        node_space_waiter = NodeSpaceWaiter(node_id)
        return node_space_waiter.generate_param_file_presigned_url(file_name)

    def remove_node_param_file(self, node_id, file_name):
        node_space_waiter = NodeSpaceWaiter(node_id)
        node_space_waiter.delete_param_file(file_name)

flow_service = FlowService()

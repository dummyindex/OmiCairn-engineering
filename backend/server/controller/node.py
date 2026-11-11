from flask import Blueprint, request
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from exception.request.parameter_invalid import ParameterInvalidException
from exception.common.not_operatable import NotOperatableException
from constants.computation import SystemEnv
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from service.flow import flow_service
from service.function_block_v1 import function_block_v1_service
from wrapper.exception import exception_wrapper
from constants.node import NodeListFetchMode, NodeType
from typing import List
from model.node import Node
from tool.function_block import FunctionBlockTool
from constants.authority import AuthorityCarrier

class NodeEditAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["node_id"]
        )
        node_id = request.args.get("node_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id, check_writable=True)
        
        post_data = request.get_json()
        
        flow_service.edit_node(node_id, post_data)
        
        # return response may different when handling different API
        return ResponseManager.new_success_response()
    
class NodeBatchEditAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(
            request=request,
            checked_list=["node_id_list", "attrs"]
        )
        post_data = request.get_json()
        node_id_list = post_data.get("node_id_list")
        attrs = post_data.get("attrs")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        for node_id in node_id_list:
            guardian.check_authority(node_id, check_writable=True)
            flow_service.edit_node(node_id, attrs)
        return ResponseManager.new_success_response()
    
class CreateAPI(Resource):

    def _handle_creating_data_node(self, owner_id):
        analysis_id = int(request.form.get("analysis_id"))
        x = float(request.form.get("x"))
        y = float(request.form.get("y"))
        name = request.form.get("name", None)
        request_auditor.request_form_check(
            request=request,
            checked_list=["data_id"]
        )
        data_id = int(request.form.get("data_id"))
        node = flow_service.create_data_node(
            analysis_id,
            data_id,
            x,
            y,
            name,
            owner_id
        )
        return node

    def _handle_creating_computation_node(self, owner_id):
        analysis_id = int(request.form.get("analysis_id"))
        x = float(request.form.get("x"))
        y = float(request.form.get("y"))
        name = request.form.get("name", None)
        replan_source_id = request.form.get("replan_source_id", None)
        request_auditor.request_form_check(
            request=request,
            checked_list=["function_block_id"]
        )
        function_block_id = request.form.get("function_block_id" ,None)
        if function_block_id is not None:
            function_block_id = int(function_block_id)
            # args = function_block_service.get_arguments(function_block_id)
            fb_version_v1_record = function_block_v1_service.get_current_version(function_block_id)
            if fb_version_v1_record is None:
                raise NotOperatableException("Function block has no version now")
            fb_attr_dict = fb_version_v1_record.to_dict()
            default_value_dict = FunctionBlockTool.abstract_args_attr_dict_by_name(fb_attr_dict["args"], "default_value")
            tag = fb_version_v1_record.tag
            fb_version_id = fb_version_v1_record.id
        else:
            default_value_dict = {}
            tag = None
            fb_version_id = None
        dynamic_generation_id = request.form.get("dynamic_generation_id", None)
        computation_resource_configure = request.form.get("computation_resource_configure", None)
        dynamic_generation_session_id = request.form.get("dynamic_generation_session_id", None)
        system_env = request.form.get("system_env", SystemEnv.AWS_BATCH.value)
        node = flow_service.create_computation_node(
            function_block_id,
            default_value_dict,
            analysis_id,
            x,
            y,
            name,
            tag,
            fb_version_id,
            owner_id,
            system_env=system_env,
            node_type=NodeType.COMPUTATION_NODE_V2.value if fb_version_v1_record.is_v2 else NodeType.COMPUTATION_NODE.value,
            dynamic_generation_id=dynamic_generation_id,
            dynamic_generation_session_id=dynamic_generation_session_id,
            computation_resource_configure=computation_resource_configure,
            replan_source_id=replan_source_id
        )
        return node

    def _handle_creating_report_node(self, owner_id):
        analysis_id = int(request.form.get("analysis_id"))
        x = float(request.form.get("x"))
        y = float(request.form.get("y"))
        name = request.form.get("name", "Report Node")
        source_node_ids = request.form.get("source_node_ids", "")
        
        node = flow_service.create_report_node(
            analysis_id,
            x,
            y,
            name,
            source_node_ids,
            owner_id
        )
        return node
    
    def _handle_creating_notebook_node(self, owner_id):
        analysis_id = int(request.form.get("analysis_id"))
        x = float(request.form.get("x"))
        y = float(request.form.get("y"))
        name = request.form.get("name", "Notebook Node")
        computation_resource_configure = request.form.get("computation_resource_configure", None)
        system_env = request.form.get("system_env", SystemEnv.AWS_BATCH.value)
        dynamic_generation_id = request.form.get("dynamic_generation_id", None)
        node = flow_service.create_notebook_node(
            analysis_id,
            x,
            y,
            name,
            owner_id,
            system_env=system_env,
            dynamic_generation_id=dynamic_generation_id,
            computation_resource_configure=computation_resource_configure
        )
        return node

    def _handle_creating_claude_code_node(self, owner_id):
        analysis_id = int(request.form.get("analysis_id"))
        x = float(request.form.get("x"))
        y = float(request.form.get("y"))
        name = request.form.get("name", "Claude Code Node")
        computation_resource_configure = request.form.get("computation_resource_configure", None)
        system_env = request.form.get("system_env", SystemEnv.AWS_BATCH.value)
        dynamic_generation_id = request.form.get("dynamic_generation_id", None)
        node = flow_service.create_claude_code_node(
            analysis_id,
            x,
            y,
            name,
            owner_id,
            system_env=system_env,
            dynamic_generation_id=dynamic_generation_id,
            computation_resource_configure=computation_resource_configure,
        )
        return node

    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_form_check(
            request=request,
            checked_list=["node_type", "analysis_id", 'x', 'y']
        )
        node_type = request.form.get("node_type")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        analysis_id = request.form.get("analysis_id")
        guardian.check_authority(analysis_id, check_writable=True)
        user_id = guardian.get_user_id()
        if node_type == NodeType.DATA_NODE.value:
            new_node = self._handle_creating_data_node(user_id)
        elif node_type in [NodeType.COMPUTATION_NODE.value, NodeType.COMPUTATION_NODE_V2.value]:
            new_node = self._handle_creating_computation_node(user_id)
        elif node_type == NodeType.REPORT_NODE.value:
            new_node = self._handle_creating_report_node(user_id)
        elif node_type == NodeType.NOTEBOOK_NODE.value:
            new_node = self._handle_creating_notebook_node(user_id)
        elif node_type == NodeType.CLAUDE_CODE_NODE.value:
            new_node = self._handle_creating_claude_code_node(user_id)
        else:
            raise ParameterInvalidException("node_type is invalid")
        return ResponseManager.new_success_response(data=new_node)


class ListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        mode = request.args.get("mode", NodeListFetchMode.ANALYSIS.value)
        node_list: List[Node] = []
        if mode == NodeListFetchMode.ANALYSIS.value:
            request_auditor.request_args_check(
                request=request,
                checked_list=["analysis_id"]
            )
            analysis_id = request.args.get("analysis_id")
            with_computation = request.args.get("with_computation", "0") == "1"
            guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
            guardian.check_authority(analysis_id)
            node_list = flow_service.get_node_list_by_analysis_id(
                analysis_id,
                with_computation
            )
        elif mode == NodeListFetchMode.IDX.value:
            node_id_list = request.args.getlist("node_id_list[]")
            node_list = flow_service.get_node_list_by_idx(
                node_id_list
            )
        else:
            raise ParameterInvalidException("mode is invalid")
        return ResponseManager.new_success_response(data=node_list)
    
class PreviousNodeListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["node_id"]
        )
        node_id = request.args.get("node_id")
        with_self = request.args.get("with_self", "0") == "1"
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id)
        previous_node_list = flow_service.get_previous_node_list_by_node_id(node_id, with_self)
        return ResponseManager.new_success_response(data=previous_node_list)
    

class PreviousPathGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["node_id"]
        )
        node_id = request.args.get("node_id")
        with_self = request.args.get("with_self", "0") == "1"
        previous_node_list, previous_edge_list = flow_service.get_previous_path_by_node_id(node_id, with_self)
        return ResponseManager.new_success_response(data={
            "previousNodeList": previous_node_list,
            "previousEdgeList": previous_edge_list
        })

class ParentNodesGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["node_id"]
        )
        node_id = request.args.get("node_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id)
        parent_nodes = flow_service.get_parent_node_list_by_node_id(node_id)
        return ResponseManager.new_success_response(data=parent_nodes)

class PreviteStateDictGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["analysis_id"]
        )
        analysis_id = request.args.get("analysis_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_authority(analysis_id)
        previte_state_dict = flow_service.get_node_previte_dict_by_analysis_id(analysis_id)
        return ResponseManager.new_success_response(data=previte_state_dict)

# class NameEditAPI(Resource):
#     @exception_wrapper
#     @transaction_wrapper
#     def post(self):
#         request_auditor.request_form_check(
#             request=request,
#             checked_list=["node_id", "name"]
#         )
#         node_id = request.form.get("node_id")
#         guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
#         guardian.check_authority(node_id)
#         name = request.form.get("name")
#         flow_service.edit_node_name(
#             node_id,
#             name
#         )
#         return ResponseManager.new_success_response()

# class TagEditAPI(Resource):
#     @exception_wrapper
#     @transaction_wrapper
#     def post(self):
#         request_auditor.request_args_check(
#             request=request,
#             checked_list=["node_id", "tag"]
#         )
#         node_id = request.args.get("node_id")
#         guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
#         guardian.check_authority(node_id)
#         tag = request.args.get("tag")
#         flow_service.edit_node_tag(
#             node_id,
#             tag
#         )
#         return ResponseManager.new_success_response()



# class ParamsEditAPI(Resource):
#     @exception_wrapper
#     @transaction_wrapper
#     def post(self):
#         request_auditor.request_json_check(
#             request=request,
#             checked_list=["node_id", "computation_params"]
#         )
#         post_data = request.get_json()
#         node_id = post_data.get("node_id")
#         guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
#         guardian.check_authority(node_id)
#         computation_params = post_data.get("computation_params")
#         flow_service.edit_node_params(
#             node_id,
#             computation_params
#         )
#         return ResponseManager.new_success_response()


class DeleteAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def delete(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["node_id"]
        )
        node_id = request.args.get("node_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id, check_writable=True)
        flow_service.remove_node(node_id)
        return ResponseManager.new_success_response()

class BatchDeleteAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(
            request=request,
            checked_list=["node_id_list"]
        )
        post_data = request.get_json()
        node_id_list = post_data.get("node_id_list")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        for node_id in node_id_list:
            guardian.check_authority(node_id, check_writable=True)
        flow_service.batch_remove_node(node_id_list)
        return ResponseManager.new_success_response()


# class MoveAPI(Resource):
#     @exception_wrapper
#     @transaction_wrapper
#     def post(self):
#         request_auditor.request_form_check(
#             request=request,
#             checked_list=["node_id", "x", "y"]
#         )
#         node_id = request.form.get("node_id")
#         guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
#         guardian.check_authority(node_id)
#         x = request.form.get("x")
#         y = request.form.get("y")
#         flow_service.move_node(node_id, x, y)
#         return ResponseManager.new_success_response()

class BatchMoveAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        request_auditor.request_json_check(
            request=request,
            checked_list=["target_list"]
        )
        post_data = request.get_json()
        target_list = post_data.get("target_list")
        for target in target_list:
            node_id = target.get("node_id")
            guardian.check_authority(node_id)
            x = target.get("x")
            y = target.get("y")
            flow_service.move_node(node_id, x, y)
        return ResponseManager.new_success_response()

class ParamsGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["node_id"]
        )
        node_id = request.args.get("node_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id)
        params = flow_service.get_node_params(node_id)
        return ResponseManager.new_success_response(data=params)


class CopyAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["node_id"]
        )
        node_id = request.args.get("node_id")
        with_edges = request.args.get("with_edges", "0") == "1"
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        user_id = guardian.get_user_id()
        guardian.check_authority(node_id, check_writable=True)
        new_node = flow_service.copy_node(node_id, user_id, with_edges=with_edges)
        return ResponseManager.new_success_response(data=new_node)
    
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["node_id"]
        )
        node_id = request.args.get("node_id")
        updated_attrs = request.get_json()
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        user_id = guardian.get_user_id()
        guardian.check_authority(node_id, check_writable=True)
        new_node = flow_service.copy_node(node_id, user_id, updated_attrs=updated_attrs)
        return ResponseManager.new_success_response(data=new_node)

class ParamsRestoreAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_form_check(
            request=request,
            checked_list=["node_id"]
        )
        node_id = request.form.get("node_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id, check_writable=True)
        node = flow_service.get_node_by_id(node_id)
        fb_record = function_block_v1_service.get_current_version(node.function_block_id)
        args = fb_record.to_dict()["args"]
        default_value_dict = FunctionBlockTool.abstract_args_attr_dict_by_name(args, "default_value")
        flow_service.edit_node_params(
            node_id,
            default_value_dict
        )
        return ResponseManager.new_success_response(data=default_value_dict)

class TagListGetAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_json_check(
            request,
            checked_list=["node_id_list"]
        )
        post_data = request.get_json()
        node_id_list = post_data.get("node_id_list")
        AuthorityGuardianFactory.get_authority_guardian()
        tag_list = flow_service.get_node_tag_list(node_id_list)
        return ResponseManager.new_success_response(data=tag_list)
    
class GetByComputationAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["computation_id"]
        )
        computation_id = request.args.get("computation_id")
        node = flow_service.get_node_by_computation_id(computation_id)
        return ResponseManager.new_success_response(data=node)

class ParamFileListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["node_id"]
        )
        node_id = request.args.get("node_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id)
        file_list = flow_service.get_node_param_file_list(node_id)
        return ResponseManager.new_success_response(data=file_list)
    
class ParamFileDownloadRequestAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["node_id", "file_name"]
        )
        node_id = request.args.get("node_id")
        file_name = request.args.get("file_name")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id)
        url = flow_service.request_download_node_param_file(node_id, file_name)
        return ResponseManager.new_success_response(data=url)

class ParamFileUploadRequestAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["node_id", "file_name", "file_size"]
        )
        node_id = request.args.get("node_id")
        file_name = request.args.get("file_name")
        file_size = int(request.args.get("file_size"))
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id, check_writable=True)
        url = flow_service.request_upload_node_param_file(node_id, file_name, file_size)
        return ResponseManager.new_success_response(data=url)
    
class ParamFileDeleteAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def delete(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["node_id", "file_name"]
        )
        node_id = request.args.get("node_id")
        file_name = request.args.get("file_name")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id, check_writable=True)
        flow_service.remove_node_param_file(node_id, file_name)
        return ResponseManager.new_success_response()
    
class NodeInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["node_id"]
        )
        node_id = request.args.get("node_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id)
        node = flow_service.get_node_by_id(node_id)
        return ResponseManager.new_success_response(data=node)

class NodeInformationGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["node_id"]
        )
        node_id = request.args.get("node_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(node_id)
        information = flow_service.get_information(node_id)
        return ResponseManager.new_success_response(data=information)
    
# class ComputationSystemEnvChangeAPI(Resource):
#     @exception_wrapper
#     @transaction_wrapper
#     def post(self):
#         request_auditor.request_json_check(
#             request=request,
#             checked_list=["node_id", "system_env"]
#         )
#         post_data = request.get_json()
#         node_id = post_data.get("node_id")
#         system_env = post_data.get("system_env")
#         guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
#         guardian.check_authority(node_id)
#         flow_service.edit_node_system_env(node_id, system_env)
#         return ResponseManager.new_success_response()
    
class MiniToolGetAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(
            request=request,
            checked_list=["function_block_id"]
        )
        function_block_id = request.args.get("function_block_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.FUNCTION_BLOCK.value)
        user_id = guardian.get_user_id()
        mini_tool = flow_service.get_mini_tool_node(function_block_id, user_id)
        return ResponseManager.new_success_response(data=mini_tool)

node_bp = Blueprint("node", __name__)
node_api = Api(node_bp, prefix="/node")
node_api.add_resource(NodeEditAPI, "/edit")
node_api.add_resource(NodeBatchEditAPI, "/batch-edit")
node_api.add_resource(CreateAPI, "/create")
node_api.add_resource(ListGetAPI, "/list/get")
node_api.add_resource(PreviousNodeListGetAPI, "/get-previous-node-list")
node_api.add_resource(PreviousPathGetAPI, "/get-previous-path")
node_api.add_resource(ParentNodesGetAPI, "/get-parent-nodes")
node_api.add_resource(PreviteStateDictGetAPI, "/get-previte-state-dict")
# node_api.add_resource(NameEditAPI, "/name/edit")
# node_api.add_resource(TagEditAPI, "/tag/edit")
# node_api.add_resource(ParamsEditAPI, "/params/edit")
node_api.add_resource(DeleteAPI, "/delete")
node_api.add_resource(BatchDeleteAPI, "/batch-delete")
# node_api.add_resource(MoveAPI, "/move")
node_api.add_resource(BatchMoveAPI, "/batch-move")
node_api.add_resource(ParamsGetAPI, "/params/get")
node_api.add_resource(CopyAPI, "/copy")
node_api.add_resource(ParamsRestoreAPI, "/params/restore")
node_api.add_resource(TagListGetAPI, "/tag-list/get")
node_api.add_resource(GetByComputationAPI, "/get-by-computation")
node_api.add_resource(ParamFileListGetAPI, "/list-params-files")
node_api.add_resource(ParamFileDownloadRequestAPI, "/request-download-param-file")
node_api.add_resource(ParamFileUploadRequestAPI, "/request-upload-param-file")
node_api.add_resource(ParamFileDeleteAPI, "/delete-param-file")
node_api.add_resource(NodeInfoGetAPI, "/get-info")
node_api.add_resource(NodeInformationGetAPI, "/get-information")
# node_api.add_resource(ComputationSystemEnvChangeAPI, "/change-system-env")
node_api.add_resource(MiniToolGetAPI, "/get-mini-tool-node")
from flask import Blueprint, request, send_file
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from tool.gpt_space_manager import GptSpaceManager
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from service.analysis import analysis_service
from service.flow import flow_service
from service.gpt import gpt_service
from service.computation import computation_service
from sss.porter_factory import PorterFactory
from wrapper.exception import exception_wrapper
from wrapper.db_session import transaction_wrapper
from exception.request.parameter_invalid import ParameterInvalidException
from log.logger_factory import logger_factory
from llm.llm_interface import LlmInterface
from service.data import data_service
from service.branch_report import branch_report_service
from service.figure_description import figure_description_service
from service.consumption import consumption_service
from dao.node import node_dao
from model.llm_consumption import LLMConsumption
import json
import uuid
import time
logger = logger_factory.create_logger("chat controller")

class ChatInitAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "analysis_id"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        analysis_id = request.args.get("analysis_id")
        owner_id = guardian.get_user_id()
        llm_interface = LlmInterface()
        response = llm_interface.init_chat(analysis_id, owner_id)
        return ResponseManager.new_raw_response(response.status_code, response.text)

class ChatHistroyAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "analysis_id"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        analysis_id = request.args.get("analysis_id")
        owner_id = guardian.get_user_id()
        llm_interface = LlmInterface()
        response = llm_interface.get_chat_history(analysis_id, owner_id)
        return ResponseManager.new_raw_response(response.status_code, response.text)

class ChatSendAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "analysis_id",
            "message",
            "chat_id"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        analysis_id = request.args.get("analysis_id")
        chat_id = request.args.get("chat_id")
        message = request.args.get("message")
        owner_id = guardian.get_user_id()
        llm_interface = LlmInterface()
        response = llm_interface.send_message(analysis_id, owner_id, chat_id, message)
        return ResponseManager.new_raw_response(response.status_code, response.text)

class GlobalChatInitAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "analysis_id",
        ]
        )
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        analysis_id = request.args.get("analysis_id")
        user_id = guardian.get_user_id()
        llm_interface = LlmInterface()
        response = llm_interface.init_global_chat(analysis_id, user_id)
        return ResponseManager.new_raw_response(response.status_code, response.text)

class GlobalChatSendAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "analysis_id",
            "message",
            "chat_id"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        analysis_id = request.args.get("analysis_id")
        chat_id = request.args.get("chat_id")
        message = request.args.get("message")
        owner_id = guardian.get_user_id()
        llm_interface = LlmInterface()
        response = llm_interface.send_global_message(analysis_id, owner_id, chat_id, message)
        return ResponseManager.new_raw_response(response.status_code, response.text)

class LocalChatInitAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "analysis_id",
            "node_id"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        analysis_id = request.args.get("analysis_id")
        node_id = request.args.get("node_id")
        owner_id = guardian.get_user_id()
        llm_interface = LlmInterface()
        response = llm_interface.init_local_chat(analysis_id, node_id, owner_id)
        return ResponseManager.new_raw_response(response.status_code, response.text)

class LocalChatSendAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "analysis_id",
            "message",
            "chat_id"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        analysis_id = request.args.get("analysis_id")
        chat_id = request.args.get("chat_id")
        message = request.args.get("message")
        owner_id = guardian.get_user_id()
        llm_interface = LlmInterface()
        response = llm_interface.send_local_message(analysis_id, owner_id, chat_id, message)
        return ResponseManager.new_raw_response(response.status_code, response.text)

class ComplexChatListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "analysis_id"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        analysis_id = request.args.get("analysis_id")
        owner_id = guardian.get_user_id()
        llm_interface = LlmInterface()
        response = llm_interface.get_complex_chat_list(analysis_id, owner_id)
        return ResponseManager.new_raw_response(response.status_code, response.text)

class ComplexChatMessageListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "thread_id"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        thread_id = request.args.get("thread_id")
        llm_interface = LlmInterface()
        response = llm_interface.get_complex_chat_message_list(thread_id, user_id)
        return ResponseManager.new_raw_response(response.status_code, response.text)

class ComplexChatInitAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "analysis_id"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        analysis_id = request.args.get("analysis_id")
        owner_id = guardian.get_user_id()
        llm_interface = LlmInterface()
        response = llm_interface.init_complex_chat(analysis_id, owner_id)
        return ResponseManager.new_raw_response(response.status_code, response.text)

class ComplexChatSendAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "analysis_id",
            "message",
            "thread_id"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        analysis_id = request.args.get("analysis_id")
        thread_id = request.args.get("thread_id")
        message = request.args.get("message")
        owner_id = guardian.get_user_id()
        llm_interface = LlmInterface()
        response = llm_interface.send_complex_message(analysis_id, owner_id, thread_id, message)
        return ResponseManager.new_raw_response(response.status_code, response.text)

class ListSpaceAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        request_auditor.request_args_check(request, [
            "prefix",
            "search_key"
        ])
        owner_id = guardian.get_user_id()
        prefix = request.args.get("prefix")
        search_key = request.args.get("search_key")
        gpt_space_manager = GptSpaceManager()
        result = gpt_space_manager.list_files(owner_id, prefix, search_key, False)
        return ResponseManager.new_success_response(data=result)

class ListAllChildrenAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        request_auditor.request_args_check(request, [
            "prefix",
            "search_key"
        ])
        owner_id = guardian.get_user_id()
        prefix = request.args.get("prefix")
        search_key = request.args.get("search_key")
        gpt_space_manager = GptSpaceManager()
        result = gpt_space_manager.list_files(owner_id, prefix, search_key, True)
        return ResponseManager.new_success_response(data=result)

class UploadFileAPI(Resource):
    @exception_wrapper
    def post(self):
        # form
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        owner_id = guardian.get_user_id()
        request_auditor.request_form_check(request, [
            "prefix",
            "file_name"
        ])
        file = request.files["file"]
        prefix = request.form.get("prefix")
        file_name = request.form.get("file_name")
        gpt_space_manager = GptSpaceManager()
        gpt_space_manager.upload_file(owner_id, file, prefix, file_name)
        return ResponseManager.new_success_response()

class DownloadFileAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        owner_id = guardian.get_user_id()
        request_auditor.request_args_check(request, [
            "prefix",
            "file_name"
        ])
        prefix = request.args.get("prefix")
        file_name = request.args.get("file_name")
        gpt_space_manager = GptSpaceManager()
        temp_path = gpt_space_manager.download_file(owner_id, prefix, file_name)
        return send_file(temp_path, as_attachment=True)

class PipelineRecommandAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "user_request"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        post_data = request.get_json()
        user_request = post_data.get("user_request")
        llm_interface = LlmInterface()
        max_retry = 3
        retry = 0
        while retry <= max_retry:
            retry += 1
            try:
                response = llm_interface.recommend_pipeline(user_request, user_id)
                if response.status_code != 200:
                    raise Exception(f"recommend pipeline failed: {response.status_code}")
                response_data = response.json()
                recommend_structure = response_data.get("data", {})
                recommend_structure = json.loads(recommend_structure)
                if flow_service.validate_recommend_structure(recommend_structure):
                    return ResponseManager.new_raw_response(response.status_code, response.text)
                else:
                    raise Exception(f"recommend pipeline failed: {recommend_structure}")
            except Exception as e:
                logger.error(f"{e}, retry: {retry}")
        raise Exception("recommend pipeline failed")
    
class SimilarPipelineTemplateGetAPI(Resource):
    @exception_wrapper
    def post(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        request_auditor.request_json_check(request, [
            "user_request"
        ])
        post_data = request.get_json()
        user_request = post_data.get("user_request")
        llm_interface = LlmInterface()
        response = llm_interface.get_similar_pipeline_template(user_request, user_id)
        return ResponseManager.new_raw_response(response.status_code, response.text)
    
class ParamsFillAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "history",
            "node_id"
        ])
        post_data = request.get_json()
        param_dict = post_data.get("param_dict")
        history = post_data.get("history")
        node_id = post_data.get("node_id")
        to_create_function = post_data.get("to_create_function", "0")
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        llm_interface = LlmInterface()
        response = llm_interface.fill_params(node_id, param_dict, history, to_create_function, user_id)
        return ResponseManager.new_raw_response(response.status_code, response.text)
    
class NodeReportGenerateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "history",
            "node_id"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        post_data = request.get_json()
        history = post_data.get("history")
        node_id = post_data.get("node_id")
        llm_interface = LlmInterface()
        response = llm_interface.get_node_report(node_id, history, user_id)
        node = node_dao.find_by_id(node_id)
        json_data = response.json()
        consumption = json_data.get("consumption", {})
        consumption["user_id"] = user_id
        consumption["functionality"] = "Node Report Generation"
        consumption["functionality_task_id"] = node.analysis_id
        consumption["node_id"] = node_id
        consumption_service.record_consumption(consumption)
        node_report_content = json_data.get("data", "")
        latest_compution = computation_service.get_latest_by_node(node_id)
        if latest_compution:
            computation_service.save_computation_report(latest_compution.id, node_report_content)
        return ResponseManager.new_raw_response(response.status_code, response.text)
    
class WorkflowReportCreateAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "computation_details_list",
            "node_ids",
            "analysis_id",
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        post_data = request.get_json()
        node_ids = post_data.get("node_ids")
        computation_details_list = post_data.get("computation_details_list")
        analysis_id = post_data.get("analysis_id")
        llm_interface = LlmInterface()
        uuid_str = uuid.uuid4().hex
        response = llm_interface.create_workflow_report(node_ids, computation_details_list, analysis_id, uuid_str, user_id)
        return ResponseManager.new_raw_response(response.status_code, response.text)

class BranchReportGenerateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "analysis_id",
            "branch_nodes", 
            "report_node"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        post_data = request.get_json()
        analysis_id = post_data.get("analysis_id")
        branch_nodes = post_data.get("branch_nodes")
        report_node = post_data.get("report_node")
        model = post_data.get("model", "gpt-4o-mini")
        
        response = branch_report_service.generate_branch_report(
            analysis_id, branch_nodes, report_node, user_id, model
        )
        
        if response and response.status_code == 200:
            try:
                response_data = response.json()
                consumption = response_data['consumption']
                if consumption:
                    consumption["user_id"] = user_id
                    consumption["functionality"] = "Branch Report Manual"
                    consumption["functionality_task_id"] = analysis_id
                    consumption["node_id"] = report_node.get('id', -1)
                    gpt_service.record_consumption(consumption, user_id)
            except Exception as e:
                logger.error(f"Error recording token consumption for manual report: {e}")
        
        return ResponseManager.new_raw_response(response.status_code, response.text)

class BranchReportGenerateAutomatedAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "analysis_id",
            "branch_nodes", 
            "report_node"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        post_data = request.get_json()
        analysis_id = post_data.get("analysis_id")
        branch_nodes = post_data.get("branch_nodes")
        report_node = post_data.get("report_node")
        model = post_data.get("model", "gpt-4o-mini")
        
        response = branch_report_service.generate_branch_report_automated(
            analysis_id, branch_nodes, report_node, user_id, model
        )
        
        if response and response.status_code == 200:
            try:
                response_data = response.json()
                consumption = response_data['consumption']
                if consumption:
                    consumption["user_id"] = user_id
                    consumption["functionality"] = "Branch Report Automation"
                    consumption["functionality_task_id"] = analysis_id
                    consumption["node_id"] = report_node.get('id', -1)
                    gpt_service.record_consumption(consumption, user_id)
            except Exception as e:
                logger.error(f"Error recording token consumption for automated report: {e}")
        
        return ResponseManager.new_raw_response(response.status_code, response.text)

class SelectFiguresAutomatedAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "analysis_id",
            "branch_nodes"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        post_data = request.get_json()
        analysis_id = post_data.get("analysis_id")
        branch_nodes = post_data.get("branch_nodes")
        model = post_data.get("model", "gpt-4o-mini")
        
        response = branch_report_service.select_figures_automated(
            analysis_id, branch_nodes, user_id, model
        )
        
        if response and response.status_code == 200:
            try:
                response_data = response.json()
                consumption = response_data['consumption']
                if consumption:
                    consumption["user_id"] = user_id
                    consumption["functionality"] = "Branch Report Automation"
                    consumption["functionality_task_id"] = analysis_id
                    consumption["node_id"] = -1  # No specific node ID
                    gpt_service.record_consumption(consumption, user_id)
            except Exception as e:
                logger.error(f"Error recording token consumption for figure selection: {e}")
        
        return ResponseManager.new_raw_response(response.status_code, response.text)

class GenerateFigureDescriptionAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "figure_uuid",
            "figure_name"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        post_data = request.get_json()
        figure_uuid = post_data.get("figure_uuid")
        figure_name = post_data.get("figure_name")
        node_name = post_data.get("node_name")
        
        response = figure_description_service.generate_figure_description(
            figure_uuid, figure_name, node_name, user_id
        )
        
        if response and response.status_code == 200:
            try:
                response_data = response.json()
                consumption = response_data['consumption']
                if consumption:
                    consumption["user_id"] = user_id
                    consumption["functionality"] = "Figure Description Generation"
                    consumption["functionality_task_id"] = -1
                    consumption["node_id"] = -1  # No specific node ID
                    gpt_service.record_consumption(consumption, user_id)
            except Exception as e:
                logger.error(f"Error recording token consumption: {e}")
            
            return ResponseManager.new_raw_response(response.status_code, response.text)
        else:
            return ResponseManager.new_error_response(
                message="Failed to generate figure description"
            )

class BatchGenerateFigureDescriptionsAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "figures"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        post_data = request.get_json()
        figures = post_data.get("figures")
        
        response = figure_description_service.batch_generate_descriptions(
            figures, user_id
        )
        
        if isinstance(response, dict):
            if response.get('status') == 'error':
                return ResponseManager.new_error_response(
                    message=response.get('message', 'Failed to generate descriptions')
                )
            else:
                return ResponseManager.new_success_response(response)
        elif response and response.status_code == 200:
            try:
                response_data = response.json()
                result = response_data.get('data', {})
                consumptions = [item.get("consumption", {}) for item in result.get("successful", [])] + [item.get("consumption", {}) for item in result.get("failed", [])]
                total_consumption = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
                for consumption in consumptions:
                    total_consumption["prompt_tokens"] += consumption.get("prompt_tokens", 0)
                    total_consumption["completion_tokens"] += consumption.get("completion_tokens", 0)
                    total_consumption["total_tokens"] += consumption.get("total_tokens", 0)
                    if "model" not in total_consumption and "model" in consumption:
                        total_consumption["model"] = consumption.get("model", "gpt-4o")
                total_consumption["functionality"] = "Batch Figure Description Generation"
                total_consumption["functionality_task_id"] = -1
                total_consumption["node_id"] = -1  # No specific node ID
                gpt_service.record_consumption(total_consumption, user_id)
            except Exception as e:
                logger.error(f"Error recording batch token consumption: {e}")
            
            return ResponseManager.new_raw_response(response.status_code, response.text)
        else:
            return ResponseManager.new_error_response(
                message="Failed to generate figure descriptions"
            )
    
class AIUsedRecordGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "offset",
            "limit"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        offset = request.args.get("offset")
        limit = request.args.get("limit")
        records, total = gpt_service.get_by_user_id(user_id, offset, limit)
        return ResponseManager.new_success_response(data={
            "records": records,
            "total": total
        })
    
class DynamicFBAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "node_id",
            "user_request",
            "history"
        ])
        AuthorityGuardianFactory.get_authority_guardian()
        post_data = request.get_json()
        node_id = post_data.get("node_id")
        user_request = post_data.get("user_request")
        history = post_data.get("history")
        llm_interface = LlmInterface()
        response = llm_interface.dynamic_fb(user_request, node_id, history)
        return ResponseManager.new_raw_response(response.status_code, response.text)
        

class DataCaptureAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        user_request = request.args.get("user_request")
        result = data_service.capture_data_list_by_llm(user_id, user_request)
        return ResponseManager.new_success_response(data=result)

class RecordConsumption(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "consumption"
        ])
        post_data = request.get_json()
        consumption = post_data.get("consumption")
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        consumption = gpt_service.record_consumption(consumption, user_id)
        return ResponseManager.new_success_response(data=consumption)

class BranchReportPresignedUrlAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "report_id"
        ])
        report_id = request.args.get("report_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        
        logger.debug(f"Presigned URL request for report_id={report_id}, user_id={user_id}")
        
        presigned_url = branch_report_service.get_branch_report_presigned_url(report_id)
        
        if presigned_url:
            return ResponseManager.new_success_response(data={"url": presigned_url})
        else:
            return ResponseManager.new_dynamic_status_code_response(404, "Report file not found")

gpt_bp = Blueprint("gpt", __name__)
gpt_api = Api(gpt_bp, prefix="/gpt")
gpt_api.add_resource(ChatSendAPI, "/chat/send")
gpt_api.add_resource(ChatInitAPI, "/chat/init")
gpt_api.add_resource(ChatHistroyAPI, "/chat/history")
gpt_api.add_resource(GlobalChatSendAPI, "/chat/send-global-message")
gpt_api.add_resource(GlobalChatInitAPI, "/chat/init-global-chat")
gpt_api.add_resource(LocalChatSendAPI, "/chat/send-local-message")
gpt_api.add_resource(LocalChatInitAPI, "/chat/init-local-chat")
gpt_api.add_resource(ComplexChatListGetAPI, "/complex-chat/list-chat")
gpt_api.add_resource(ComplexChatMessageListGetAPI, "/complex-chat/list-message")
gpt_api.add_resource(ComplexChatInitAPI, "/complex-chat/init-chat")
gpt_api.add_resource(ComplexChatSendAPI, "/complex-chat/send-message")
gpt_api.add_resource(ListSpaceAPI, "/space/list")
gpt_api.add_resource(ListAllChildrenAPI, "/space/list-all-children")
gpt_api.add_resource(UploadFileAPI, "/space/upload")
gpt_api.add_resource(DownloadFileAPI, "/space/download")
gpt_api.add_resource(PipelineRecommandAPI, "/recommend-pipeline")
gpt_api.add_resource(SimilarPipelineTemplateGetAPI, "/get-similar-pipeline-template")
gpt_api.add_resource(ParamsFillAPI, "/fill-params")
gpt_api.add_resource(NodeReportGenerateAPI, "/generate-node-report")
gpt_api.add_resource(WorkflowReportCreateAPI, "/create-workflow-report")
gpt_api.add_resource(BranchReportGenerateAPI, "/generate-branch-report")
gpt_api.add_resource(BranchReportGenerateAutomatedAPI, "/generate-branch-report-automated")
gpt_api.add_resource(SelectFiguresAutomatedAPI, "/select-figures-automated")
gpt_api.add_resource(GenerateFigureDescriptionAPI, "/generate-figure-description")
gpt_api.add_resource(BatchGenerateFigureDescriptionsAPI, "/batch-generate-figure-descriptions")
gpt_api.add_resource(AIUsedRecordGetAPI, "/get-used-record")
gpt_api.add_resource(DynamicFBAPI, "/dynamic-fb")
gpt_api.add_resource(DataCaptureAPI, "/capture-data")
gpt_api.add_resource(RecordConsumption, "/record-consumption")
gpt_api.add_resource(BranchReportPresignedUrlAPI, "/get-branch-report-presigned-url")

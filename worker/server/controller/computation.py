from flask import Blueprint, request
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from service.computation import computation_service
from service.task import task_service
from service.llm import llm_service
from log.logger_factory import LoggerFactory
from constants.authority import AuthorityCarrier
from constants.computation import ComputationState

logger = LoggerFactory.get_logger("ComputationController")


class ListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["mode"])
        mode = request.args.get("mode", None)
        if mode == "node":
            guardian = AuthorityGuardianFactory.get_authority_guardian(
                AuthorityCarrier.NODE.value)
            request_auditor.request_args_check(request, ["node_id"])
            node_id = request.args.get("node_id", None)
            guardian.check_authority(node_id)
            result = computation_service.get_list_by_node(node_id)
            return ResponseManager.new_success_response(data=result)
        elif mode == "task":
            request_auditor.request_args_check(request, ["task_id"])
            task_id = request.args.get("task_id", None)
            result = computation_service.get_list_by_task(task_id)
            return ResponseManager.new_success_response(data=result)
        return ResponseManager.new_bad_request_response("mode is invalid")


class ComputationSummaryGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "computation_id"
        ])
        computation_id = request.args.get("computation_id")
        summary = computation_service.get_summary(computation_id)
        return ResponseManager.new_success_response(summary)


class ComputationLogsGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "computation_id"
        ])
        computation_id = request.args.get("computation_id")
        logs = computation_service.get_log(computation_id)
        return ResponseManager.new_success_response(logs)


class FiguresGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "computation_id"
        ])
        computation_id = request.args.get("computation_id")
        figures = computation_service.get_figures(computation_id)
        return ResponseManager.new_success_response(figures)


class LatestByNodeGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.NODE.value)
        request_auditor.request_args_check(request, ["node_id"])
        node_id = request.args.get("node_id", None)
        guardian.check_authority(node_id)
        result = computation_service.get_latest_by_node(node_id)
        return ResponseManager.new_success_response(data=result)


class OptimizedErrorDescriptionRefreshAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        request_auditor.request_args_check(request, ["computation_id"])
        computation_id = request.args.get("computation_id", None)
        result = computation_service.refresh_optimized_error_description(
            computation_id, user_id)
        return ResponseManager.new_success_response(data=result)


class OutputFilesListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            [
                "computation_id"
            ]
        )
        computation_id = request.args.get("computation_id")
        prefix = request.args.get("prefix", None)
        start_after_file_name = request.args.get("start_after_file_name", "")
        max_keys = request.args.get("max_keys", 50, type=int)
        search_query = request.args.get("search_query", None)
        file_type_filter = request.args.get("file_type_filter", None)
        
        result = computation_service.list_output_files(
            computation_id, prefix, start_after_file_name, 
            max_keys, search_query, file_type_filter)
        return ResponseManager.new_success_response(data=result)


class OutputFoldersListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        List output folders with file counts and sizes.
        Designed for tree view display of Claude Code outputs.

        Query params:
        - computation_id: The computation ID (required)
        - prefix: Optional folder prefix to list subfolders from

        Returns:
        {
            "folders": [{"name": "step_01_...", "path": "...", "file_count": 10, "total_size": 12345}],
            "root_files": [{"file_name": "summary.md", ...}],
            "total_folders": 5,
            "total_root_files": 3
        }
        """
        request_auditor.request_args_check(request, ["computation_id"])
        computation_id = request.args.get("computation_id")
        prefix = request.args.get("prefix", None)

        result = computation_service.list_output_folders(computation_id, prefix)
        return ResponseManager.new_success_response(data=result)


class OutputFileCollectAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(
            request,
            [
                "computation_id",
                "file_name"
            ]
        )
        computation_id = request.args.get("computation_id")
        prefix = request.args.get("prefix", None)
        file_name = request.args.get("file_name", None)
        result = computation_service.collect_output_file(
            computation_id, prefix, file_name)
        return ResponseManager.new_success_response(data=result)


class OutputFileDownloadInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            [
                "object_key",
                "computation_id"
            ]
        )
        object_key = request.args.get("object_key")
        computation_id = request.args.get("computation_id")
        result = computation_service.get_output_file_download_info(object_key, computation_id)
        return ResponseManager.new_success_response(data=result)


class ComputationRetryProcessStopAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(request, ["retry_process_id"])
        retry_process_id = request.args.get("retry_process_id")
        computation_service.stop_retry_process(retry_process_id)
        return ResponseManager.new_success_response()


class ComputationRetryProcessListByNodeAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["node_id"])
        node_id = request.args.get("node_id")
        result = computation_service.get_retry_process_list_by_node(node_id)
        return ResponseManager.new_success_response(data=result)


class ComputationRetryProcessListByAnalysisAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["analysis_id"])
        analysis_id = request.args.get("analysis_id")
        result = computation_service.get_retry_process_list_by_analysis(
            analysis_id)
        return ResponseManager.new_success_response(data=result)


class ComputationRetryProcessFixHistoryDetailsGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["retry_process_id"])
        retry_process_id = request.args.get("retry_process_id")
        result = computation_service.get_retry_process_history_details(
            retry_process_id)
        return ResponseManager.new_success_response(data={
            "history": result
        })


class ComputationRetryProcessTriggerAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, ["node_id", "user_prompt"])
        post_data = request.get_json()
        node_id = post_data.get("node_id")
        user_prompt = post_data.get("user_prompt")
        max_debug = post_data.get("max_debug", "3")
        max_debug = int(max_debug)
        llm_model = post_data.get("llm_model", None)
        computation_service.trigger_retry_process(
            node_id, user_prompt, llm_model, max_debug)
        return ResponseManager.new_success_response()


class ComputationRetryProcessPromptGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request, ["retry_process_id", "computation_id"])
        retry_process_id = request.args.get("retry_process_id")
        computation_id = request.args.get("computation_id")
        result = computation_service.get_retry_process_prompt(
            retry_process_id, computation_id)
        return ResponseManager.new_success_response(data=result)


class ComputationLogsUploadAPI(Resource):
    @exception_wrapper
    def post(self):
        computation_id = request.args.get("computation_id")
        post_data = request.get_json()
        logs = post_data.get("logs")
        computation_service.set_logs(computation_id, logs)
        return ResponseManager.new_success_response()


class RetryProcessTraceGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["computation_id"])
        computation_id = request.args.get("computation_id")
        result = computation_service.get_retry_process_trace(computation_id)
        return ResponseManager.new_success_response(data=result)


class RetryProcessSessionGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["computation_id"])
        computation_id = request.args.get("computation_id")
        result = computation_service.get_retry_process_session(computation_id)
        return ResponseManager.new_success_response(data=result)


class BugFixerSessionRecordAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, ["session"])
        post_data = request.get_json()
        session = post_data.get("session")
        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.NODE.value)
        user_id = guardian.get_user_id()
        recorded_session = computation_service.record_bug_fixer_session(
            session, user_id)
        return ResponseManager.new_success_response(recorded_session)


class BugFixerSessionListAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["retry_process_id"])
        retry_process_id = request.args.get("retry_process_id")
        sessions = computation_service.list_bug_fixer_sessions(
            retry_process_id)
        return ResponseManager.new_success_response(sessions)
    
class ComputationCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [])
        attrs = request.json
        computation = computation_service.create_computation(attrs)
        return ResponseManager.new_success_response(computation)


class ComputationUpdateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(request, ["computation_id"])
        request_auditor.request_json_check(request, [])
        computation_id = request.args.get("computation_id")
        attrs = request.json
        computation = computation_service.update_computation(computation_id, attrs)
        return ResponseManager.new_success_response(computation)

class CodeAgentInvokeAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(request, ["node_id", "max_debug", "model"])
        node_id = request.args.get("node_id")
        max_debug = request.args.get("max_debug")
        model = request.args.get("model")
        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.NODE.value)
        user_id = guardian.get_user_id()
        result = task_service.invoke_code_agent(node_id, max_debug, model, user_id)
        return ResponseManager.new_success_response(data=result)


class FixDescriptionSaveAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """
        Save fix description for a computation
        
        Request body:
        {
            "computation_id": 123,
            "error_info": "Error stack trace or message...",
            "fix_strategy": "Explanation of the fix..."
        }
        """
        request_auditor.request_json_check(request, ["computation_id", "error_info", "fix_strategy"])
        post_data = request.get_json()
        computation_id = post_data.get("computation_id")
        error_info = post_data.get("error_info")
        fix_strategy = post_data.get("fix_strategy")
        
        result = computation_service.save_fix_description(computation_id, error_info, fix_strategy)
        return ResponseManager.new_success_response(data=result.to_dict())


class FixDescriptionListAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        Get all fix descriptions for a computation
        
        Query params:
        - computation_id: The computation ID
        """
        request_auditor.request_args_check(request, ["computation_id"])
        computation_id = request.args.get("computation_id")
        
        descriptions = computation_service.get_fix_descriptions(computation_id)
        return ResponseManager.new_success_response(data=[d.to_dict() for d in descriptions])

class ComputationPipeGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "node_id"
        ])
        node_id = request.args.get("node_id")
        pipeline = computation_service.get_computation_pipe(node_id)
        return ResponseManager.new_success_response(pipeline)


class JobReviewerMessagesUploadAPI(Resource):
    @exception_wrapper
    def post(self):
        """
        Upload job reviewer messages to S3
        
        Request body:
        {
            "computation_id": "123",
            "uuid": "random-uuid-string",
            "messages": [...]
        }
        """
        request_auditor.request_json_check(request, ["computation_id", "uuid", "messages"])
        post_data = request.get_json()
        computation_id = post_data.get("computation_id")
        uuid_str = post_data.get("uuid")
        messages = post_data.get("messages")
        
        object_key = computation_service.save_job_reviewer_messages(
            computation_id, uuid_str, messages)
        
        return ResponseManager.new_success_response(data={"object_key": object_key})
    
class JobReviewerReportReportAPI(Resource):
    @exception_wrapper
    def post(self):
        """
        Upload job reviewer report to S3
        
        Request body:
        {
            "computation_id": "123",
            "uuid": "random-uuid-string",
            "report": {...}
        }
        """
        request_auditor.request_args_check(request, ["computation_id", "uuid"])
        computation_id = request.args.get("computation_id")
        uuid_str = request.args.get("uuid")
        post_data = request.get_json()
        raw_report = post_data.get("raw_json")
        structured_report = post_data.get("structured_text")
        computation_service.save_job_reviewer_report(
            computation_id, uuid_str, raw_report, structured_report
        )
        

class JobReviewerErrorGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        Get job reviewer error messages from S3
        
        Query params:
        - computation_id: The computation ID
        - uuid: The UUID string used during upload
        """
        request_auditor.request_args_check(request, ["computation_id"])
        
        computation_id = request.args.get("computation_id")
        error_messages = computation_service.get_job_reviewer_error(computation_id)

        return ResponseManager.new_success_response(data=error_messages)


class JobReviewerReportsListAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        List all job reviewer reports for a computation
        
        Query params:
        - computation_id: The computation ID (required)
        
        Returns:
        List of report metadata objects with:
        - uuid: Report UUID
        - timestamp: Upload timestamp
        - object_key: S3 object key
        - computation_id: Computation ID
        """
        request_auditor.request_args_check(request, ["computation_id"])
        computation_id = request.args.get("computation_id")
        
        reports = computation_service.list_job_reviewer_reports(computation_id)
        return ResponseManager.new_success_response(data=reports)


class JobReviewerMessagesGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        Get job reviewer messages for a specific report
        
        Query params:
        - computation_id: The computation ID (required)
        - uuid: The report UUID (required)
        
        Returns:
        Messages object with conversation history
        """
        request_auditor.request_args_check(request, ["computation_id", "uuid"])
        computation_id = request.args.get("computation_id")
        uuid_str = request.args.get("uuid")
        
        messages = computation_service.get_job_reviewer_messages(computation_id, uuid_str)
        
        if messages is None:
            return ResponseManager.new_bad_request_response(
                f"Messages not found for computation {computation_id}, uuid {uuid_str}"
            )
        
        return ResponseManager.new_success_response(data=messages)


class JobReviewerReportGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        Get job reviewer report for a specific report
        
        Query params:
        - computation_id: The computation ID (required)
        - uuid: The report UUID (required)
        
        Returns:
        Report object with:
        - raw_report: JSON review result
        - structured_report: Formatted text report
        """
        request_auditor.request_args_check(request, ["computation_id", "uuid"])
        computation_id = request.args.get("computation_id")
        uuid_str = request.args.get("uuid")
        
        report = computation_service.get_job_reviewer_report(computation_id, uuid_str)
        
        if report is None:
            return ResponseManager.new_bad_request_response(
                f"Report not found for computation {computation_id}, uuid {uuid_str}"
            )
        
        return ResponseManager.new_success_response(data=report)

class AgentSessionCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """
        Create a new agent session record
        
        Request body:
        {
            "agent_type": "code_agent",
            "status": "completed",
            "current_node_id": 123,
            "current_analysis_id": 456,
            "current_computation_id": 789,
            "consumption_id": 111
        }
        """
        request_auditor.request_json_check(request, ["agent_type", "status"])
        post_data = request.get_json()
        
        agent_type = post_data.get("agent_type")
        status = post_data.get("status")
        current_node_id = post_data.get("current_node_id")
        current_analysis_id = post_data.get("current_analysis_id")
        current_computation_id = post_data.get("current_computation_id")
        consumption_id = post_data.get("consumption_id")
        
        session = llm_service.create_agent_session(
            agent_type=agent_type,
            status=status,
            current_node_id=current_node_id,
            current_analysis_id=current_analysis_id,
            current_computation_id=current_computation_id,
            consumption_id=consumption_id
        )
        
        return ResponseManager.new_success_response(data=session.to_dict())


class AgentSessionQueryByNodeAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        Query agent sessions by node_id
        
        Query params:
        - current_node_id: Node ID (required)
        - agent_type: Agent type filter (optional)
        """
        request_auditor.request_args_check(request, ["current_node_id"])
        current_node_id = int(request.args.get("current_node_id"))
        agent_type = request.args.get("agent_type")
        
        sessions = llm_service.query_sessions_by_node(current_node_id, agent_type)
        return ResponseManager.new_success_response(data=sessions)


class AgentSessionQueryByComputationAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        Query agent sessions by computation_id
        
        Query params:
        - current_computation_id: Computation ID (required)
        - agent_type: Agent type filter (optional)
        """
        request_auditor.request_args_check(request, ["current_computation_id"])
        current_computation_id = int(request.args.get("current_computation_id"))
        agent_type = request.args.get("agent_type")
        
        sessions = llm_service.query_sessions_by_computation(current_computation_id, agent_type)
        return ResponseManager.new_success_response(data=sessions)


class ProgrammingAgentMessagesUploadAPI(Resource):
    @exception_wrapper
    def post(self):
        """
        Upload programming agent messages to S3
        
        Request body:
        {
            "computation_id": "123",
            "uuid": "random-uuid-string",
            "messages": [...]
        }
        """
        request_auditor.request_json_check(request, ["computation_id", "uuid", "messages"])
        post_data = request.get_json()
        computation_id = post_data.get("computation_id")
        uuid_str = post_data.get("uuid")
        messages = post_data.get("messages")
        
        object_key = computation_service.save_programming_agent_messages(
            computation_id, uuid_str, messages)
        
        return ResponseManager.new_success_response(data={"object_key": object_key})


class ProgrammingAgentMessagesGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        Get programming agent messages with pagination
        
        Query params:
        - computation_id: The computation ID (required)
        - page: Page number (default: 1)
        - page_size: Items per page (default: 20)
        
        Returns:
        {
            "data": [...],
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_count": 100,
                "total_pages": 5,
                "has_more": true
            }
        }
        """
        request_auditor.request_args_check(request, ["computation_id"])
        computation_id = request.args.get("computation_id")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
        
        result = computation_service.get_programming_agent_messages(
            computation_id, page, page_size)
        
        return ResponseManager.new_success_response(data=result)


class VisualizerAgentMessagesUploadAPI(Resource):
    @exception_wrapper
    def post(self):
        """
        Upload visualizer agent messages to S3
        
        Request body:
        {
            "computation_id": "123",
            "uuid": "random-uuid-string",
            "messages": [...]
        }
        """
        request_auditor.request_json_check(request, ["computation_id", "uuid", "messages"])
        post_data = request.get_json()
        computation_id = post_data.get("computation_id")
        uuid_str = post_data.get("uuid")
        messages = post_data.get("messages")
        
        object_key = computation_service.save_visualizer_agent_messages(
            computation_id, uuid_str, messages)
        
        return ResponseManager.new_success_response(data={"object_key": object_key})


class VisualizerAgentMessagesGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """
        Get visualizer agent messages for a specific record
        
        Query params:
        - computation_id: The computation ID (required)
        - uuid: The report UUID (required)
        
        Returns:
        Messages object with conversation history
        """
        request_auditor.request_args_check(request, ["computation_id", "uuid"])
        computation_id = request.args.get("computation_id")
        uuid_str = request.args.get("uuid")
        
        messages = computation_service.get_visualizer_agent_messages(computation_id, uuid_str)
        
        if messages is None:
            return ResponseManager.new_bad_request_response(
                f"Messages not found for computation {computation_id}, uuid {uuid_str}"
            )
        
        return ResponseManager.new_success_response(data=messages)


computation_bp = Blueprint("computation", __name__)
computation_api = Api(computation_bp, "/computation")
computation_api.add_resource(ComputationSummaryGetAPI, "/get-summary")
computation_api.add_resource(ComputationLogsGetAPI, "/get-logs")
computation_api.add_resource(FiguresGetAPI, "/get-figures")
computation_api.add_resource(ListGetAPI, "/list")
computation_api.add_resource(LatestByNodeGetAPI, "/get-latest-by-node")
computation_api.add_resource(
    OptimizedErrorDescriptionRefreshAPI, "/refresh-optimized-error-description")
computation_api.add_resource(OutputFilesListGetAPI, "/list-output-files")
computation_api.add_resource(OutputFoldersListGetAPI, "/list-output-folders")
computation_api.add_resource(OutputFileCollectAPI, "/collect-output-file")
computation_api.add_resource(
    OutputFileDownloadInfoGetAPI, "/get-output-file-download-info")
computation_api.add_resource(
    ComputationRetryProcessStopAPI, "/stop-retry-process")
computation_api.add_resource(
    ComputationRetryProcessListByNodeAPI, "/list-retry-process-by-node")
computation_api.add_resource(
    ComputationRetryProcessListByAnalysisAPI, "/list-retry-process-by-analysis")
computation_api.add_resource(
    ComputationRetryProcessFixHistoryDetailsGetAPI, "/get-retry-process-fix-history-details")
computation_api.add_resource(
    ComputationRetryProcessTriggerAPI, "/trigger-retry-process")
computation_api.add_resource(
    ComputationRetryProcessPromptGetAPI, "/get-retry-process-prompt"
)
computation_api.add_resource(
    ComputationLogsUploadAPI, "/upload-logs"
)
computation_api.add_resource(
    RetryProcessTraceGetAPI, "/get-retry-process-trace"
)
computation_api.add_resource(
    RetryProcessSessionGetAPI, "/get-retry-process-session"
)
computation_api.add_resource(
    BugFixerSessionRecordAPI, "/record-bug-fixer-session"
)
computation_api.add_resource(ComputationCreateAPI, "/create")
computation_api.add_resource(ComputationUpdateAPI, "/update")
computation_api.add_resource(
    BugFixerSessionListAPI, "/list-bug-fixer-sessions"
)
computation_api.add_resource(
    CodeAgentInvokeAPI, "/invoke-code-agent"
)
computation_api.add_resource(
    FixDescriptionSaveAPI, "/save-fix-description"
)
computation_api.add_resource(
    FixDescriptionListAPI, "/list-fix-descriptions"
)
computation_api.add_resource(
    ComputationPipeGetAPI, "/get-computation-pipe"
)
computation_api.add_resource(
    JobReviewerMessagesUploadAPI, "/upload-job-reviewer-messages"
)
computation_api.add_resource(
    JobReviewerReportReportAPI, "/upload-job-reviewer-report"
)
computation_api.add_resource(
    JobReviewerErrorGetAPI, "/get-job-reviewer-error"
)
computation_api.add_resource(
    JobReviewerReportsListAPI, "/list-job-reviewer-reports"
)
computation_api.add_resource(
    JobReviewerMessagesGetAPI, "/get-job-reviewer-messages"
)
computation_api.add_resource(
    JobReviewerReportGetAPI, "/get-job-reviewer-report"
)
computation_api.add_resource(
    AgentSessionCreateAPI, "/create-agent-session"
)
computation_api.add_resource(
    AgentSessionQueryByNodeAPI, "/query-agent-sessions-by-node"
)
computation_api.add_resource(
    AgentSessionQueryByComputationAPI, "/query-agent-sessions-by-computation"
)
computation_api.add_resource(
    ProgrammingAgentMessagesUploadAPI, "/upload-programming-agent-messages"
)
computation_api.add_resource(
    ProgrammingAgentMessagesGetAPI, "/get-programming-agent-messages"
)
computation_api.add_resource(
    VisualizerAgentMessagesUploadAPI, "/upload-visualizer-agent-messages"
)
computation_api.add_resource(
    VisualizerAgentMessagesGetAPI, "/get-visualizer-agent-messages"
)

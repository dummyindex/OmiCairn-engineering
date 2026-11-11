from flask import Blueprint, request
from flask_restful import Api, Resource
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from service.computation import computation_service
from service.dynamic_generation import dynamic_generation_service
from service.task import task_service
from log.logger_factory import LoggerFactory
from constants.authority import AuthorityCarrier
from constants.common import GenerationMode
from tool.computation_launcher import ComputationLauncher
from authority.guardian_factory import AuthorityGuardianFactory
from tool.performance_timer import timer_stage, log_timings
from db import alchemy_db as db

logger = LoggerFactory.get_logger("DynamicGenerationController")


class DynamicGenerationPlanGenerateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        timings = {}

        with timer_stage("W2_auth_validation", timings):
            request_auditor.request_json_check(request, [
                "previous_node_id",
                "max_node",
                "max_branch",
                "user_request",
                "computation_resource_configure"
            ])
            post_data = request.get_json()
            previous_node_id = post_data.get("previous_node_id")
            max_node = post_data.get("max_node")
            max_branch = post_data.get("max_branch")
            user_request = post_data.get("user_request")
            computation_resource_configure = post_data.get(
                "computation_resource_configure")
            generation_mode = post_data.get(
                "generation_mode", GenerationMode.MIXED.value)
            max_debug = post_data.get("max_debug", 5)
            llm_model = post_data.get("llm_model", None)
            version = post_data.get("version", None)
            replan_count_limit = post_data.get("replan_count_limit", None)
            file_list = post_data.get("file_list", [])
            claude_execution_model = post_data.get("claude_execution_model", None)
            claude_max_iterations = post_data.get("claude_max_iterations", 100)

            guardian = AuthorityGuardianFactory.get_authority_guardian(
                AuthorityCarrier.NODE.value)
            guardian.check_authority(previous_node_id, check_writable=True)
            user_id = guardian.get_user_id()

        with timer_stage("W3_W6_service_call", timings):
            plan_result = dynamic_generation_service.generate_initial_plan(
                user_id=user_id,
                previous_node_id=previous_node_id,
                max_node=max_node,
                max_branch=max_branch,
                user_request=user_request,
                computation_resource_configure=computation_resource_configure,
                generation_mode=generation_mode,
                max_debug=max_debug,
                llm_model=llm_model,
                version=version,
                replan_count_limit=replan_count_limit,
                file_list=file_list,
                claude_execution_model=claude_execution_model,
                claude_max_iterations=claude_max_iterations
            )

        log_timings("W1_generate_plan_api", timings)

        if plan_result and isinstance(plan_result, dict):
            plan_result['_worker_timing'] = timings

        return ResponseManager.new_success_response(data=plan_result)


class DynamicGenerationPlanGetAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "previous_node_id",
            "generation_id"
        ])
        previous_node_id = request.args.get("previous_node_id")
        generation_id = request.args.get("generation_id")
        plan_result = dynamic_generation_service.get_plan(
            previous_node_id, generation_id)
        
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(previous_node_id, check_writable=False)

        if plan_result is None:
            return ResponseManager.new_bad_request_response("Plan not found or not generated yet")

        return ResponseManager.new_success_response(data=plan_result)


class DynamicGenerationPlanUpdateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def put(self):
        request_auditor.request_json_check(request, [
            "previous_node_id",
            "generation_id"
        ])
        post_data = request.get_json()
        previous_node_id = post_data.get("previous_node_id")
        generation_id = post_data.get("generation_id")

        attrs = {k: v for k, v in post_data.items()
                 if k not in ["previous_node_id", "generation_id"]}

        updated_plan = dynamic_generation_service.update_plan(
            previous_node_id, generation_id, attrs)

        if updated_plan is None:
            return ResponseManager.new_bad_request_response("Plan not found or cannot be modified")

        return ResponseManager.new_success_response(data=updated_plan)
    

class DynamicGenerationPlanStoreAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "previous_node_id",
            "generation_id",
            "plan_data"
        ])
        post_data = request.get_json()
        previous_node_id = post_data.get("previous_node_id")
        generation_id = post_data.get("generation_id")
        plan_data = post_data.get("plan_data")

        dynamic_generation_service.store_plan(
            previous_node_id, generation_id, plan_data)

        return ResponseManager.new_success_response()


class DynamicGenerationPlanListAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "analysis_id"
        ])
        analysis_id = request.args.get("analysis_id")
        plans = dynamic_generation_service.list_plans_by_analysis_id(
            analysis_id)

        return ResponseManager.new_success_response(data=plans)


class DynamicGenerationPlanDeleteAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def delete(self):
        request_auditor.request_args_check(request, [
            "generation_id",
            "previous_node_id"
        ])
        generation_id = request.args.get("generation_id")
        previous_node_id = request.args.get("previous_node_id")

        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(previous_node_id, check_writable=True)

        result = dynamic_generation_service.delete_plan(generation_id, previous_node_id)

        if "error" in result:
            if result.get("code") == 404:
                return ResponseManager.new_bad_request_response(result["error"])
            elif result.get("code") == 400:
                return ResponseManager.new_bad_request_response(result["error"])
            else:
                return ResponseManager.new_server_error_response(result["error"])

        return ResponseManager.new_success_response(data=result)


class DynamicGenerationCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "previous_node_id",
            "max_node",
            "max_branch",
            "user_request",
            "computation_resource_configure"
        ])
        post_data = request.get_json()
        previous_node_id = post_data.get("previous_node_id")
        max_node = post_data.get("max_node")
        max_branch = post_data.get("max_branch")
        user_request = post_data.get("user_request")
        computation_resource_configure = post_data.get(
            "computation_resource_configure")
        generation_mode = post_data.get(
            "generation_mode", GenerationMode.MIXED.value)
        max_debug = post_data.get("max_debug", 5)
        llm_model = post_data.get("llm_model", None)
        version = post_data.get("version", "v2")
        replan_count_limit = post_data.get("replan_count_limit", None)
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(previous_node_id, check_writable=True)
        dynamic_generation, first_branch = dynamic_generation_service.create(
            previous_node_id,
            max_node,
            max_branch,
            user_request,
            computation_resource_configure,
            generation_mode,
            max_debug,
            llm_model,
            version,
            replan_count_limit
        )

        return ResponseManager.new_success_response(data=dynamic_generation.to_dict())


class DynamicGenerationCreateWithPlanAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "dynamic_generation_id",
            "previous_node_id",
        ])
        post_data = request.get_json()
        dynamic_generation_id = post_data.get("dynamic_generation_id")
        previous_node_id = post_data.get("previous_node_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(previous_node_id, check_writable=True)
        dynamic_generation_service.create_with_plan(
            dynamic_generation_id,
            previous_node_id
        )
        return ResponseManager.new_success_response()


class FileUploadInfoGetAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "dynamic_generation_id",
            "file_name"
        ])
        dynamic_generation_id = request.args.get("dynamic_generation_id")
        file_name = request.args.get("file_name")
        file_upload_info = dynamic_generation_service.get_file_upload_info(
            dynamic_generation_id,
            file_name
        )
        return ResponseManager.new_success_response(
            file_upload_info
        )


class FileUploadConfirmAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "dynamic_generation_id",
            "file_name"
        ])
        post_data = request.get_json()
        dynamic_generation_id = post_data.get("dynamic_generation_id")
        file_name = post_data.get("file_name")
        dynamic_generation_service.confirm_file_upload(
            dynamic_generation_id,
            file_name
        )
        return ResponseManager.new_success_response()


class DynamicGenerationLaunchAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "dynamic_generation_id"
        ])
        dynamic_generation_id = request.args.get("dynamic_generation_id")
        dynamic_generation = dynamic_generation_service.get_by_id(
            dynamic_generation_id)
        if dynamic_generation is None:
            return ResponseManager.new_bad_request_response(
                "dynamic generation not found")
        dynamic_generation_service.upload_files_to_llm_server(
            dynamic_generation_id)
        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.NODE.value)
        guardian.check_authority(dynamic_generation.previous_node_id, check_writable=True)
        user_id = guardian.get_user_id()
        branches = dynamic_generation_service.get_generation_branch_list_by_generation_id(
            dynamic_generation.generation_id)
        # NOTE: len(branches) should be 1 at this point
        if len(branches) != 1:
            return ResponseManager.new_server_error_response(
                "Dynamic generation branches should be 1 at this point, but got {}".format(len(branches)))
        first_branch = branches[0]
        ComputationLauncher.launch_dynamic_generation(
            dynamic_generation,
            first_branch,
            user_id
        )
        return ResponseManager.new_success_response(data=first_branch.to_dict())


class DynamicGenerationLaunchWithPlanAPI(Resource):
    @exception_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "dynamic_generation_id"
        ])
        dynamic_generation_id = request.args.get("dynamic_generation_id")
        dynamic_generation = dynamic_generation_service.get_by_id(
            dynamic_generation_id)
        if dynamic_generation is None:
            return ResponseManager.new_bad_request_response(
                "dynamic generation not found")
        # dynamic_generation_service.upload_files_to_llm_server(
        #     dynamic_generation_id)
        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.NODE.value)
        guardian.check_authority(dynamic_generation.previous_node_id, check_writable=True)
        user_id = guardian.get_user_id()
        branches = dynamic_generation_service.get_generation_branch_list_by_generation_id(
            dynamic_generation.generation_id)
        if len(branches) != 1:
            return ResponseManager.new_server_error_response(
                "Dynamic generation branches should be 1 at this point, but got {}".format(len(branches)))
        first_branch = branches[0]
        ComputationLauncher.launch_dynamic_generation_with_plan(
            dynamic_generation.previous_node_id,
            dynamic_generation,
            first_branch,
            user_id
        )
        return ResponseManager.new_success_response(data=first_branch.to_dict())


class DynamicGenerationLaunchWithClaudeCodeAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """
        Launch Claude Code execution for a dynamic generation plan.
        This endpoint creates a Claude Code node, then dispatches the task for execution.
        """
        request_auditor.request_json_check(request, [
            "dynamic_generation_id",
            "previous_node_id",
        ])
        post_data = request.get_json()
        dynamic_generation_id = post_data.get("dynamic_generation_id")
        previous_node_id = post_data.get("previous_node_id")

        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.NODE.value
        )
        guardian.check_authority(previous_node_id, check_writable=True)
        user_id = guardian.get_user_id()
        
        result = dynamic_generation_service.launch_with_claude_code(
            dynamic_generation_id,
            previous_node_id,
            user_id
        )

        return ResponseManager.new_success_response(data=result)


class DynamicGenerationListByAnalysisAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "analysis_id"
        ])
        analysis_id = request.args.get("analysis_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.NODE.value)
        guardian.check_authority(analysis_id, check_writable=False)
        result = dynamic_generation_service.list_by_analysis_id(analysis_id)
        return ResponseManager.new_success_response(data=result)

class DynamicGenerationBranchCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "dynamic_generation_id",
            "end_node_id",
        ])
        dynamic_generation_id = request.args.get("dynamic_generation_id")
        end_node_id = request.args.get("end_node_id")
        new_branch = dynamic_generation_service.create_branch(
            dynamic_generation_id,
            end_node_id
        )
        if new_branch is None:
            return ResponseManager.new_bad_request_response(
                "Failed to create new branch"
            )
        return ResponseManager.new_success_response(data=new_branch.to_dict())

class DynamicGenerationBranchDoneReportAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        request_auditor.request_args_check(request, [
            "dynamic_generation_branch_id"
        ])
        dynamic_generation_branch_id = request.args.get(
            "dynamic_generation_branch_id")
        dynamic_generation_service.handle_branch_done(
            dynamic_generation_branch_id
        )
        return ResponseManager.new_success_response()


class DynamicGenerationNodeListAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "dynamic_generation_id"
        ])
        dynamic_generation_id = request.args.get("dynamic_generation_id")
        result = dynamic_generation_service.list_nodes(dynamic_generation_id)
        return ResponseManager.new_success_response(data=result)


class DynamicGenerationLogAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "dynamic_generation_id"
        ])
        dynamic_generation_id = request.args.get("dynamic_generation_id")
        previous_node_id = request.args.get("previous_node_id", None)
        node_id = request.args.get("node_id", None)
        if previous_node_id is not None:
            result = dynamic_generation_service.get_log_by_previous_node_id(
                dynamic_generation_id, previous_node_id)
        elif node_id is not None:
            result = dynamic_generation_service.get_log_by_node_id(
                dynamic_generation_id, node_id)
        else:
            result = dynamic_generation_service.get_log(dynamic_generation_id)
        return ResponseManager.new_success_response(data=result)


class DynamicGenerationSessionRecordAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "session"
        ])
        post_data = request.get_json()
        session = post_data.get("session")
        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.NODE.value)
        user_id = guardian.get_user_id()
        recorded_session = dynamic_generation_service.record_session(
            session, user_id)
        return ResponseManager.new_success_response(data=recorded_session.to_dict())


class DynamicGenerationSessionListAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "dynamic_generation_id"
        ])
        dynamic_generation_id = request.args.get("dynamic_generation_id")
        sessions = dynamic_generation_service.list_sessions(
            dynamic_generation_id)
        return ResponseManager.new_success_response(data=sessions)


class SessionNodesListAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "dynamic_generation_session_id"
        ])
        dynamic_generation_session_id = request.args.get(
            "dynamic_generation_session_id")
        nodes = dynamic_generation_service.list_nodes_by_session_id(
            dynamic_generation_session_id)
        return ResponseManager.new_success_response(data=nodes)

class DynamicGenerationContinueAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(request, [
            "dynamic_generation_id",
            "node_id"
        ])
        dynamic_generation_id = request.args.get("dynamic_generation_id")
        node_id = request.args.get("node_id")

        result = dynamic_generation_service.continue_generation(
            dynamic_generation_id,
            node_id
        )

        if result:
            return ResponseManager.new_success_response(data=result)
        else:
            return ResponseManager.new_bad_request_response(
                "Failed to continue dynamic generation"
            )


class DynamicGenerationGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "dynamic_generation_id"
        ])
        dynamic_generation_id = request.args.get("dynamic_generation_id")
        
        dynamic_generation = dynamic_generation_service.get_by_id(
            dynamic_generation_id)
        
        if dynamic_generation is None:
            return ResponseManager.new_bad_request_response(
                "Dynamic generation not found")
        
        return ResponseManager.new_success_response(data=dynamic_generation.to_dict())


class DynamicGenerationFixStuckStatesAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """Repair a stuck dynamic_generation state"""
        # This API needs no special permission check; basic access is sufficient
        result = dynamic_generation_service.fix_stuck_generation_states()

        if "error" in result:
            return ResponseManager.new_server_error_response(result["message"])
        else:
            return ResponseManager.new_success_response(data=result)


class DynamicGenerationInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        """Get dynamic generation information"""
        request_auditor.request_args_check(request, ["dynamic_generation_id"])
        dynamic_generation_id = request.args.get("dynamic_generation_id")

        info = dynamic_generation_service.get_info(dynamic_generation_id)

        if info:
            return ResponseManager.new_success_response(data=info)
        else:
            return ResponseManager.new_bad_request_response("Dynamic generation not found")


class DynamicGenerationInfoUpdateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        """Update dynamic generation information"""
        request_auditor.request_json_check(request, ["dynamic_generation_id", "updated_attrs"])
        post_data = request.get_json()
        dynamic_generation_id = post_data.get("dynamic_generation_id")
        updated_attrs = post_data.get("updated_attrs")

        success = dynamic_generation_service.update_info(dynamic_generation_id, updated_attrs)

        if success:
            return ResponseManager.new_success_response()
        else:
            return ResponseManager.new_bad_request_response("Failed to update dynamic generation")


class DynamicGenerationCustomPlanAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "previous_node_id",
            "max_node",
            "max_branch",
            "user_request",
            "computation_resource_configure",
            "plan_name",
            "plan_steps"
        ])
        post_data = request.get_json()
        previous_node_id = post_data.get("previous_node_id")
        max_node = post_data.get("max_node")
        max_branch = post_data.get("max_branch")
        user_request = post_data.get("user_request")
        computation_resource_configure = post_data.get("computation_resource_configure")
        generation_mode = post_data.get("generation_mode", GenerationMode.MIXED.value)
        max_debug = post_data.get("max_debug", 5)
        llm_model = post_data.get("llm_model", None)
        version = post_data.get("version", None)
        replan_count_limit = post_data.get("replan_count_limit", None)
        plan_name = post_data.get("plan_name")
        plan_steps = post_data.get("plan_steps")
        claude_execution_model = post_data.get("claude_execution_model", None)
        claude_max_iterations = post_data.get("claude_max_iterations", 100)

        guardian = AuthorityGuardianFactory.get_authority_guardian(
            AuthorityCarrier.NODE.value)
        guardian.check_authority(previous_node_id, check_writable=True)
        user_id = guardian.get_user_id()

        result = dynamic_generation_service.create_custom_plan(
            user_id=user_id,
            previous_node_id=previous_node_id,
            max_node=max_node,
            max_branch=max_branch,
            user_request=user_request,
            computation_resource_configure=computation_resource_configure,
            generation_mode=generation_mode,
            max_debug=max_debug,
            llm_model=llm_model,
            version=version,
            replan_count_limit=replan_count_limit,
            plan_name=plan_name,
            plan_steps=plan_steps,
            claude_execution_model=claude_execution_model,
            claude_max_iterations=claude_max_iterations
        )

        return ResponseManager.new_success_response(data=result)


dg_bp = Blueprint("dynamic_generation", __name__)
dynamic_generation_api = Api(dg_bp, "/dynamic-generation")
dynamic_generation_api.add_resource(DynamicGenerationCreateAPI, "/create")
dynamic_generation_api.add_resource(
    DynamicGenerationCreateWithPlanAPI, "/create-with-plan")
dynamic_generation_api.add_resource(
    FileUploadInfoGetAPI, "/get-file-upload-info")
dynamic_generation_api.add_resource(DynamicGenerationLaunchAPI, "/launch")
dynamic_generation_api.add_resource(
    DynamicGenerationLaunchWithPlanAPI, "/launch-with-plan")
dynamic_generation_api.add_resource(
    DynamicGenerationLaunchWithClaudeCodeAPI, "/launch-with-claude-code")
dynamic_generation_api.add_resource(
    DynamicGenerationListByAnalysisAPI, "/list-by-analysis")
dynamic_generation_api.add_resource(
    DynamicGenerationBranchCreateAPI, "/create-branch")
dynamic_generation_api.add_resource(
    DynamicGenerationBranchDoneReportAPI, "/branch-done-report")
dynamic_generation_api.add_resource(
    DynamicGenerationNodeListAPI, "/list-nodes")
dynamic_generation_api.add_resource(DynamicGenerationLogAPI, "/get-log")
dynamic_generation_api.add_resource(
    DynamicGenerationPlanGenerateAPI, "/generate-plan")
dynamic_generation_api.add_resource(DynamicGenerationPlanGetAPI, "/get-plan")
dynamic_generation_api.add_resource(
    DynamicGenerationPlanUpdateAPI, "/update-plan")
dynamic_generation_api.add_resource(
    DynamicGenerationPlanStoreAPI, "/store-plan")
dynamic_generation_api.add_resource(
    DynamicGenerationPlanListAPI, "/list-plans")
dynamic_generation_api.add_resource(
    DynamicGenerationPlanDeleteAPI, "/delete-plan")
dynamic_generation_api.add_resource(
    DynamicGenerationSessionRecordAPI, "/record-session"
)
dynamic_generation_api.add_resource(
    DynamicGenerationSessionListAPI, "/list-sessions"
)
dynamic_generation_api.add_resource(
    SessionNodesListAPI, "/list-nodes-by-session"
)
dynamic_generation_api.add_resource(
    DynamicGenerationContinueAPI, "/continue"
)
dynamic_generation_api.add_resource(
    DynamicGenerationGetAPI, "/get"
)
dynamic_generation_api.add_resource(
    DynamicGenerationFixStuckStatesAPI, "/fix-stuck-states"
)
dynamic_generation_api.add_resource(
    DynamicGenerationInfoGetAPI, "/get-info"
)
dynamic_generation_api.add_resource(
    DynamicGenerationInfoUpdateAPI, "/update-info"
)
dynamic_generation_api.add_resource(
    DynamicGenerationCustomPlanAPI, "/create-custom-plan"
)
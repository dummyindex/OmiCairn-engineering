from flask import Blueprint, request
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from constants.authority import AuthorityCarrier, SpecialUserId
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from service.analysis import analysis_service
from wrapper.exception import exception_wrapper
from exception.request.parameter_invalid import ParameterInvalidException
from exception.authority.no_authority import NoAuthorityException
from exception.authority.token_invalid import TokenInvalidException
from dao.collaboration_invitation import collaboration_invitation_dao


def _require_login(guardian):
    user_id = guardian.get_user_id()
    if user_id is None:
        raise TokenInvalidException()
    return user_id


def _get_invitation_or_raise(invitation_id):
    invitation = collaboration_invitation_dao.find_by_id(invitation_id)
    if invitation is None:
        raise ParameterInvalidException("invitation_id is invalid")
    return invitation

class PublicAnalysisInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["analysis_id"])
        analysis_id = request.args.get("analysis_id", None)
        result = analysis_service.get_info(
            analysis_id
        )
        return ResponseManager.new_success_response(data=result)

class AnalysisInfoGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        request_auditor.request_args_check(request, ["analysis_id"])
        analysis_id = request.args.get("analysis_id", None)
        guardian.check_authority(analysis_id)
        result = analysis_service.get_info(
            analysis_id
        )
        return ResponseManager.new_success_response(data=result)

class PublicAnalysisListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        result = analysis_service.get_info_list(
            SpecialUserId.PUBLIC.value
        )
        return ResponseManager.new_success_response(data=result)

class AnalysisListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        user_id = guardian.get_user_id()
        result = analysis_service.get_info_list(
            user_id,
            add_latest_visit_time=True
        )
        return ResponseManager.new_success_response(data=result)


class AnalysisCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        user_id = _require_login(guardian)
        name = request.form.get("name", None)
        description = request.form.get("description", None)
        password = request.form.get("password", None)
        creation_source = request.form.get("creation_source", None)
        result = analysis_service.create(
            user_id,
            name,
            description,
            password,
            creation_source
        )
        return ResponseManager.new_success_response(data=result)

class AnalysisValidateAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "analysis_id"
        ])
        analysis_id = request.args.get("analysis_id")
        password = request.args.get("password", None)
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_authority(analysis_id)
        result = analysis_service.validate_password(analysis_id, password)
        return ResponseManager.new_success_response(result)

class DataImportAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "data_ids",
            "analysis_id"
        ])
        post_data = request.get_json()
        data_ids = post_data.get("data_ids")
        analysis_id = post_data.get("analysis_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_authority(analysis_id, check_writable=True)
        analysis_service.import_data_batch(analysis_id, data_ids)
        return ResponseManager.new_success_response()

class DataUnimportAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def delete(self):
        request_auditor.request_args_check(request, [
            "data_id",
            "analysis_id"
        ])
        data_id = request.args.get("data_id")
        analysis_id = request.args.get("analysis_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_authority(analysis_id, check_writable=True)
        analysis_service.remove_data_from_imported_list(analysis_id, data_id)
        return ResponseManager.new_success_response()

class CopyAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "analysis_id",
            "name"
        ])
        post_data = request.get_json()
        analysis_id = post_data.get("analysis_id")
        name = post_data.get("name")
        description = post_data.get("description", None)
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_authority(analysis_id)
        user_id = _require_login(guardian)
        result = analysis_service.copy(
            analysis_id,
            name,
            description,
            user_id
        )
        return ResponseManager.new_success_response(data=result)

class EditAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(
        request,
        ['analysis_id']
        )
        analysis_id = request.args.get('analysis_id', None)
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_authority(analysis_id, check_writable=True)
        
        post_data = request.get_json()
        
        analysis_service.edit_analyisis(analysis_id, post_data)
        
        # return response may different when handling different API
        return ResponseManager.new_success_response()
        
class DeleteAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def delete(self):
        request_auditor.request_args_check(request, [
            "analysis_id"
        ])
        analysis_id = request.args.get("analysis_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_ownership(analysis_id)
        analysis_service.delete(analysis_id)
        return ResponseManager.new_success_response()

class SharingForAllToggleAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_args_check(request,[
            "analysis_id",
            "share_to_all"
        ])
        analysis_id = request.args.get("analysis_id")
        share_to_all = int(request.args.get("share_to_all"))
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_ownership(analysis_id)
        user_relation_list = guardian.get_user_relations(analysis_id)
        already_shared = False
        for user_relation in user_relation_list:
            if user_relation.user_id == SpecialUserId.ALL.value:
                already_shared = True
                break
        if share_to_all == 0 and already_shared:
            guardian.cancel_share_to_all(analysis_id)
        if share_to_all == 1 and not already_shared:
            guardian.share_to_all(analysis_id)
        return ResponseManager.new_success_response()
    
class PermissionChangeAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        invitation_id = request.args.get("invitation_id", None)
        analysis_id = request.args.get("analysis_id", None)
        receiver_id = request.args.get("receiver_id", None)
        if invitation_id is not None:
            permission = request.args.get("permission", None)
            invitation = _get_invitation_or_raise(invitation_id)
            guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
            guardian.check_ownership(invitation.oid)
            result = analysis_service.change_user_permission_by_invitation_id(invitation_id, permission)
            return ResponseManager.new_success_response(data=result)
        if analysis_id is not None and receiver_id is not None:
            # TODO: may later need to modify permissions via analysis_id and receiver_id
            return ResponseManager.new_success_response()
        raise ParameterInvalidException(
            "invitation_id or analysis_id and receiver_id must be provided."
        )
        

class AuthorityGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "analysis_id"
        ])
        analysis_id = request.args.get("analysis_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_authority(analysis_id)
        user_relation_list = guardian.get_user_relations(analysis_id)
        return ResponseManager.new_success_response(data=user_relation_list)
    
class CollaboratorInviteAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        request_auditor.request_json_check(request, [
            "analysis_id",
            "receiver_id_list",
            "permission"
        ])
        post_data = request.get_json()
        analysis_id = post_data.get("analysis_id")
        receiver_id_list = post_data.get("receiver_id_list")
        permission = post_data.get("permission")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_ownership(analysis_id)
        user_id = guardian.get_user_id()
        result = analysis_service.invite_collaborator(analysis_id, user_id, receiver_id_list, permission)
        return ResponseManager.new_success_response(data=result)
    
class CollaborationCancellAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "invitation_id"
        ])
        invitation_id = request.args.get("invitation_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        user_id = _require_login(guardian)
        invitation = _get_invitation_or_raise(invitation_id)
        if str(invitation.invitee_id) != str(user_id):
            guardian.check_ownership(invitation.oid)
        result = analysis_service.cancel_collaboration(invitation_id)
        return ResponseManager.new_success_response(data=result)
    
class CollaborationListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "analysis_id"
        ])
        analysis_id = request.args.get("analysis_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_authority(analysis_id)
        user_id = guardian.get_user_id()
        result = analysis_service.get_collaboration_list(analysis_id, user_id)
        return ResponseManager.new_success_response(data=result)
    
class InvitationListGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = _require_login(guardian)
        offset = request.args.get("offset", 0)
        limit = request.args.get("limit", 20)
        result = analysis_service.get_invitation_list(user_id, offset, limit)
        return ResponseManager.new_success_response(data=result)
    
class InvitationAcceptAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "invitation_id"
        ])
        invitation_id = request.args.get("invitation_id")
        user_id = _require_login(AuthorityGuardianFactory.get_authority_guardian())
        invitation = _get_invitation_or_raise(invitation_id)
        if str(invitation.invitee_id) != str(user_id):
            raise NoAuthorityException("This invitation was not sent to you.")
        result = analysis_service.accept_invitation(invitation_id)
        return ResponseManager.new_success_response(data=result)
    
class InvitationRejectAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "invitation_id"
        ])
        invitation_id = request.args.get("invitation_id")
        user_id = _require_login(AuthorityGuardianFactory.get_authority_guardian())
        invitation = _get_invitation_or_raise(invitation_id)
        if str(invitation.invitee_id) != str(user_id):
            raise NoAuthorityException("This invitation was not sent to you.")
        result = analysis_service.reject_invitation(invitation_id)
        return ResponseManager.new_success_response(data=result)

class UpdatedRecordGetAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "analysis_id"
        ])
        analysis_id = request.args.get("analysis_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_authority(analysis_id)
        result = analysis_service.get_updated_record(analysis_id)
        return ResponseManager.new_success_response(data=result)
    
class ExportWithoutDataAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "analysis_id"
        ])
        analysis_id = request.args.get("analysis_id")
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_authority(analysis_id)
        result = analysis_service.export_without_data(analysis_id)
        return ResponseManager.new_success_response(data=result)
    
class ImportAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = _require_login(guardian)
        request_auditor.request_json_check(request, [
            "analysis_structure"
        ])
        post_data = request.get_json()
        analysis_structure = post_data.get("analysis_structure")
        analysis_service.tie_in(analysis_structure, user_id)
        return ResponseManager.new_success_response()

class TotalComputationTimeAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, ["analysis_id"])
        analysis_id = request.args.get('analysis_id')
        guardian = AuthorityGuardianFactory.get_authority_guardian(AuthorityCarrier.ANALYSIS.value)
        guardian.check_authority(analysis_id)
        total_duration = analysis_service.calculate_total_duration(analysis_id)
        return ResponseManager.new_success_response(data={"total_duration": total_duration})
    
analysis_bp = Blueprint("analysis", __name__)
analysis_api = Api(analysis_bp, prefix="/analysis")
analysis_api.add_resource(PublicAnalysisInfoGetAPI, "/public/get-info")
analysis_api.add_resource(AnalysisInfoGetAPI, "/get-info")
analysis_api.add_resource(PublicAnalysisListGetAPI, "/public/get-list")
analysis_api.add_resource(AnalysisListGetAPI, "/get-list")
analysis_api.add_resource(AnalysisCreateAPI, "/create")
analysis_api.add_resource(AnalysisValidateAPI, "/validate")
analysis_api.add_resource(DataImportAPI, "/data/import")
analysis_api.add_resource(DataUnimportAPI, "/data/unimport")
analysis_api.add_resource(CopyAPI, "/copy")
analysis_api.add_resource(EditAPI, "/edit")
analysis_api.add_resource(DeleteAPI, "/delete")
analysis_api.add_resource(SharingForAllToggleAPI, "/toggle-sharing-for-all")
analysis_api.add_resource(PermissionChangeAPI, "/change-permission")
analysis_api.add_resource(AuthorityGetAPI, "/get-authority")
analysis_api.add_resource(CollaboratorInviteAPI, "/invite-collaborator")
analysis_api.add_resource(CollaborationCancellAPI, "/cancel-collaboration")
analysis_api.add_resource(CollaborationListGetAPI, "/get-collaboration-list")
analysis_api.add_resource(InvitationListGetAPI, "/get-invitation-list")
analysis_api.add_resource(InvitationAcceptAPI, "/accept-invitation")
analysis_api.add_resource(InvitationRejectAPI, "/reject-invitation")
analysis_api.add_resource(UpdatedRecordGetAPI, "/get-updated-record")
analysis_api.add_resource(ExportWithoutDataAPI, "/export-without-data")
analysis_api.add_resource(ImportAPI, "/import")
analysis_api.add_resource(TotalComputationTimeAPI, '/total-computation-time')


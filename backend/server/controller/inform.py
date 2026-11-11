from service.inform import inform_service
from flask import Blueprint, request
from flask_restful import Api, Resource
from authority.guardian_factory import AuthorityGuardianFactory
from wrapper.db_session import transaction_wrapper
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from authority.admin import require_administrator

class AnnouncementCreateAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        user_id = require_administrator()
        request_auditor.request_json_check(
            request,
            [
                "content",
                "title"
            ]
        )
        post_data = request.get_json()
        content = post_data["content"]
        title = post_data["title"]
        announcement = inform_service.create_announcement(user_id, title, content)
        return ResponseManager.new_success_response(announcement)

class AnnouncementReadAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        request_auditor.request_args_check(
            request,
            [
                "announcement_id"
            ]
        )
        announcement_id = request.args.get("announcement_id")
        inform_service.read_announcement(user_id, announcement_id)
        return ResponseManager.new_success_response()

class AnnouncementListAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        offset = int(request.args.get("offset", 0))
        limit = int(request.args.get("limit", 10))
        announcement_list = inform_service.get_announcement_list(user_id, offset, limit)
        return ResponseManager.new_success_response(announcement_list)

class AnnouncementUnreadListAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        unread_announcements = inform_service.get_unread_announcements_by_user_id(user_id)
        return ResponseManager.new_success_response(unread_announcements)

class AnnouncementDetailAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            [
                "announcement_id"
            ]
        )
        announcement_id = request.args.get("announcement_id")
        announcement = inform_service.get_announcement_detail(announcement_id)
        return ResponseManager.new_success_response(announcement)

class InformListAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        offset = int(request.args.get("offset", 0))
        limit = int(request.args.get("limit", 20))
        inform_type = request.args.get("inform_type", None)
        inform_list = inform_service.get_inform_history_by_receiver_id(user_id, inform_type,offset, limit)
        return ResponseManager.new_success_response(inform_list)

class InformUnreadListAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(request, [
            "offset",
            "limit"
        ])
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        offset = int(request.args.get("offset"))
        limit = int(request.args.get("limit"))
        unread_informs, total = inform_service.get_unread_informs_by_user_id(user_id, offset, limit)
        return ResponseManager.new_success_response(data={
            "unread_informs": unread_informs,
            "total": total
        })

class InformDetailAPI(Resource):
    @exception_wrapper
    def get(self):
        request_auditor.request_args_check(
            request,
            [
                "inform_id"
            ]
        )
        inform_id = request.args.get("inform_id")
        inform = inform_service.get_inform_detail(inform_id)
        return ResponseManager.new_success_response(inform)

class InformReadAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def post(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        request_auditor.request_json_check(
            request,
            [
                "inform_id_list"
            ]
        )
        post_data = request.get_json()
        inform_id_list = post_data["inform_id_list"]
        inform_service.read_informs(inform_id_list)
        return ResponseManager.new_success_response()

class InformCountGetAPI(Resource):
    @exception_wrapper
    def get(self):
        guardian = AuthorityGuardianFactory.get_authority_guardian()
        user_id = guardian.get_user_id()
        unread_inform_count = inform_service.get_inform_count(user_id)
        return ResponseManager.new_success_response(unread_inform_count)

inform_bp = Blueprint('inform', __name__)
inform_api = Api(inform_bp, prefix="/inform")
inform_api.add_resource(AnnouncementCreateAPI, "/create-announcement")
inform_api.add_resource(AnnouncementReadAPI, "/read-announcement")
inform_api.add_resource(AnnouncementListAPI, "/list-announcement")
inform_api.add_resource(AnnouncementUnreadListAPI, "/list-unread-announcement")
inform_api.add_resource(AnnouncementDetailAPI, "/get-announcement-detail")
inform_api.add_resource(InformListAPI, "/list-inform")
inform_api.add_resource(InformUnreadListAPI, "/list-unread-inform")
inform_api.add_resource(InformDetailAPI, "/get-inform-detail")
inform_api.add_resource(InformReadAPI, "/read-inform")
inform_api.add_resource(InformCountGetAPI, "/get-inform-count")

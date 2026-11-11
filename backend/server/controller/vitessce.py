from flask import Blueprint, request
from flask_restful import Api, Resource
from datetime import datetime
from authority.guardian_factory import AuthorityGuardianFactory
from tool.response_manager import ResponseManager
from tool.requests_auditor import request_auditor
from wrapper.exception import exception_wrapper
from service.vitessce import vitessce_service

class PresignedUrlGetAPI(Resource):
    @exception_wrapper
    def post(self):
        AuthorityGuardianFactory.get_authority_guardian().require_user_id()
        request_auditor.request_json_check(request, ['raw_url'])
        post_data = request.get_json()
        raw_url = post_data['raw_url']
        presigned_url = vitessce_service.prepare_presigned_url_from_raw_url(raw_url)
        return ResponseManager.new_success_response(presigned_url)

vitessce_bp = Blueprint('vitessce', __name__)
vitessce_api = Api(vitessce_bp, prefix='/vitessce')
vitessce_api.add_resource(PresignedUrlGetAPI, '/get-presigned-url')
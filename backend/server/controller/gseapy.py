from flask_restful import Resource, Api
from flask import (
    request,
    Blueprint
)
from tool.response_manager import ResponseManager
from service.gseapy import gseapy_service
from wrapper.exception import exception_wrapper
from wrapper.db_session import transaction_wrapper
from tool.requests_auditor import request_auditor
# from authority.guardian_factory import AuthorityGuardianFactory
from constants.gseapy import ORGANISM_LIST

class GetOrganismListGetAPI(Resource):
    def get(self):
        return ResponseManager.new_success_response(
            data=ORGANISM_LIST
        )


class LibraryNameListGetAPI(Resource):
    @exception_wrapper
    @transaction_wrapper
    def get(self):
        organism = request.args.get("organism", None)
        if organism is None:
            library_name_list = gseapy_service.whole_library_name_list_get()
        else:
            library_name_list = gseapy_service.library_name_list_get(organism)
        return ResponseManager.new_success_response(data=library_name_list)

gseapy_bp = Blueprint("gseapy", __name__)
gseapy_api = Api(gseapy_bp, prefix="/gseapy")
gseapy_api.add_resource(
    GetOrganismListGetAPI,
    "/organism/list/get"
)
gseapy_api.add_resource(
    LibraryNameListGetAPI,
    "/library/list/get"
)

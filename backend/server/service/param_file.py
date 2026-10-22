from dao.param_file import param_file_dao
from model.param_file import ParamFile
from sss.porter_factory import PorterFactory
from constants.sss import BUCKET_NAME
from tool.common_generator import CommonGenerator
from tool.common_analysist import CommonAnalysist
from datetime import datetime

class ParamFileService:
    def create_param_file(self, file_name: str, file_size: int, user_id) -> None:
        file_uuid = CommonGenerator.generate_uuid(True)
        content_type = CommonAnalysist.analysize_content_type(file_name)
        suffix = CommonAnalysist.analysis_file_suffix(file_name)
        object_key = f"param-file/{file_uuid}"
        created_time = datetime.now()
        param_file = ParamFile(
            uuid=file_uuid,
            user_id=user_id,
            name=file_name,
            size=file_size,
            suffix=suffix,
            content_type=content_type,
            object_key=object_key,
            bucket=BUCKET_NAME,
            created_time=created_time
        )
        param_file_dao.insert(param_file)
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        presigned_post = porter.get_presigned_post(file_size, 60 * 60)
        return {
            "paramFile": param_file,
            "presignedPost": presigned_post
        }
    
    def get_param_file_presigned_url(self, file_uuid: str) -> dict:
        param_file = param_file_dao.find_by_uuid(file_uuid)
        porter = PorterFactory.create_porter()
        porter.set_operation_target(param_file.object_key)
        presigned_url = porter.get_presigned_url(60 * 60)
        return presigned_url
    
    def get_param_file_info(self, file_uuid: str) -> dict:
        param_file = param_file_dao.find_by_uuid(file_uuid)
        return param_file
    
    def list_param_files_by_user(self, user_id: int, offset: int, limit: int, search_key: str) -> list:
        param_files = param_file_dao.find_by_user_id(user_id, limit, offset, search_key)
        return param_files
    
    def list_param_files_by_suffixes(self, suffixes: list, user_id: str | int) -> list:
        param_files = param_file_dao.find_by_suffixes(suffixes, user_id)
        return param_files

    def update_param_file(self, file_uuid: str, updated_attrs: dict) -> None:
        param_file_dao.update_by_uuid(file_uuid, updated_attrs)
    
    def delete_param_file(self, file_uuid: str) -> None:
        param_file = param_file_dao.find_by_uuid(file_uuid)
        porter = PorterFactory.create_porter()
        porter.remove_file(param_file.object_key)
        param_file_dao.delete_by_uuid(file_uuid)

param_file_service = ParamFileService()
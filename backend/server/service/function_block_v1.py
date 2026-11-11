from io import BytesIO
import zipfile
import os
import json
import tempfile
import shutil
from dao.function_block_v1 import function_block_v1_dao
from dao.function_block_group import function_block_group_dao
from model.function_block_v1 import FunctionBlockV1
from model.function_block_version_v1 import FunctionBlockVersionV1
from model.function_block_user_relation import FunctionBlockUserRelation
from model.function_block_group import FunctionBlockGroup
from model.function_block_collected import FunctionBlockCollected
from constants.function_block import FBOccasion, FunctionBlockVersionState
from model.function_block_group_user_relation import FunctionBlockGroupUserRelation
from tool.function_block import FunctionBlockTool
from sss.porter_factory import PorterFactory
from waiter.function_block_v1_waiter import FunctionBlockV1Waiter
from datetime import datetime
from dto.function_block_search_dto import FunctionBlockSearchDTO
from constants.authority import SpecialUserId
from constants.authority import Relation, Permission
from exception.request.parameter_invalid import ParameterInvalidException
from constants.function_block import FB_PP_QUEUE
from batch_job.aws import AWSBatchJob
from job_logs.aws_cloudwatch_taker import AWSCloudwatchLogsTaker
from log.logger_factory import logger_factory

logger = logger_factory.create_logger("function_block_v1_service")

class FunctionBlockV1Service:
    def get_group_list_by_owner_id(self, owner_id):
        return function_block_group_dao.find_by_user_id(owner_id)

    def create_group(self, owner_id, name, alt_name):
        now = datetime.now()
        groups = function_block_group_dao.find_by_user_id(owner_id)
        latest_serial_number = max([group.serial_number for group in groups], default=-1)
        serial_number = latest_serial_number + 1
        published = owner_id == SpecialUserId.PUBLIC.value
        if published:
            groups.sort(key=lambda g: g.id, reverse=True)
            group_with_max_id = groups[0] if len(groups) > 0 else None
            new_group_id = group_with_max_id.id + 1 if group_with_max_id is not None else 1
            new_group = FunctionBlockGroup(
                id=new_group_id,
                name=name,
                created_time=now,
                serial_number=serial_number,
                alt_name=alt_name
            )
        else:
            new_group = FunctionBlockGroup(
                name=name,
                created_time=now,
                serial_number=serial_number,
                alt_name=alt_name
            )
        function_block_group_dao.insert(new_group)
        new_user_relation = FunctionBlockGroupUserRelation(
            function_block_group_id=new_group.id,
            user_id=owner_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        function_block_group_dao.insert_user_relation(new_user_relation)
        return new_group

    def get_by_group_id(self, group_id):
        return function_block_v1_dao.find_by_group_id(group_id)
    

    def get_information(self, function_block_id):
        fb = function_block_v1_dao.find_by_id(function_block_id)
        fb_version_id = fb.current_version_id
        fb_version = function_block_v1_dao.find_version_by_id(fb_version_id)
        fb_json = fb.to_dict()
        fb_json["currentVersionInformation"] = fb_version.to_dict()
        return fb_json
    
    def get_version_information(self, function_block_version_id):
        fb_version = function_block_v1_dao.find_version_by_id(function_block_version_id)
        if fb_version is None:
            return None
        return fb_version.to_dict()

    def get_current_version(self, function_block_id) -> FunctionBlockVersionV1:
        fb = function_block_v1_dao.find_by_id(function_block_id)
        fb_version_id = fb.current_version_id
        if fb_version_id is None:
            return None
        return function_block_v1_dao.find_version_by_id(fb_version_id)

    def get_search(self, keyname, owner_id):

        search_results = function_block_v1_dao.get_function_blocks_with_keyname(keyname, owner_id)

        results = []

        for search_result in search_results:

            dto = FunctionBlockSearchDTO(
                fb_id=search_result.function_block_id,
                fb_name=search_result.function_block_name,
                fb_alt_name=search_result.function_block_alt_name,
                description=search_result.current_version_description,
                source=search_result.current_version_source
            )
            results.append(dto.to_dict())

        return results
    
    def get_updated_records(self, start_time, user_id):
        private_fb_id_list = function_block_v1_dao.find_id_list_by_user_id(user_id)
        public_fb_id_list = function_block_v1_dao.find_id_list_by_user_id(SpecialUserId.PUBLIC.value)
        private_updated_record = \
            function_block_v1_dao.find_updated_record_list_by_id_list_and_start_time(
                private_fb_id_list, 
                start_time
            )
        public_updated_record = \
            function_block_v1_dao.find_updated_record_list_by_id_list_and_start_time(
                public_fb_id_list, 
                start_time
            )
        return private_updated_record + public_updated_record

    def validate_creation_form(self, fb_type, first_version_name):
        error_list = []
        if fb_type not in [
            "computation"
        ]:
            error_list.append({
                "field": "fb_type",
                "reason": "fb_type should be one of [computation, ...]"
            })
        if first_version_name is None or first_version_name == "":
            error_list.append({
                "field": "first_version_name",
                "reason": "first_version_name should not be empty"
            })
        return error_list

    def create_function_block(self, user_id, group_id, name, alt_name, fb_type, first_version_name, occasion):
        now = datetime.now()
        published = SpecialUserId.PUBLIC.value == user_id
        if published:
            public_list = function_block_v1_dao.find_by_user_id(SpecialUserId.PUBLIC.value)
            previous_max_id = max([fb.id for fb in public_list])
            new_fb_id = previous_max_id + 1
            function_block = FunctionBlockV1(
                id=new_fb_id,
                group_id=group_id,
                name=name,
                alt_name=alt_name,
                type=fb_type,
                created_time=now,
                occasion=occasion
            )
        else:
            function_block = FunctionBlockV1(
                group_id=group_id,
                name=name,
                alt_name=alt_name,
                type=fb_type,
                created_time=now,
                occasion=occasion
            )
        function_block_v1_dao.insert(function_block)
        new_fb_user_relation = FunctionBlockUserRelation(
            function_block_id=function_block.id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        function_block_v1_dao.insert_user_relation(new_fb_user_relation)
        if published:
            all_published_fb_version_list = function_block_v1_dao.find_fb_version_by_user_id(SpecialUserId.PUBLIC.value)
            max_fb_version_id = -1
            for fb_v in all_published_fb_version_list:
                max_fb_version_id = fb_v.function_block_version_id if fb_v.function_block_version_id > max_fb_version_id else max_fb_version_id
            first_function_block_version = FunctionBlockVersionV1(
                id=max_fb_version_id + 1,
                name=first_version_name,
                function_block_id = function_block.id,
                created_time=now,
                state=FunctionBlockVersionState.UNUPLOAD.value
            )
        else:
            first_function_block_version = FunctionBlockVersionV1(
                function_block_id=function_block.id,
                name=first_version_name,
                created_time=now,
                state=FunctionBlockVersionState.UNUPLOAD.value
            )
        function_block_v1_dao.insert_new_version(first_function_block_version)
        return first_function_block_version

    def create_public_function_block(self, name, group_id, fb_type, first_version_name, occasion):
        now = datetime.now()
        fb_list = function_block_v1_dao.find_by_user_id(SpecialUserId.PUBLIC.value)
        max_id = 0
        max_version_id = 0
        for fb in fb_list:
            if fb.id > max_id:
                max_id = fb.id
            fb_version_list = function_block_v1_dao.find_version_by_function_block_id(fb.id)
            for fb_version in fb_version_list:
                if fb_version.id > max_version_id:
                    max_version_id = fb_version.id
        id = max_id + 1
        first_version_id = max_version_id + 1
        function_block = FunctionBlockV1(
            id=id,
            group_id=group_id,
            name=name,
            type=fb_type,
            created_time=now,
            occasion=occasion
        )
        function_block_v1_dao.insert(function_block)
        new_fb_user_relation = FunctionBlockUserRelation(
            function_block_id=function_block.id,
            user_id=SpecialUserId.PUBLIC.value,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        function_block_v1_dao.insert_user_relation(new_fb_user_relation)
        first_function_block_version = FunctionBlockVersionV1(
            id=first_version_id,
            function_block_id=function_block.id,
            name=first_version_name,
            created_time=now,
            state=FunctionBlockVersionState.UNUPLOAD.value
        )
        function_block_v1_dao.insert_new_version(first_function_block_version)
        return first_function_block_version
    
    def get_fb_version_by_name(self, function_block_id, version_name):
        return function_block_v1_dao.find_version_by_function_block_id_and_name(function_block_id, version_name)

    def get_raw_fb_zip_upload_info(self, function_block_version_id, file_size):
        fbv = function_block_v1_dao.find_version_by_id(function_block_version_id)
        waiter = FunctionBlockV1Waiter(function_block_version_id, fbv.program_language)
        return waiter.get_raw_fb_zip_upload_info(file_size)

    def validate_update_form(self, version_name, function_block_id, user_id):
        error_list = []
        if function_block_id is None or function_block_id == "":
            error_list.append({
                "field": "function_block_id",
                "reason": "function_block_id should not be empty"
            })
        else:
            function_block = function_block_v1_dao.find_by_id(function_block_id)
            if function_block is None:
                error_list.append({
                    "field": "function_block_id",
                    "reason": "function_block_id should be valid"
                })
        if version_name is None or version_name == "":
            error_list.append({
                "field": "version_name",
                "reason": "version_name should not be empty"
            })
        else:
            name_shared_version_list = function_block_v1_dao.find_version_by_function_block_id_and_name(
                function_block_id,
                version_name
            )
            if name_shared_version_list is not None:
                error_list.append({
                    "field": "version_name",
                    "reason": "version_name should be unique"
                })
        return error_list

    def create_function_block_version(self, function_block_id, first_version_name):
        fb_user_relation_list = function_block_v1_dao.find_user_relation_by_fb_id(function_block_id)
        published = False
        for user_relation in fb_user_relation_list:
            if user_relation.user_id == SpecialUserId.PUBLIC.value and user_relation.relation == Relation.BELONG_TO:
                published = True
        
        now = datetime.now()
        if published:
            all_published_fb_version_list = function_block_v1_dao.find_fb_version_by_user_id(SpecialUserId.PUBLIC.value)
            max_fb_version_id = -1
            for fb_v in all_published_fb_version_list:
                max_fb_version_id = fb_v.function_block_version_id if fb_v.function_block_version_id > max_fb_version_id else max_fb_version_id
            function_block_version = FunctionBlockVersionV1(
                id=max_fb_version_id + 1,
                name=first_version_name,
                function_block_id = function_block_id,
                created_time=now,
                state=FunctionBlockVersionState.UNUPLOAD.value
            )
        else:
            function_block_version = FunctionBlockVersionV1(
                name=first_version_name,
                function_block_id = function_block_id,
                created_time=now,
                state=FunctionBlockVersionState.UNUPLOAD.value
            )
        function_block_v1_dao.insert_new_version(function_block_version)
        return function_block_version

    def get_version_list(self, function_block_id):
        fb_v_list = function_block_v1_dao.find_version_by_function_block_id(function_block_id)
        return fb_v_list

    def switch_version(self, function_block_id, version_id):
        function_block = function_block_v1_dao.find_by_id(function_block_id)
        if function_block is None:
            return None
        function_block_version = function_block_v1_dao.find_version_by_id(version_id)
        if function_block_version is None:
            raise ParameterInvalidException("invalid function block version")
        function_block_v1_dao.update(function_block_id, {
            "current_version_id": version_id
        })
        return function_block_version

    def get_preprocess_logs(self, function_block_version_id):
        function_block_version = function_block_v1_dao.find_version_by_id(function_block_version_id)
        if function_block_version is None:
            raise ParameterInvalidException("invalid function block version")
        job_name = f"fb-preprocessor-{function_block_version_id}"
        batch_job = AWSBatchJob()
        job_list = batch_job.query_job_by_name(job_name, FB_PP_QUEUE)
        if len(job_list) == 0:
            return []
        job_id = job_list[0]['jobId']
        job_info = batch_job.describe_job(job_id)
        if job_info is None:
            return []
        log_stream_name = job_info['container']['logStreamName']
        cloudwatch_taker = AWSCloudwatchLogsTaker(
            group_name="/aws/batch/job",
            log_stream_name=log_stream_name
        )
        logs = cloudwatch_taker.get()
        return logs

    def get_preview_images_list(self, function_block_version_id = None, function_block_id = None):
        if function_block_version_id is None and function_block_id is None:
            raise ParameterInvalidException("function_block_version_id or function_block_id should be provided")
        if function_block_version_id is None:
            function_block = function_block_v1_dao.find_by_id(function_block_id)
            if function_block is None:
                raise ParameterInvalidException("invalid function block")
            function_block_version_id = function_block.current_version_id
        elif function_block_id is not None:
            logger.warning("function_block_id is ignored when function_block_version_id is provided")
        if function_block_version_id is None:
            raise ParameterInvalidException("invalid function block version")
        function_block_version = function_block_v1_dao.find_version_by_id(function_block_version_id)
        if function_block_version is None:
            raise ParameterInvalidException("invalid function block version")
        fb_waiter = FunctionBlockV1Waiter(function_block_version_id,function_block_version.program_language)
        return fb_waiter.fetch_preview_images_list()
    
    def get_mini_tool_function_blocks(self, offset, limit, search_key):
        return function_block_v1_dao.find_fb_by_user_id_and_occasion(SpecialUserId.PUBLIC.value, FBOccasion.MINI_TOOL.value , offset, limit, search_key)

    def get_collected_minitools_by_user_id(self, user_id, offset, limit, search_key = None):
        return function_block_v1_dao.find_collected_minitools_by_user_id(user_id, offset, limit, search_key)
    
    def check_collected_function_blocks(self, user_id, function_block_id_list):
        collected_fbs = function_block_v1_dao.find_list_collected(user_id, function_block_id_list)
        dict_collected_fbs = {
            int(id) : False for id in function_block_id_list
        }
        for fb in collected_fbs:
            dict_collected_fbs[fb.function_block_id] = True
        return dict_collected_fbs

    def collect_function_block(self, user_id, function_block_id):
        now = datetime.now()
        function_block = function_block_v1_dao.find_by_id(function_block_id)
        if function_block is None:
            raise ParameterInvalidException("invalid function block")
        is_collected = function_block_v1_dao.find_is_collected(user_id, function_block_id)
        if is_collected:
            raise ParameterInvalidException("function block already collected")
        collected = FunctionBlockCollected(
            function_block_id=function_block_id,
            user_id=user_id,
            created_time=now
        )
        function_block_v1_dao.insert_collected(collected)
        return collected
    
    def uncollect_function_block(self, user_id, function_block_id):
        function_block_v1_dao.delete_collected(user_id, function_block_id)
        return True
    
    def preprocess_function_block_version_directly(self, function_block_version_id):
        # update fb version record state to prehandling
        # execute_sql("UPDATE function_block_version_v1 SET state = 'prehandling' WHERE id = %s", (FB_VERSION_ID,))
        function_block_version = function_block_v1_dao.find_version_by_id(function_block_version_id)
        if function_block_version is None:
            raise ParameterInvalidException("invalid function block version")
        function_block_v1_dao.update_version(function_block_version_id, {
            "state": FunctionBlockVersionState.PREHANDLING.value
        })
        function_block_id = function_block_version.function_block_id
        # download zip file
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"function-block-version/{function_block_version_id}.raw-fb-zip")
        tmp_path = tempfile.mkdtemp()
        zip_path = os.path.join(tmp_path, "raw-fb.zip")
        unzip_path = os.path.join(tmp_path, "raw-fb")

        porter.fetch_file(zip_path)
        # unzip using the zipfile module
        zip_file = zipfile.ZipFile(zip_path)
        # Reject archive members that would escape the extraction directory (zip-slip).
        unzip_root = os.path.realpath(unzip_path)
        for member in zip_file.namelist():
            member_path = os.path.realpath(os.path.join(unzip_root, member))
            if member_path != unzip_root and not member_path.startswith(unzip_root + os.sep):
                raise ValueError(f"Unsafe path in function block archive: {member}")
        zip_file.extractall(unzip_path)

        # read static-config.json
        static_config_path = os.path.join(unzip_path, "static-config.json")
        if not os.path.exists(static_config_path):
            raise Exception("lack of static_config.json")
        static_config = {}
        with open(static_config_path, "r") as f:
            static_config = json.load(f)
        args = dict.get(static_config, "args", [])
        args = args if args is not None else []
        args = FunctionBlockTool.complete_args(args)
        document_url = dict.get(static_config, "document_url", None)
        description = dict.get(static_config, "description", None)
        tag = dict.get(static_config, "tag", None)
        source = dict.get(static_config, "source", None)
        program_language = dict.get(static_config, "program_language", "Python")
        plot_only = dict.get(static_config, "plot_only", False)
        runtime_version = dict.get(static_config, "runtime_version", None)
        preset_env = dict.get(static_config, "preset_env", None)
        alt_name = dict.get(static_config, "alt_name", None)
        name = dict.get(static_config, "name", "unamed_fb")
        is_v2 = dict.get(static_config, "is_v2", False)

        # clear old files in s3
        porter.set_operation_target(f"function-block-version/{function_block_version_id}/")
        former_related_object_keys = porter.list_files(recursive=True)
        for object_key in former_related_object_keys:
            porter.set_operation_target(object_key)
            porter.remove_file()

        # upload to s3
        for root, dirs, files in os.walk(unzip_path):
            for file in files:
                local_path = os.path.join(root, file)
                s3_key = os.path.join("function-block-version", function_block_version_id, os.path.relpath(local_path, unzip_path))
                porter.set_operation_target(s3_key)
                porter.save_file(local_path)

        # update args, document_url, description, tag, source
        function_block_v1_dao.update_version(function_block_version_id, {
            "args": json.dumps(args),
            "document_url": document_url,
            "description": description,
            "tag": tag,
            "source": source,
            "program_language": program_language,
            "plot_only": plot_only,
            "runtime_version": runtime_version,
            "preset_env": preset_env,
            "alt_name": alt_name,
            "name": name,
            "is_v2": is_v2,
            "state": FunctionBlockVersionState.OK.value
        })
        # update fb record current version id
        function_block_v1_dao.update(function_block_id, {
            "current_version_id": function_block_version_id,
            "alt_name": alt_name
        })

        # cleanup
        # delete local files
        shutil.rmtree(tmp_path)

    def get_function_block_version_code(self, function_block_version_id, file):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"function-block-version/{function_block_version_id}/{file}")
        try:
            content = porter.fetch_file_stream()
            code = content.decode("utf-8")
            return code
        except Exception as e:
            return None
        
    def get_function_block_version_structure(self, function_block_version_id):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(f"function-block-version/{function_block_version_id}/")
        all_files = porter.list_files(recursive=True)
        structure = {}
        for file_key in all_files:
            if file_key.endswith('/'):
                continue
            relative_path = file_key.replace(f"function-block-version/{function_block_version_id}/", "")
            parts = relative_path.split('/')
            current_level = structure
            for part in parts[:-1]:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
            current_level[parts[-1]] = "file"
        return structure

    def download_function_block_version(self, function_block_version_id):
        porter = PorterFactory.create_porter()
        prefix = f"function-block-version/{function_block_version_id}/"
        porter.set_operation_target(prefix)
        all_files = porter.list_files(recursive=True)
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_key in all_files:
                if file_key.endswith('/'):
                    continue
                # Remove the prefix to get relative path
                # This ensures files are at the top level when extracted
                relative_path = file_key[len(prefix):] if file_key.startswith(prefix) else file_key
                content = porter.fetch_file_stream(file_key)
                zip_file.writestr(relative_path, content)
        zip_buffer.seek(0)
        return zip_buffer

    def update_version_is_v2(self, function_block_version_id: int, is_v2: bool) -> None:
        """Update the is_v2 field of a function block version"""
        function_block_v1_dao.update_version(function_block_version_id, {"is_v2": is_v2})

    def get_existing_public_fbvs_v2(self):
        v2_fbvs = function_block_v1_dao.find_version_by_is_v2_and_user_id(True, SpecialUserId.PUBLIC.value)
        return v2_fbvs

function_block_v1_service = FunctionBlockV1Service()

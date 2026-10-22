from datetime import datetime
from dao.data import data_dao
from model.data import Data
from constants.data import CreatedFrom
from exception.data.confirm import DataConfirmException
from dao.analysis_data_relation import analysis_data_relation_dao
from model.analysis_data_relation import AnalysisDataRelation
from model.data_user_relation import DataUserRelation
from dao.computation import computation_dao
from dao.node import node_dao
from dao.edge import edge_dao
from exception.data.collect import DataCollectException
from waiter.data_waiter import DataWaiter
from typing import List
from dao.data import data_dao
from model.data import Data
from constants.authority import SpecialUserId, Relation, Permission
from constants.node import NodeType, NodeState
from constants.data import DataState
from datetime import datetime
from exception.data.delete import DataDeleteException
from dao.thirty_part_data_source import thirty_part_data_source_dao
from batch_job.aws import AWSBatchJob
from constants.batch import DATA_PREPROCESSOR_QUEUE
from llm.llm_interface import LlmInterface
from log.logger_factory import logger_factory
from sss.porter_factory import PorterFactory
from sss.porter import Porter
from model.llm_consumption import LLMConsumption
from dao.llm import llm_dao

logger = logger_factory.create_logger("DataService")

class DataService:

    def create_frame_record(self, user_id, upload_type, name, species, description):
        now = datetime.now()
        data = Data(
            upload_type=upload_type,
            created_from=CreatedFrom.UPLOAD.value,
            created_time=now,
            collected=False,
            name=name,
            species=species,
            description=description,
            state=DataState.UPLOADING.value,
            error_message=None
        )
        data_dao.insert(data)
        data_user_relation = DataUserRelation(
            data_id=data.id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        data_dao.insert_user_relation(data_user_relation)
        return data
    
    def prepare_h5ad_upload_info(self, data_id, file_size):
        data_waiter = DataWaiter(data_id)
        return data_waiter.fetch_h5ad_upload_info(file_size)

    def prepare_h5ad_download_info(self, data_id, user_id):
        data_waiter = DataWaiter(data_id)
        return data_waiter.fetch_h5ad_download_info()

    def prepare_data_component_upload_info(self, data_id, component_type, file_suffix, file_size):
        data_waiter = DataWaiter(data_id)
        data = data_dao.find_by_id(data_id)
        upload_type = data.upload_type
        return data_waiter.fetch_data_component_upload_info(
            file_size,
            upload_type,
            component_type,
            file_suffix
        )
    
    def prepare_data_component_download_info(self, data_id, component_type):
        data_waiter = DataWaiter(data_id)
        data = data_dao.find_by_id(data_id)
        upload_type = data.upload_type
        return data_waiter.fetch_data_component_download_info(
            upload_type,
            component_type
        )

    def collect(self, node_id, data_name):
        node = node_dao.find_by_id(node_id)
        if node.type == NodeType.DATA_NODE.value or node.type == NodeType.DATA_NODE_V2.value:
            raise DataCollectException("data node can not be collected")
        # NOTE: this is a temporary solution, we should use a more
        if node.type != NodeType.COMPUTATION_NODE.value and node.type != NodeType.COMPUTATION_NODE_V2.value:
            raise DataCollectException("node type error")
        latest_computation = computation_dao.find_latest_by_node_id(node_id)
        if latest_computation is None:
            raise DataCollectException("no computation found")
        if latest_computation.computation_state != NodeState.FINISHED.value:
            raise DataCollectException("computation not finished")
        collected_data_id = latest_computation.result_data_id
        data_dao.update(collected_data_id, {
            "collected": True,
            "name": data_name
        })
        return True

    def get_list_of_user(self, user_id, search_key):
        data_list:List[Data] = data_dao.find_by_user_id(user_id, search_key)
        return data_list

    def get_data_source_list(self, user_id, search_key):
        data_list:List[Data] = data_dao.find_by_user_id(user_id, search_key)
        data_list = [
            data
            for data in data_list
            if data.created_from == CreatedFrom.UPLOAD.value or
            data.collected == True
        ]
        return data_list
    
    def get_data_source_index(self, data_id, user_id, search_key, only_ok):
        data_source_list = data_dao.find_index_by_user_id(data_id, user_id, search_key, only_ok)
        return data_source_list
    
    def get_data_source_page(self, user_id, page, page_size, search_key, only_ok):
        data_source_list = data_dao.find_data_source_page_by_user_id(user_id, page, page_size, search_key, only_ok)
        total_count = data_dao.find_data_source_count_by_user_id(user_id, search_key, only_ok)
        return {
            "list": data_source_list,
            "total_count": total_count
        }

    def get_collected_list(self, user_id, search_key):
        data_list = data_dao.find_by_user_id_and_collected(
            user_id, collected=True, search_key=search_key)
        return data_list

    def get_uploaded_list(self, user_id, search_key):
        uploaded_list = data_dao.find_by_user_id_and_created_from_and_state(
            user_id,
            CreatedFrom.UPLOAD.value,
            DataState.OK.value,
            search_key
        )
        return uploaded_list
    
    def get_data_list_by_state(self, user_id, state, search_key):
        data_list = data_dao.find_by_user_id_and_state(
            user_id,
            state,
            search_key
        )
        return data_list

    def get_imported_list_by_analysis_id(self, analysis_id):
        analysis_data_relation_list: List[AnalysisDataRelation] = \
            analysis_data_relation_dao.find_by_analysis_id(analysis_id)
        data_id_list = [
            analysis_data_relation.data_id
            for analysis_data_relation
            in analysis_data_relation_list
        ]
        data_list: List[Data] = data_dao.find_by_id_list(data_id_list)
        return data_list

    def get_public_list(self, search_key):
        data_list = data_dao.find_by_user_id_and_created_from(
            SpecialUserId.PUBLIC.value,
            CreatedFrom.UPLOAD.value,
            search_key
        )
        return data_list

    def get_recent_valid_data(self, node_id):
        edge_path = edge_dao.find_by_target_node_id(node_id)
        index = 0
        while index < len(edge_path):
            edge = edge_path[index]
            source_node = node_dao.find_by_id(edge.source_node_id)
            if source_node.type == NodeType.DATA_NODE.value or source_node.type == NodeType.DATA_NODE_V2.value:
                data = data_dao.find_by_id(source_node.data_id)
                return data
            elif source_node.type == NodeType.COMPUTATION_NODE.value or source_node.type == NodeType.COMPUTATION_NODE_V2.value:
                if source_node.state == NodeState.FINISHED.value:
                    computation = \
                        computation_dao.find_latest_by_node_id(
                            source_node.id
                        )
                    return data_dao.find_by_id(computation.result_data_id)
                else:
                    edge_path += edge_dao.find_by_target_node_id(
                        source_node.id
                    )
            index += 1
        return None

    def remove(self, data_id, user_id):
        data = data_dao.find_by_id(data_id)
        data_user_relation = data_dao.find_user_relation_by_data_id_and_user_id(data_id, user_id, Relation.BELONG_TO.value)
        if data_user_relation is None:
            raise DataDeleteException("no permission to delete data")
        if data.created_from != CreatedFrom.UPLOAD.value:
            raise DataDeleteException("can not delete uploaded data")
        AWSBatchJob.stop_job_by_name(f"data_{data_id}", DATA_PREPROCESSOR_QUEUE)
        waiter = DataWaiter(data_id)
        data_dao.delete(data_id)
        waiter.remove_data()

    def remove_data_component(self, data_id, component_type):
        data = data_dao.find_by_id(data_id)
        upload_type = data.upload_type
        waiter = DataWaiter(data_id)
        waiter.remove_data_component(upload_type, component_type)

    def edit(self, data_id, name, description):
        data_dao.update(data_id, {
            "name": name,
            "description": description
        })

    def get_data_component_list_in_data(self, data_id, upload_type):
        data_waiter = DataWaiter(data_id)
        return data_waiter.fetch_component_list(upload_type)

    def edit_data_component_type(self, data_id, old_component_type, new_component_type):
        data = data_dao.find_by_id(data_id)
        upload_type = data.upload_type
        data_waiter = DataWaiter(data_id)
        data_waiter.edit_data_component_type(upload_type, old_component_type, new_component_type)

    def get_data_info(self, data_id):
        data = data_dao.find_by_id(data_id)
        return data
    
    def get_source_data_info(self, data_id):
        computation = computation_dao.find_by_result_data_id(data_id)
        # if computation is empty, the data was uploaded, so return its own info directly
        if computation is None:
            return {
                "node": None,
                "data": data_dao.find_by_id(data_id)
            }
        node = node_dao.find_by_id(computation.node_id)
        while node.type != NodeType.DATA_NODE.value and node.type != NodeType.DATA_NODE_V2.value:
            edge = edge_dao.find_by_target_node_id(node.id)
            if len(edge) == 0:
                break
            node = node_dao.find_by_id(edge[0].source_node_id)
        if node.type == NodeType.DATA_NODE.value or node.type == NodeType.DATA_NODE_V2.value:
            data = data_dao.find_by_id(node.data_id)
            return {
                "node": node,
                "data": data
            }
        return None
    
    def get_thirty_part_data_source_list(self, page, page_size, search_key, sort, order):
        return {
            "list":thirty_part_data_source_dao.find_page(page, page_size, search_key, sort, order),
            "total_count":thirty_part_data_source_dao.find_total_count(search_key)
        }
    
    def capture_data_list_by_llm(self, user_id, user_request):
        llm_interface = LlmInterface()
        # third-party data
        response = llm_interface.capture_data(user_request, user_id)
        consumption = response["consumption"]

        consumption["user_id"] = user_id
        consumption["functionality"] = "Data Capture"
        consumption["functionality_task_id"] = -1
        consumption["node_id"] = -1
        llm_consumption = LLMConsumption(**consumption)
        llm_dao.insert_consumption(llm_consumption)
        return response
    
    def get_referenced_state(self, data_id):
        node = node_dao.find_by_data_id(data_id)
        if len(node) > 0:
            return True
        return False
    
    def get_information(self, object_key, porter: Porter):
        if object_key.endswith("/"):
            folder_name = object_key[:-1].split("/")[-1]
            return {
                "object_key": object_key,
                "size": "-",
                "last_modified": "-",
                "collected": False,
                "mime_type": "folder",
                "file_name": folder_name + '/'
            }
        else:
            head = porter.get_head(object_key)
            metadata = head.get("Metadata")
            file_name = object_key.split("/")[-1]
            return {
                "object_key": object_key,
                "size": head.get("ContentLength"),
                "last_modified": head.get("LastModified"),
                "collected": metadata.get("collected", False),
                "mime_type": file_name.split(".")[-1] if "." in file_name else "-",
                "file_name": "/".join(object_key.split("/")[2:])
            }
    
    def list_general_inputs(self, data_id, prefix=None, start_after_file_name=None, 
                         max_keys=50, search_query=None, file_type_filter=None) -> dict:
        """
        List output files with support for pagination, search, and filtering.
        
        Args:
            data_id: ID of the data
            prefix: Optional folder prefix to list files from
            start_after_file_name: File name to start after (for pagination)
            max_keys: Maximum number of files to return (default: 50)
            search_query: Optional search string to filter file names
            file_type_filter: Optional file type filter (e.g., 'png', 'csv', 'h5ad', 'folder')
            
        Returns:
            Dictionary containing:
                - objects: List of file objects with metadata
                - next_start_after: Next start_after value for pagination
                - has_more: Boolean indicating if more files exist
                - total: Total number of files returned
                - filtered_count: Number of files after filtering
        """
        data = data_dao.find_by_id(data_id=data_id)
        
        if data is None:
            logger.warning(f"Data not found: {data_id}")
            return {
                "objects": [],
                "next_start_after": None,
                "has_more": False,
                "total": 0,
                "filtered_count": 0
            }
        real_prefix = f"adata/{data.id}-general-s3-store/{prefix}/" if prefix else f"adata/{data.id}-general-s3-store/"

        porter = PorterFactory.create_porter()
        porter.set_operation_target(real_prefix)
        logger.info(f"Listing files with prefix: {real_prefix}")
        
        # Ensure max_keys is reasonable
        max_keys = min(max(1, max_keys), 1000)  # Between 1 and 1000
        
        start_after_object_key = f"{real_prefix}{start_after_file_name}" if start_after_file_name else ""
        if start_after_file_name:
            logger.info(f"Starting after: {start_after_object_key}")
        
        # Fetch more files than needed to allow for filtering
        fetch_max_keys = max_keys * 3 if (search_query or file_type_filter) else max_keys
        object_key_list = porter.list_files(
            start_after=start_after_object_key, max_keys=fetch_max_keys, recursive=True)
        
        # Convert to object list
        object_list = [
            object_key if type(object_key) == str else object_key.get("Prefix", None) 
            for object_key in object_key_list
        ]
        
        # Get information for each object
        object_list = [
            self.get_information(object_key, porter) 
            for object_key in object_list if object_key is not None
        ]
        
        total_before_filter = len(object_list)
        
        # Apply search filter
        if search_query and search_query.strip():
            search_query_lower = search_query.strip().lower()
            object_list = [
                obj for obj in object_list 
                if search_query_lower in obj.get("file_name", "").lower()
            ]
        
        # Apply file type filter
        if file_type_filter and file_type_filter.strip():
            file_type_filter_lower = file_type_filter.strip().lower()
            object_list = [
                obj for obj in object_list 
                if obj.get("mime_type", "").lower() == file_type_filter_lower
            ]
        
        # Limit to max_keys after filtering
        filtered_count = len(object_list)
        has_more = filtered_count > max_keys or (total_before_filter == fetch_max_keys and not (search_query or file_type_filter))
        object_list = object_list[:max_keys]
        
        # Determine next_start_after
        next_start_after = None
        if has_more and object_list:
            last_obj = object_list[-1]
            # Extract the file name from the object key
            last_obj_key = last_obj.get("object_key", "")
            if last_obj_key.startswith(real_prefix):
                next_start_after = last_obj_key[len(real_prefix):]
            else:
                next_start_after = last_obj.get("file_name", "")
        
        return {
            "objects": object_list,
            "next_start_after": next_start_after,
            "has_more": has_more,
            "total": len(object_list),
            "filtered_count": filtered_count
        }
    
    def get_general_inputs_item_download_info(self, object_key):
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        return porter.get_presigned_url(60 * 60)

data_service = DataService()

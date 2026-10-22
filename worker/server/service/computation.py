import subprocess
import uuid
import os
import boto3
from waiter.retry_process import RetryProcessWaiter
from waiter.computation import ComputationWaiter
from dao.computation import computation_dao
from dao.node import node_dao
from dao.task import task_dao
from dao.edge import edge_dao
from dao.figure import figure_dao
from constants.node import NodeState, NodeType
from batch_job.aws import AWSBatchJob
from constants.task import TaskState
from computation_logs.aws_cloudwatch_taker import AWSCloudwatchLogsTaker
from datetime import datetime, timedelta
from model.computation import Computation
from model.computation_retry_process import ComputationRetryProcess
from model.bug_fixer_session import BugFixerSession
from model.fix_description import FixDescription
from tool.llm_interface import LlmInterface
from typing import List
from sss.porter import Porter
from sss.porter_factory import PorterFactory
from constants.sss import COMPUTATION_OUTPUT_FOLDER_PREFIX
from constants.computation_retry_process import ComputationRetryProcessState
from log.logger_factory import LoggerFactory
from tool.task_inspector import task_inspector
from tool.common_converter import convert_model_to_dict
from dao.computation_log import computation_log_dao
from model.llm_consumption import LLMConsumption
import json
from constants.gpt_server import (
    GPT_WORKFLOW_SERVER_HOST,
    GPT_WORKFLOW_SERVER_PORT,
    NETWORK_PROXY_HOST,
    NETWORK_PROXY_PORT,
)
from constants.computation import (
    ComputationState,
    R_JOB_DEFINITION,
    JOB_QUEUE,
    LARGE_JOB_QUEUE,
    LOGS_GROUP_NAME,
    BASH_JOB_DEFINITION,
    PYTHON_JOB_DEFINITION_SCANPY,
    PYTHON_JOB_DEFINITION_DYN,
    PYTHON_JOB_DEFINITION_MEBOCOST,
    PYTHON_JOB_DEFINITION_SCVELO,
    PYTHON_JOB_DEFINITION_SCFATES,
    PYTHON_JOB_DEFINITION_DEFAULT
)
from dao.llm import llm_dao
from db.config import (
    HOST,
    PORT,
    DATABASE,
    USERNAME,
    PASSWORD
)
from constants.common import DEPLOY_ENV
from constants.node import NodeType
from constants.sss import BUCKET_NAME
from constants.computation_retry_process import ComputationRetryProcessState
from waiter.figure_waiter import FigureWaiter


# Root of the worker code inside the container (configurable for local runs).
CODE_SPACE_ROOT = os.environ.get("OMICAIRN_CODE_SPACE", "/omicairn/code_space")


def _child_env(extra: dict) -> dict:
    """Environment for a child worker process: inherit ours, add non-None extras."""
    env = dict(os.environ)
    env.update({k: str(v) for k, v in extra.items() if v is not None})
    return env

logger = LoggerFactory.get_logger("ComputationService")


class ComputationService:
    def get_list_by_node(self, node_id) -> List[Computation]:
        computation_list = computation_dao.find_by_node_id(node_id)
        return computation_list

    def get_list_by_task(self, task_id) -> List[Computation]:
        computation_list = computation_dao.find_by_task_id(task_id)
        return computation_list

    def get_latest_by_node(self, node_id) -> Computation:
        computation = computation_dao.find_latest_by_node_id(node_id)
        return computation

    def get_summary(self, computation_id):
        waiter = ComputationWaiter(computation_id)
        waiter.check_result_exists()
        return waiter.get_result()

    def get_log(self, computation_id):
        computation_waiter = ComputationWaiter(computation_id)
        log = computation_waiter.get_log()
        if log:
            return json.loads(log)
        return []

    def refresh_optimized_error_description(self, computation_id, user_id) -> Computation:
        llm_interface = LlmInterface()
        response = llm_interface.apply_for_optimize_error_description(computation_id)
        try:
            consumption = response.json().get("consumption", {}) or {}
        except Exception as e:
            logger.error(f"Failed to get consumption from LLM response: {e}")
            consumption = {}
        computation = computation_dao.find(computation_id)
        consumption["user_id"] = user_id
        consumption["node_id"] = computation.node_id
        consumption["functionality"] = "Computation Error Message Optimization"
        consumption["functionality_task_id"] = computation.id
        consumption["created_at"] = datetime.now()
        consump = LLMConsumption(**consumption)
        llm_dao.insert_consumption(consump)
        return computation

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

    def get_figures(self, computation_id):
        figures = figure_dao.find_by_computation_id(computation_id)
        figure_list = []
        for figure in figures:
            waiter = FigureWaiter(figure.figure_uuid)
            figure_list.append(waiter.get_download_info_with_suffix("png"))
        return figure_list

    def list_output_files(self, computation_id, prefix=None, start_after_file_name=None, 
                         max_keys=50, search_query=None, file_type_filter=None) -> dict:
        """
        List output files with support for pagination, search, and filtering.
        
        Args:
            computation_id: ID of the computation
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
        computation = computation_dao.find(computation_id)
        if not computation:
            logger.warning(f"Computation not found: {computation_id}")
            return {
                "objects": [],
                "next_start_after": None,
                "has_more": False,
                "total": 0,
                "filtered_count": 0
            }
        node = node_dao.find_by_id(computation.node_id)
        if not node:
            logger.warning(f"Node not found for computation: {computation_id}")
            return {
                "objects": [],
                "next_start_after": None,
                "has_more": False,
                "total": 0,
                "filtered_count": 0
            }
        
        is_notebook = node.type == NodeType.NOTEBOOK_NODE
        is_claude_code = node.type == NodeType.CLAUDE_CODE_NODE.value
        is_v2 = node.type.endswith("v2") if node.type else False

        if is_claude_code:
            return self._list_claude_code_output_files(
                computation_id, prefix, start_after_file_name,
                max_keys, search_query, file_type_filter
            )

        if not is_v2 and not is_notebook:
            inner_key = prefix + "/" if prefix else ""
            real_prefix = f"{COMPUTATION_OUTPUT_FOLDER_PREFIX}/{computation_id}/{inner_key}"
        else:
            real_prefix = f"adata/{computation.result_data_id}-general-s3-store/{prefix}/" if prefix else f"adata/{computation.result_data_id}-general-s3-store/"
        
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

        # Return Size and LastModified directly from the list response
        object_metadata_list = porter.list_files_with_metadata(
            start_after=start_after_object_key, max_keys=fetch_max_keys, recursive=True)

        # Convert to standard object
        object_list = []
        for item in object_metadata_list:
            object_key = item["Key"]
            is_folder = item.get("IsFolder", object_key.endswith("/"))

            if is_folder:
                folder_name = object_key[:-1].split("/")[-1]
                file_name = folder_name + '/'
            else:
                file_name = "/".join(object_key.split("/")[2:])

            # Skip thumbnails
            if file_name.split("/")[-1].startswith("thumbnail_"):
                continue

            base_name = object_key.split("/")[-1]
            mime_type = "folder" if is_folder else (base_name.split(".")[-1] if "." in base_name else "-")

            object_list.append({
                "object_key": object_key,
                "size": "-" if is_folder else item.get("Size", 0),
                "last_modified": "-" if is_folder else item.get("LastModified"),
                "collected": False,
                "mime_type": mime_type,
                "file_name": file_name
            })

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

    def _list_claude_code_output_files(self, computation_id, prefix=None, start_after_file_name=None,
                                        max_keys=50, search_query=None, file_type_filter=None) -> dict:
        """
        List output files for Claude Code computations from the Claude Code S3 bucket.
        """
        computation = computation_dao.find(computation_id)
        if not computation or not computation.result_data_id:
            logger.warning(f"[claude code] Computation or result_data_id not found: {computation_id}")
            return {
                "objects": [],
                "next_start_after": None,
                "has_more": False,
                "total": 0,
                "filtered_count": 0
            }

        cc_bucket = os.environ.get('CLAUDE_CODE_BUCKET_NAME') or BUCKET_NAME
        cc_profile = os.environ.get('CLAUDE_CODE_AWS_PROFILE') or None

        try:
            cc_session = boto3.Session(profile_name=cc_profile)
            s3_client = cc_session.client('s3')

            inner_prefix = f"{prefix}/" if prefix else ""
            real_prefix = f"adata/{computation.result_data_id}-general-s3-store/{inner_prefix}"
            logger.info(f"[claude code] Listing files with prefix: {real_prefix}")

            # Ensure max_keys is reasonable
            max_keys = min(max(1, max_keys), 1000)

            start_after_object_key = f"{real_prefix}{start_after_file_name}" if start_after_file_name else ""
            if start_after_file_name:
                logger.info(f"[claude code] Starting after: {start_after_object_key}")

            # Fetch more files than needed to allow for filtering
            fetch_max_keys = max_keys * 3 if (search_query or file_type_filter) else max_keys

            # List files from S3
            list_params = {
                'Bucket': cc_bucket,
                'Prefix': real_prefix,
                'MaxKeys': fetch_max_keys
            }
            if start_after_object_key:
                list_params['StartAfter'] = start_after_object_key

            response = s3_client.list_objects_v2(**list_params)

            # Convert to standard object
            object_list = []
            for item in response.get('Contents', []):
                object_key = item["Key"]
                is_folder = object_key.endswith("/")

                if is_folder:
                    folder_name = object_key[:-1].split("/")[-1]
                    file_name = folder_name + '/'
                else:
                    # Extract file name relative to real_prefix
                    file_name = object_key[len(real_prefix):] if object_key.startswith(real_prefix) else object_key.split("/")[-1]

                # Skip thumbnails
                if file_name.split("/")[-1].startswith("thumbnail_"):
                    continue

                base_name = object_key.split("/")[-1]
                mime_type = "folder" if is_folder else self._get_mime_type(base_name)

                object_list.append({
                    "object_key": object_key,
                    "size": "-" if is_folder else item.get("Size", 0),
                    "last_modified": "-" if is_folder else (item.get("LastModified").isoformat() if item.get("LastModified") else None),
                    "collected": False,
                    "mime_type": mime_type,
                    "file_name": file_name
                })

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

        except Exception as e:
            logger.error(f"[claude code] Failed to list output files: {e}")
            return {
                "objects": [],
                "next_start_after": None,
                "has_more": False,
                "total": 0,
                "filtered_count": 0
            }

    def list_output_folders(self, computation_id, prefix=None) -> dict:
        """
        List output folders with file counts and sizes for Claude Code computations.

        Args:
            computation_id: ID of the computation
            prefix: Optional folder prefix to list subfolders from

        Returns:
            Dictionary containing:
                - folders: List of folder objects with name, path, file_count, total_size
                - root_files: List of files at the root level (or current prefix level)
                - total_folders: Number of folders
                - total_root_files: Number of root files
        """
        computation = computation_dao.find(computation_id)
        if not computation:
            logger.warning(f"Computation not found: {computation_id}")
            return {
                "folders": [],
                "root_files": [],
                "total_folders": 0,
                "total_root_files": 0
            }

        node = node_dao.find_by_id(computation.node_id)
        if not node:
            logger.warning(f"Node not found for computation: {computation_id}")
            return {
                "folders": [],
                "root_files": [],
                "total_folders": 0,
                "total_root_files": 0
            }

        is_claude_code = node.type == NodeType.CLAUDE_CODE_NODE.value

        if is_claude_code:
            return self._list_claude_code_output_folders(computation_id, prefix)

        # For non-Claude Code nodes, return empty (can be extended later)
        return {
            "folders": [],
            "root_files": [],
            "total_folders": 0,
            "total_root_files": 0
        }

    def _list_claude_code_output_folders(self, computation_id, prefix=None) -> dict:
        """
        List folders and root files for Claude Code outputs.
        Uses S3 Delimiter='/' to get folder structure without listing all files.
        """
        cc_bucket = os.environ.get('CLAUDE_CODE_BUCKET_NAME') or BUCKET_NAME
        cc_profile = os.environ.get('CLAUDE_CODE_AWS_PROFILE') or None

        try:
            cc_session = boto3.Session(profile_name=cc_profile)
            s3_client = cc_session.client('s3')

            inner_prefix = f"{prefix}/" if prefix else ""
            real_prefix = f"computation/{computation_id}/outputs/{inner_prefix}"
            logger.info(f"[claude code] Listing folders with prefix: {real_prefix}")

            # Use Delimiter to get folders as CommonPrefixes
            response = s3_client.list_objects_v2(
                Bucket=cc_bucket,
                Prefix=real_prefix,
                Delimiter='/'
            )

            folders = []
            for prefix_obj in response.get('CommonPrefixes', []):
                folder_path = prefix_obj['Prefix']
                folder_name = folder_path[len(real_prefix):].rstrip('/')

                # Skip empty folder names
                if not folder_name:
                    continue

                # Get file count and size for this folder
                folder_stats = self._get_folder_stats(s3_client, cc_bucket, folder_path)

                folders.append({
                    'name': folder_name,
                    'path': folder_path,
                    'file_count': folder_stats['count'],
                    'total_size': folder_stats['size']
                })

            # Get root-level files (files directly in this folder, not in subfolders)
            root_files = []
            for obj in response.get('Contents', []):
                key = obj['Key']
                file_name = key[len(real_prefix):]

                # Skip if it's in a subfolder or is the folder itself
                if '/' in file_name or not file_name:
                    continue

                # Skip thumbnails
                if file_name.startswith("thumbnail_"):
                    continue

                mime_type = self._get_mime_type(file_name)

                root_files.append({
                    'object_key': key,
                    'file_name': file_name,
                    'size': obj.get('Size', 0),
                    'last_modified': obj.get('LastModified').isoformat() if obj.get('LastModified') else None,
                    'mime_type': mime_type
                })

            # Sort folders by name (step_01, step_02, etc. will sort naturally)
            folders.sort(key=lambda x: x['name'])

            return {
                'folders': folders,
                'root_files': root_files,
                'total_folders': len(folders),
                'total_root_files': len(root_files)
            }

        except Exception as e:
            logger.error(f"[claude code] Failed to list output folders: {e}")
            return {
                "folders": [],
                "root_files": [],
                "total_folders": 0,
                "total_root_files": 0
            }

    def _get_folder_stats(self, s3_client, bucket, folder_prefix) -> dict:
        """Get file count and total size for a folder."""
        paginator = s3_client.get_paginator('list_objects_v2')
        total_count = 0
        total_size = 0

        try:
            for page in paginator.paginate(Bucket=bucket, Prefix=folder_prefix):
                for obj in page.get('Contents', []):
                    # Skip thumbnail files
                    key = obj.get('Key', '')
                    file_name = key.split('/')[-1]
                    if file_name.startswith("thumbnail_"):
                        continue
                    total_count += 1
                    total_size += obj.get('Size', 0)
        except Exception as e:
            logger.error(f"[claude code] Failed to get folder stats for {folder_prefix}: {e}")

        return {'count': total_count, 'size': total_size}

    def _get_mime_type(self, file_name: str) -> str:
        """Determine mime type from file extension."""
        ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        mime_type_map = {
            'png': 'png', 'jpg': 'jpg', 'jpeg': 'jpg', 'gif': 'gif', 'svg': 'svg',
            'csv': 'csv', 'tsv': 'tsv', 'txt': 'txt',
            'h5ad': 'h5ad', 'h5': 'h5', 'json': 'json', 'jsonl': 'jsonl',
            'py': 'py', 'r': 'r', 'sh': 'sh', 'log': 'log',
            'md': 'md', 'pdf': 'pdf', 'html': 'html',
            'gz': 'gz', 'zip': 'zip', 'tar': 'tar',
            'rds': 'rds', 'rdata': 'rdata'
        }
        return mime_type_map.get(ext, 'unknown')

    def collect_output_file(self, computation_id, prefix, file_name):
        porter = PorterFactory.create_porter()
        inner_key = prefix + "/" + file_name if prefix else file_name
        object_key = f"{COMPUTATION_OUTPUT_FOLDER_PREFIX}/{computation_id}/{inner_key}"
        porter.set_operation_target(object_key)
        porter.update_metadata(object_key, {"collected": True})

    def set_logs(self, computation_id, logs):
        logs_str = json.dumps(logs)
        computation_waiter = ComputationWaiter(computation_id)
        computation_waiter.save_log(logs_str)

    def get_output_file_download_info(self, object_key, computation_id):
        is_claude_code = False

        computation = computation_dao.find(computation_id)
        if computation:
            node = node_dao.find_by_id(computation.node_id)
            if node:
                is_claude_code = node.type == NodeType.CLAUDE_CODE_NODE.value

        if is_claude_code:
            cc_bucket = os.environ.get('CLAUDE_CODE_BUCKET_NAME') or BUCKET_NAME
            cc_profile = os.environ.get('CLAUDE_CODE_AWS_PROFILE') or None
            try:
                cc_session = boto3.Session(profile_name=cc_profile)
                cc_client = cc_session.client('s3')
                url = cc_client.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={
                        'Bucket': cc_bucket,
                        'Key': object_key
                    },
                    ExpiresIn=60 * 60
                )
                return url
            except Exception as e:
                logger.error(f"[claude code] Failed to generate presigned URL: {e}")
                raise
        else:
            porter = PorterFactory.create_porter()
            porter.set_operation_target(object_key)
            return porter.get_presigned_url(expiration=60 * 60)

    def scan_timeout_computations(self):
        logger.info("Scanning timeout computations")
        task_inspector.inspect_interval()

    def scan_omissive_computations(self):
        logger.info("Scanning omissive computations")
        task_inspector.inspect_remains()

    def stop_retry_process(self, retry_process_id):
        # Do not force-stop the computation for now
        computation_dao.update_retry_process(retry_process_id, {
            "state": ComputationRetryProcessState.STOPPED.value
        })

    def stop_all_retry_process(self):
        running_retry_processes = computation_dao.find_retry_process_by_state(
            ComputationRetryProcessState.RUNNING.value)
        for retry_process in running_retry_processes:
            logger.info(f"Stopping retry process: {retry_process.id}")
            self.stop_retry_process(retry_process.id)

    def get_retry_process_list_by_node(self, node_id):
        retry_process_list = computation_dao.find_retry_process_by_node_id(
            node_id)
        node_id_set = set([retry_process.node_id for retry_process in retry_process_list if retry_process.node_id is not None
                           ] + [
            retry_process.new_node_id for retry_process in retry_process_list if retry_process.new_node_id is not None])
        node_id_list = list(node_id_set)
        node_list = node_dao.find_by_id_list(node_id_list)
        node_dict = {node.id: node for node in node_list}
        computation_list = computation_dao.find_by_retry_process_id_list(
            [retry_process.id for retry_process in retry_process_list])
        computation_dict = {}
        for computation in computation_list:
            if computation.retry_process_id not in computation_dict:
                computation_dict[computation.retry_process_id] = []
            computation_dict[computation.retry_process_id].append(
                computation.to_dict())
        result = []
        for retry_process in retry_process_list:
            retry_process_dict = convert_model_to_dict(retry_process, True)
            old_node = node_dict.get(
                retry_process.node_id, None)
            if old_node is not None:
                retry_process_dict["old_node"] = old_node.to_dict()
            new_node = node_dict.get(
                retry_process.new_node_id, None)
            if new_node is not None:
                retry_process_dict["new_node"] = new_node.to_dict()
            retry_process_dict["computations"] = computation_dict.get(
                retry_process.id, [])
            result.append(retry_process_dict)
        return result

    def get_retry_process_list_by_analysis(self, analysis_id):
        retry_process_list = computation_dao.find_retry_process_list_by_analysis_id(
            analysis_id)
        node_id_set = set([retry_process.node_id for retry_process in retry_process_list if retry_process.node_id is not None
                           ] + [
                          retry_process.new_node_id for retry_process in retry_process_list if retry_process.new_node_id is not None])
        node_id_list = list(node_id_set)
        node_list = node_dao.find_by_id_list(node_id_list)
        node_dict = {node.id: node for node in node_list}
        computation_list = computation_dao.find_by_retry_process_id_list(
            [retry_process.id for retry_process in retry_process_list])
        computation_dict = {}
        for computation in computation_list:
            if computation.retry_process_id not in computation_dict:
                computation_dict[computation.retry_process_id] = []
            computation_dict[computation.retry_process_id].append(
                computation.to_dict())
        result = []
        for retry_process in retry_process_list:
            retry_process_dict = convert_model_to_dict(retry_process, True)
            old_node = node_dict.get(
                retry_process.node_id, None)
            if old_node is not None:
                retry_process_dict["old_node"] = old_node.to_dict()
            new_node = node_dict.get(
                retry_process.new_node_id, None)
            if new_node is not None:
                retry_process_dict["new_node"] = new_node.to_dict()
            retry_process_dict["computations"] = computation_dict.get(
                retry_process.id, [])
            result.append(retry_process_dict)
        return result

    def get_retry_process_history_details(self, retry_process_id):
        fixer_computation_list = computation_dao.find_by_retry_process_id(
            retry_process_id)
        fixer_history_details_str = ""
        retry_process_waiter = RetryProcessWaiter(retry_process_id)
        for computation_index in range(len(fixer_computation_list)):
            computation = fixer_computation_list[computation_index]
            fixer_history_details_str += f"########################### No. {computation_index + 1} Start ###########################\n"
            node_computation_information, input_prompt, parameters_fix_solution, code_fix_solution, result = retry_process_waiter.get_one_stage_details(
                computation.id)
            fixer_history_details_str += f"Computation: {computation}\n"
            fixer_history_details_str += f"Node Computation Information: {node_computation_information}\n"
            fixer_history_details_str += f"Input Prompt: {input_prompt}\n"
            fixer_history_details_str += f"Parameters Fix Solution: {parameters_fix_solution}\n"
            fixer_history_details_str += f"Code Fix Solution: {code_fix_solution}\n"
            fixer_history_details_str += f"Result: {result}\n"
            fixer_history_details_str += f"########################### No. {computation_index + 1} End ###########################\n\n"
        return json.dumps(fixer_history_details_str)

    def trigger_retry_process(self, node_id, user_prompt: str = None, llm_model: str = None, max_debug: int = 3):
        node = node_dao.find_by_id(node_id)
        if node is None or node.state != NodeState.FAILED.value:
            raise Exception(f"This node({node_id}) is not in failed state")
        previous_edges = edge_dao.find_all_front_edges(node_id)
        previous_node_ids = [node_id] + \
            [edge.source_node_id for edge in previous_edges]
        node_dao.update_by_id_list(previous_node_ids, {
            "locked": True
        })
        latest_computation = computation_dao.find_latest_by_node_id(node_id)
        if latest_computation is None or latest_computation.computation_state != ComputationState.FAILED.value:
            raise Exception(
                f"This node({node_id}) has no failed computation")
        task = task_dao.find_by_id(latest_computation.task_id)
        task_dao.update(task.id, {
            "state": TaskState.RUNNING.value
        })

        random_str = uuid.uuid4().hex
        temp_path = f"/tmp/{random_str}.json"
        with open(temp_path, "w") as f:
            json.dump({
                "success": False,
                "computation_id": latest_computation.id,
                "error_description": latest_computation.error_description,
                "need_optimize": False,
                "directly_trigger": True,
                "user_prompt": user_prompt,
                "llm_model": llm_model,
                "max_debug": max_debug
            }, f)
        subprocess.Popen(
            ["python3", os.path.join(CODE_SPACE_ROOT, 'handle_job_feedback', 'index.py')],
            env=_child_env({
                "DB_HOST": HOST,
                "DB_PORT": PORT,
                "DB_NAME": DATABASE,
                "DB_USER": USERNAME,
                "DB_PASSWORD": PASSWORD,
                "PYTHON_JOB_DEFINITION_SCANPY": PYTHON_JOB_DEFINITION_SCANPY,
                "PYTHON_JOB_DEFINITION_DYN": PYTHON_JOB_DEFINITION_DYN,
                "PYTHON_JOB_DEFINITION_MEBOCOST": PYTHON_JOB_DEFINITION_MEBOCOST,
                "PYTHON_JOB_DEFINITION_SCVELO": PYTHON_JOB_DEFINITION_SCVELO,
                "PYTHON_JOB_DEFINITION_SCFATES": PYTHON_JOB_DEFINITION_SCFATES,
                "PYTHON_JOB_DEFINITION_DEFAULT": PYTHON_JOB_DEFINITION_DEFAULT,
                "R_JOB_DEFINITION": R_JOB_DEFINITION,
                "BASH_JOB_DEFINITION": BASH_JOB_DEFINITION,
                "JOB_QUEUE": JOB_QUEUE,
                "LARGE_JOB_QUEUE": LARGE_JOB_QUEUE,
                "DEPLOY_ENV": DEPLOY_ENV,
                "OPTIONS_PATH": temp_path,
                "GPT_WORKFLOW_SERVER_HOST": GPT_WORKFLOW_SERVER_HOST,
                "GPT_WORKFLOW_SERVER_PORT": GPT_WORKFLOW_SERVER_PORT,
                "NETWORK_PROXY_HOST": NETWORK_PROXY_HOST,
                "NETWORK_PROXY_PORT": NETWORK_PROXY_PORT,
                "BUCKET_NAME": BUCKET_NAME,
            })
        )

    def get_retry_process_prompt(self, retry_process_id, computation_id):
        retry_process_waiter = RetryProcessWaiter(retry_process_id)
        return retry_process_waiter.get_prompt(computation_id)

    def refresh_function_block_average_duration(self):
        computation_dao.refresh_function_block_average_duration()

    def get_retry_process_trace(self, computation_id):
        computation = computation_dao.find(computation_id)
        retry_process_id = computation.retry_process_id
        computation_list = computation_dao.find_by_retry_process_id(
            retry_process_id)
        computation_list.sort(key=lambda x: x.created_time)
        retry_process_waiter = RetryProcessWaiter(retry_process_id)
        session_urls = []
        for computation in computation_list:
            session_url = None
            bug_fixer_session = computation_dao.find_bug_fixer_session_by_fixed_computation_id(computation.id)
            if bug_fixer_session:
                session_url = retry_process_waiter.get_a_session(bug_fixer_session.id)
            session_urls.append({
                "computation": computation.to_dict(),
                "session_url": session_url,
            })
        return session_urls

    def get_retry_process_session(self, computation_id):
        computation = computation_dao.find(computation_id)
        retry_process_id = computation.retry_process_id
        retry_process_waiter = RetryProcessWaiter(retry_process_id)
        bug_fixer_session = computation_dao.find_bug_fixer_session_by_fixed_computation_id(computation_id)
        if bug_fixer_session:
            return retry_process_waiter.get_a_session(bug_fixer_session.id)
        return None

    def record_bug_fixer_session(self, session: dict, user_id: str):
        """
        Record a bug fixer session in the database.

        :param session: An instance of BugFixerSession containing session details.
        :return: The recorded BugFixerSession instance.
        """
        try:
            for time_key in ['created_at', "start_time", "end_time"]:
                if time_key in session and session[time_key] is not None:
                    if isinstance(session[time_key], (int, float)):
                        session[time_key] = datetime.fromtimestamp(
                            session[time_key] / 1000)
                    elif not isinstance(session[time_key], datetime):
                        session[time_key] = datetime.now()
                else:
                    session[time_key] = None

            # TODO: record user_id
            session_model = BugFixerSession(**session)
            return computation_dao.insert_bug_fixer_session(session_model)
        except Exception as e:
            logger.error(f"Failed to record bug fixer session: {e}")
            raise e

    def list_bug_fixer_sessions(self, retry_process_id: str) -> List[BugFixerSession]:
        """
        List all bug fixer sessions for a given retry process ID.

        :param retry_process_id: The ID of the retry process to list sessions for.
        :return: A list of BugFixerSession instances.
        """
        try:
            return computation_dao.find_bug_fixer_sessions_by_retry_process_id(retry_process_id)
        except Exception as e:
            logger.error(f"Failed to list bug fixer sessions: {e}")
            raise e

    def create_computation(self, attrs: dict) -> Computation:
        """
        Create a new computation with flexible attributes.
        
        :param attrs: Dictionary of computation attributes
        :return: Created Computation instance
        """
        try:
            computation = Computation()
            # Map camelCase to snake_case for known fields
            field_mapping = {
                'computationParams': 'computation_params',
                'startTime': 'start_time',
                'computationState': 'computation_state',
                'nodeId': 'node_id',
                'sourceDataIds': 'source_data_ids',
                'resultDataId': 'result_data_id',
                'functionBlockId': 'function_block_id',
                'functionBlockVersionId': 'function_block_version_id',
                'taskId': 'task_id',
                'errorDescription': 'error_description',
                'jobIdent': 'job_ident',
                'optimizedErrorDescription': 'optimized_error_description',
                'systemEnv': 'system_env',
                'computationResourceConfigure': 'computation_resource_configure',
                'previousComputationId': 'previous_computation_id',
                'retryProcessId': 'retry_process_id'
            }
            
            for key, value in attrs.items():
                # Convert camelCase to snake_case
                attr_name = field_mapping.get(key, key)
                if hasattr(computation, attr_name):
                    setattr(computation, attr_name, value)
            
            computation_dao.insert(computation)
            return computation
        except Exception as e:
            logger.error(f"Failed to create computation: {e}")
            raise e

    def update_computation(self, computation_id: str, attrs: dict) -> Computation:
        """
        Update a computation with flexible attributes.
        
        :param computation_id: ID of the computation to update
        :param attrs: Dictionary of attributes to update
        :return: Updated Computation instance
        """
        try:
            # Map camelCase to snake_case for known fields
            field_mapping = {
                'computationParams': 'computation_params',
                'startTime': 'start_time',
                'computationState': 'computation_state',
                'nodeId': 'node_id',
                'sourceDataIds': 'source_data_ids',
                'resultDataId': 'result_data_id',
                'functionBlockId': 'function_block_id',
                'functionBlockVersionId': 'function_block_version_id',
                'taskId': 'task_id',
                'errorDescription': 'error_description',
                'jobIdent': 'job_ident',
                'optimizedErrorDescription': 'optimized_error_description',
                'systemEnv': 'system_env',
                'computationResourceConfigure': 'computation_resource_configure',
                'previousComputationId': 'previous_computation_id',
                'retryProcessId': 'retry_process_id',
                'duration': 'duration'
            }
            
            update_attrs = {}
            for key, value in attrs.items():
                # Convert camelCase to snake_case
                attr_name = field_mapping.get(key, key)
                update_attrs[attr_name] = value
            
            computation_dao.update(computation_id, update_attrs)
            computation = computation_dao.find(computation_id)
            return computation
        except Exception as e:
            logger.error(f"Failed to update computation: {e}")
            raise e

    def save_fix_description(self, computation_id: int, error_info: str, fix_strategy: str) -> FixDescription:
        """
        Save fix description for a computation.
        
        :param computation_id: The ID of the computation
        :param error_info: The error information (stack trace or error message)
        :param fix_strategy: The fix strategy explanation
        :return: Created FixDescription instance
        """
        try:
            fix_description = FixDescription(
                computation_id=computation_id,
                error_info=error_info,
                fix_strategy=fix_strategy
            )
            return computation_dao.insert_fix_description(fix_description)
        except Exception as e:
            logger.error(f"Failed to save fix description: {e}")
            raise e

    def get_fix_descriptions(self, computation_id: int) -> List[FixDescription]:
        """
        Get all fix descriptions for a computation.
        
        :param computation_id: The ID of the computation
        :return: List of FixDescription instances
        """
        try:
            return computation_dao.find_fix_descriptions_by_computation_id(computation_id)
        except Exception as e:
            logger.error(f"Failed to get fix descriptions: {e}")
            raise e
        
    def get_computation_pipe(self, node_id: str) -> List[dict]:
        previous_edges = edge_dao.find_all_front_edges(node_id)
        previous_edges.reverse()
        previous_node_ids = [edge.source_node_id for edge in previous_edges]
        result = []
        for previous_node_id in previous_node_ids:
            previous_node = node_dao.find_by_id(previous_node_id)
            if previous_node is None or previous_node.type is None:
                continue
            if previous_node.type.startswith("data node"):
                result.append(f"""
Node ID: {previous_node_id}
Type: Data Node

========
""")
                continue
            porter = PorterFactory.create_porter()
            porter.set_operation_target(f"function-block-version/{previous_node.function_block_version_id}/")
            file_list = porter.list_files(recursive=True)
            node_block = f"""
Node ID: {previous_node_id}
Type: {previous_node.type}
Files:
"""
            for file_key in file_list:
                file_suffix = file_key.split(".")[-1]
                if file_suffix.lower() in ["json", "py", "r" , "sh", "txt"]:
                    logger.warning(f"file_key: {file_key}")
                    porter.set_operation_target(file_key)
                    file_info = porter.get_file_info()
                    description = None
                    if file_info.get("Size", 0) > 100 * 1024:
                        description = f"--- {file_key} ---\n[File too large to display, {file_info.get('Size')} bytes]\n"
                        continue
                    file_text = porter.fetch_file_text()
                    description = f"--- {file_key} ---\n{file_text}\n"
                    logger.warning(f"description: {description}")
                    node_block += description
                else:
                    node_block += f"--- {file_key} ---\n[Binary file, {file_suffix}]\n"
            node_block += "\n=========\n"
            result.append(node_block)

        return result

    def save_job_reviewer_messages(self, computation_id, uuid_str, messages):
        """
        Save job reviewer messages to S3
        
        Args:
            computation_id: The computation ID
            uuid_str: UUID for this message record
            messages: List of message dictionaries
            
        Returns:
            The S3 object key where messages were saved
        """
        import time
        timestamp = int(time.time())
        
        # Create object key: job-reviewer-messages/{computation_id}/uuid-{timestamp}.json
        object_key = f"job-reviewer-messages/{computation_id}/{uuid_str}-{timestamp}.json"
        
        # Convert messages to JSON
        messages_json = json.dumps(messages, indent=2, ensure_ascii=False)
        
        # Upload to S3 using porter
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        porter.save_file_text(messages_json)
        
        logger.info(f"Saved job reviewer messages to S3: {object_key}")
        return object_key
    
    def save_job_reviewer_report(self, computation_id, uuid_str, raw_report, structured_report):
        """
        Save job reviewer report to S3
        
        Args:
            computation_id: The computation ID
            uuid_str: UUID for this report record
            report: Report dictionary
            
        Returns:
            The S3 object key where the report was saved
        """
        import time
        timestamp = int(time.time())
        
        # Create object key: job-reviewer-reports/{computation_id}/uuid-{timestamp}.json
        object_key = f"job-reviewer-reports/{computation_id}/{uuid_str}-{timestamp}.json"

        report = {
            "raw_report": raw_report,
            "structured_report": structured_report
        }
        
        # Convert report to JSON
        report_json = json.dumps(report, indent=2, ensure_ascii=False)
        
        # Upload to S3 using porter
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        porter.save_file_text(report_json)
        
        logger.info(f"Saved job reviewer report to S3: {object_key}")
        return object_key
    
    def get_job_reviewer_error(self, computation_id):
        """
        Retrieve job reviewer error log from S3
        
        Args:
            computation_id: The computation ID
            
        Returns:
            The content of the review output log, or a default message if not found
        """
        computation_waiter = ComputationWaiter(computation_id)
        return computation_waiter.get_review_error()
    
    def list_job_reviewer_reports(self, computation_id):
        """
        List all job reviewer reports for a computation
        
        Args:
            computation_id: The computation ID
            
        Returns:
            List of report metadata (uuid, timestamp, object_key)
        """
        prefix = f"job-reviewer-reports/{computation_id}/"
        
        porter = PorterFactory.create_porter()
        porter.set_operation_target(prefix)
        
        # List all objects with this prefix (recursive to get all files)
        keys = porter.list_files(recursive=True)
        
        reports = []
        for key in keys:
            if key.endswith('.json'):
                # Extract uuid and timestamp from filename
                # Format: job-reviewer-reports/{computation_id}/{uuid}-{timestamp}.json
                filename = key.split('/')[-1]
                if filename.endswith('.json'):
                    filename_no_ext = filename[:-5]  # Remove .json
                    parts = filename_no_ext.rsplit('-', 1)
                    if len(parts) == 2:
                        uuid_str, timestamp = parts
                        reports.append({
                            "uuid": uuid_str,
                            "timestamp": int(timestamp),
                            "object_key": key,
                            "computation_id": computation_id
                        })
        
        # Sort by timestamp descending (newest first)
        reports.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return reports
    
    def get_job_reviewer_messages(self, computation_id, uuid_str):
        """
        Get job reviewer messages for a specific report
        
        Args:
            computation_id: The computation ID
            uuid_str: The UUID of the message record
            
        Returns:
            The messages content as dict, or None if not found
        """
        # Find the messages file matching the uuid
        prefix = f"job-reviewer-messages/{computation_id}/"
        
        porter = PorterFactory.create_porter()
        porter.set_operation_target(prefix)
        
        # List all files with this prefix (recursive to get all files)
        keys = porter.list_files(recursive=True)
        
        # Find matching key (uuid-{timestamp}.json)
        matching_key = None
        for key in keys:
            filename = key.split('/')[-1]
            if filename.startswith(f"{uuid_str}-") and filename.endswith('.json'):
                matching_key = key
                break
        
        if not matching_key:
            logger.warning(f"No messages found for computation {computation_id}, uuid {uuid_str}")
            return None
        
        # Read the file
        porter.set_operation_target(matching_key)
        content = porter.fetch_file_text()
        
        if content:
            return json.loads(content)
        
        return None
    
    def get_job_reviewer_report(self, computation_id, uuid_str):
        """
        Get job reviewer report for a specific report
        
        Args:
            computation_id: The computation ID
            uuid_str: The UUID of the report
            
        Returns:
            The report content as dict, or None if not found
        """
        # Find the report file matching the uuid
        prefix = f"job-reviewer-reports/{computation_id}/"
        
        porter = PorterFactory.create_porter()
        porter.set_operation_target(prefix)
        
        # List all files with this prefix (recursive to get all files)
        keys = porter.list_files(recursive=True)
        
        # Find matching key (uuid-{timestamp}.json)
        matching_key = None
        for key in keys:
            filename = key.split('/')[-1]
            if filename.startswith(f"{uuid_str}-") and filename.endswith('.json'):
                matching_key = key
                break
        
        if not matching_key:
            logger.warning(f"No report found for computation {computation_id}, uuid {uuid_str}")
            return None
        
        # Read the file
        porter.set_operation_target(matching_key)
        content = porter.fetch_file_text()
        
        if content:
            return json.loads(content)
        
        return None

    def save_programming_agent_messages(self, computation_id, uuid_str, messages):
        """
        Save programming agent messages to S3
        
        Args:
            computation_id: The computation ID
            uuid_str: UUID for this message record
            messages: List of message dictionaries
            
        Returns:
            The S3 object key where messages were saved
        """
        import time
        timestamp = int(time.time())
        
        # Create object key: programming-agent-messages/{computation_id}/uuid-{timestamp}.json
        object_key = f"programming-agent-messages/{computation_id}/{uuid_str}-{timestamp}.json"
        
        # Convert messages to JSON
        messages_json = json.dumps(messages, indent=2, ensure_ascii=False)
        
        # Upload to S3 using porter
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        porter.save_file_text(messages_json)
        
        logger.info(f"Saved programming agent messages to S3: {object_key}")
        return object_key

    def get_programming_agent_messages(self, computation_id, page=1, page_size=20):
        """
        Get programming agent messages for a computation with pagination
        
        Args:
            computation_id: The computation ID
            page: Page number (1-indexed)
            page_size: Number of messages per page
            
        Returns:
            Dict with messages list and pagination info
        """
        prefix = f"programming-agent-messages/{computation_id}/"
        
        porter = PorterFactory.create_porter()
        porter.set_operation_target(prefix)
        
        # List all objects with this prefix
        keys = porter.list_files(recursive=True)
        
        # Parse and sort message files by timestamp (newest first)
        message_files = []
        for key in keys:
            if key.endswith('.json'):
                filename = key.split('/')[-1]
                if filename.endswith('.json'):
                    filename_no_ext = filename[:-5]  # Remove .json
                    parts = filename_no_ext.rsplit('-', 1)
                    if len(parts) == 2:
                        uuid_str, timestamp = parts
                        try:
                            message_files.append({
                                "uuid": uuid_str,
                                "timestamp": int(timestamp),
                                "object_key": key
                            })
                        except ValueError:
                            logger.warning(f"Invalid timestamp in filename: {filename}")
        
        # Sort by timestamp descending (newest first)
        message_files.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Calculate pagination
        total_count = len(message_files)
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Get the page of message files
        page_files = message_files[start_idx:end_idx]
        
        # Load messages content for this page
        messages_list = []
        for file_info in page_files:
            porter.set_operation_target(file_info['object_key'])
            content = porter.fetch_file_text()
            if content:
                try:
                    messages_data = json.loads(content)
                    messages_list.append({
                        "uuid": file_info['uuid'],
                        "timestamp": file_info['timestamp'],
                        "messages": messages_data
                    })
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from {file_info['object_key']}: {e}")
        
        return {
            "data": messages_list,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_more": page < total_pages
            }
        }

    def save_visualizer_agent_messages(self, computation_id, uuid_str, messages):
        """
        Save visualizer agent messages to S3
        
        Args:
            computation_id: The computation ID
            uuid_str: UUID for this message record
            messages: List of message dictionaries
            
        Returns:
            The S3 object key where messages were saved
        """
        import time
        timestamp = int(time.time())
        
        # Create object key: visualizer-agent-messages/{computation_id}/uuid-{timestamp}.json
        object_key = f"visualizer-agent-messages/{computation_id}/{uuid_str}-{timestamp}.json"
        
        # Convert messages to JSON
        messages_json = json.dumps(messages, indent=2, ensure_ascii=False)
        
        # Upload to S3 using porter
        porter = PorterFactory.create_porter()
        porter.set_operation_target(object_key)
        porter.save_file_text(messages_json)
        
        logger.info(f"Saved visualizer agent messages to S3: {object_key}")
        return object_key

    def get_visualizer_agent_messages(self, computation_id, uuid_str):
        """
        Get visualizer agent messages for a specific record
        
        Args:
            computation_id: The computation ID
            uuid_str: The UUID of the message record
            
        Returns:
            The messages content as list, or None if not found
        """
        # Find the messages file matching the uuid
        prefix = f"visualizer-agent-messages/{computation_id}/"
        
        porter = PorterFactory.create_porter()
        porter.set_operation_target(prefix)
        
        # List all files with this prefix (recursive to get all files)
        keys = porter.list_files(recursive=True)
        
        # Find matching key (uuid-{timestamp}.json)
        matching_key = None
        for key in keys:
            filename = key.split('/')[-1]
            if filename.startswith(f"{uuid_str}-") and filename.endswith('.json'):
                matching_key = key
                break
        
        if not matching_key:
            logger.warning(f"No messages found for computation {computation_id}, uuid {uuid_str}")
            return None
        
        # Read the file
        porter.set_operation_target(matching_key)
        content = porter.fetch_file_text()
        
        if content:
            return json.loads(content)
        
        return None

computation_service = ComputationService()

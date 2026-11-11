from dao.computation import computation_dao
from dao.node import node_dao
from dao.edge import edge_dao
from sss.porter_factory import PorterFactory
from log.logger_factory import LoggerFactory
from typing import Dict, Any, List, Optional
import mimetypes
import requests
import os
import json
import subprocess
import tempfile

MAIN_SERVER_HOST = os.getenv("MAIN_SERVER_HOST")

logger = LoggerFactory.get_logger("InputsService")


class InputsService:
    def get_inputs_structure(self, node_id: str) -> Dict[str, Any]:
        """
        Get inputs directory structure for a node.
        Mimics the input-staging logic of the computation job runner.
        Returns a hierarchical structure similar to AutoGenieAgent's expected format.
        """
        try:
            # Get branch path to find all previous nodes
            branch_path = self._get_branch_path_from_data_server(node_id)
            branch_nodes = branch_path.get("previousNodeList", [])

            # Build directory structure
            structure = {
                "name": "inputs",
                "type": "directory",
                "children": []
            }

            index = 1
            total_nodes = len(branch_nodes)
            for target_node in branch_nodes:
                target_node_id = target_node.get("id")
                target_data_id = None

                if target_node.get("type").startswith("data node"):
                    target_data_id = target_node.get("dataId")
                else:
                    # Get latest computation result data id
                    latest_computation = computation_dao.find_latest_by_node_id(target_node_id)
                    if latest_computation:
                        target_data_id = latest_computation.result_data_id

                if target_data_id:
                    # Scan the data directory in S3
                    # Mark the last node as the most direct input
                    if index == total_nodes:
                        node_dir_name = f"node_{index} (Direct Input)"
                    else:
                        node_dir_name = f"node_{index}"
                    source_data_prefix = f"adata/{target_data_id}-general-s3-store/"

                    node_structure = self._scan_s3_directory(
                        source_data_prefix, node_dir_name, target_node_id)
                    structure["children"].append(node_structure)

                index += 1

            return structure

        except Exception as e:
            raise e

    def _scan_s3_directory(self, s3_prefix: str, dir_name: str, node_id: str) -> Dict[str, Any]:
        """
        Recursively scan S3 directory and build hierarchical structure
        """
        porter = PorterFactory.create_porter()
        porter.set_operation_target(s3_prefix)

        try:
            # List objects in this prefix
            object_keys = porter.list_files(recursive=True, max_keys=10000)

            # Build tree structure
            root = {
                "name": dir_name,
                "type": "directory",
                "path": dir_name,
                "node_id": node_id,
                "children": []
            }

            # Create a tree from flat list of object keys
            tree_dict = {}
            for object_key in object_keys:
                # Get relative path (remove prefix)
                if object_key.startswith(s3_prefix):
                    relative_path = object_key[len(s3_prefix):]
                else:
                    relative_path = object_key

                if not relative_path or relative_path == '':
                    continue

                # Build path hierarchy
                parts = relative_path.split('/')
                current_path = dir_name

                for i, part in enumerate(parts):
                    if not part:
                        continue

                    parent_path = current_path
                    current_path = f"{current_path}/{part}" if current_path else part

                    if current_path not in tree_dict:
                        is_file = (i == len(parts) - 1)
                        node_data = {
                            "name": part,
                            "type": "file" if is_file else "directory",
                            "path": current_path,
                            "node_id": node_id,
                            "object_key": object_key if is_file else None
                        }

                        if is_file:
                            # Get file metadata
                            try:
                                head = porter.get_head(object_key)
                                node_data["size"] = head.get("ContentLength", 0)
                            except:
                                node_data["size"] = 0
                        else:
                            node_data["children"] = []

                        tree_dict[current_path] = {
                            "data": node_data,
                            "parent_path": parent_path
                        }

            # Build tree from dict
            for path, node_info in tree_dict.items():
                parent_path = node_info["parent_path"]
                if parent_path == dir_name:
                    root["children"].append(node_info["data"])
                elif parent_path in tree_dict:
                    parent_node = tree_dict[parent_path]["data"]
                    if "children" in parent_node:
                        parent_node["children"].append(node_info["data"])

            return root

        except Exception as e:
            logger.error(f"Error scanning S3 directory {s3_prefix}: {str(e)}")
            return {
                "name": dir_name,
                "type": "directory",
                "path": dir_name,
                "node_id": node_id,
                "children": [],
                "error": str(e)
            }

    def get_file_content(self, node_id: str, relative_path: str) -> Dict[str, Any]:
        """
        Get file content from inputs directory using file_resolver.

        Args:
            node_id: The node ID
            relative_path: Path relative to inputs folder (e.g., "inputs/node_1/data.csv")

        Returns:
            Dict with file content or file info for binary files
        """
        try:
            # Parse relative path to extract node directory and file path
            # Format: inputs/node_X/...
            parts = relative_path.split('/')
            if len(parts) < 3 or parts[0] != 'inputs' or not parts[1].startswith('node_'):
                return {"error": "Invalid relative path format. Expected: inputs/node_X/..."}
            
            node_index = parts[1][5:]  # Extract X from node_X
            if not node_index.isdigit():
                return {"error": "Invalid node directory in path."}
            node_index = int(node_index)
            
            # Get branch path to find corresponding node ID
            branch_path = self._get_branch_path_from_data_server(node_id)
            branch_nodes = branch_path.get("previousNodeList", [])
            if node_index < 1 or node_index > len(branch_nodes):
                return {"error": f"Node index {node_index} out of range."}
            
            target_node = branch_nodes[node_index - 1]
            target_node_id = target_node.get("id")
            if not target_node_id:
                return {"error": f"No ID found for target node at index {node_index}"}

            if target_node.get("type").startswith("data node"):
                target_data_id = target_node.get("dataId")
                if not target_data_id:
                    return {"error": f"No data ID found for data node {target_node_id}"}
                result_data_id = target_data_id
            else:
                # Get the latest computation result_data_id for this node
                latest_computation = computation_dao.find_latest_by_node_id(target_node_id)
                if not latest_computation or not latest_computation.result_data_id:
                    return {"error": f"No result data found for node {target_node_id}"}
                result_data_id = latest_computation.result_data_id

            # Remove "inputs/node_X/" prefix and construct object key
            remaining_path = '/'.join(parts[2:])
            object_key = f"adata/{result_data_id}-general-s3-store/{remaining_path}"

            # Get file from S3
            porter = PorterFactory.create_porter()
            porter.set_operation_target(object_key)

            # Check if file exists
            if not porter.check_file():
                return {"error": f"File not found: {relative_path}"}

            # Get file metadata
            try:
                head = porter.get_head(object_key)
                content_type = head.get("ContentType", "")
                file_size = head.get("ContentLength", 0)
                last_modified = head.get("LastModified")
            except Exception as e:
                logger.error(f"Error getting file head: {str(e)}")
                return {"error": f"Error getting file info: {str(e)}"}

            file_name = parts[-1]
            
            # Download file to temporary location for processing with file_resolver
            temp_file = None
            try:
                # Create a temporary file with the same extension
                file_ext = os.path.splitext(file_name)[1]
                temp_file = tempfile.NamedTemporaryFile(
                    mode='wb', 
                    suffix=file_ext, 
                    delete=False
                )
                temp_file_path = temp_file.name
                temp_file.close()
                
                # Download file from S3 to temp location
                logger.info(f"Downloading file {object_key} to {temp_file_path}")
                porter.fetch_file(temp_file_path)
                
                # Use file_resolver to parse the file
                resolver_output = self._call_file_resolver(temp_file_path)
                
                # Build response with resolver output
                return {
                    "type": "resolved",
                    "content": resolver_output,
                    "info": {
                        "filename": file_name,
                        "size": file_size,
                        "size_readable": self._format_size(file_size),
                        "content_type": content_type,
                        "last_modified": str(last_modified) if last_modified else None,
                        "path": relative_path
                    }
                }
                
            except Exception as e:
                logger.error(f"Error processing file with file_resolver: {str(e)}")
                return {
                    "type": "error",
                    "error": f"Error processing file: {str(e)}",
                    "info": {
                        "filename": file_name,
                        "size": file_size,
                        "size_readable": self._format_size(file_size),
                        "content_type": content_type,
                        "last_modified": str(last_modified) if last_modified else None,
                        "path": relative_path
                    }
                }
            finally:
                # Clean up temporary file
                if temp_file and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                        logger.info(f"Cleaned up temporary file: {temp_file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up temporary file: {str(e)}")

        except Exception as e:
            logger.error(f"Error getting file content: {str(e)}")
            return {"error": f"Error reading file: {str(e)}"}

    def _call_file_resolver(self, file_path: str) -> str:
        """
        Call file_resolver script to parse file content.
        
        Args:
            file_path: Absolute path to the file
            
        Returns:
            String output from file_resolver
        """
        try:
            # Runs: <FILE_RESOLVER_PYTHON> index.py <absolute-file-path> inside FILE_RESOLVER_DIR
            resolver_dir = os.environ.get("FILE_RESOLVER_DIR", "/omicairn/code_space/file_resolver")
            resolver_python = os.environ.get("FILE_RESOLVER_PYTHON", "/omicairn/venvs/file_resolver_env/bin/python3")
            cmd = [resolver_python, "index.py", file_path]
            
            logger.info(f"Calling file_resolver with command: {cmd}")
            
            result = subprocess.run(
                cmd,
                cwd=resolver_dir,
                shell=False,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                logger.error(f"file_resolver failed with return code {result.returncode}: {error_msg}")
                return f"Error running file_resolver:\n{error_msg}\n\nStdout:\n{result.stdout}"
                
        except subprocess.TimeoutExpired:
            logger.error("file_resolver timed out after 60 seconds")
            return "Error: File processing timed out (60 seconds)"
        except Exception as e:
            logger.error(f"Error calling file_resolver: {str(e)}")
            return f"Error calling file_resolver: {str(e)}"

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def _get_branch_path_from_data_server(self, node_id: str) -> Dict[str, Any]:
        """Get branch path from the main (backend) server"""
        try:
            response = requests.get(
                f"http://{MAIN_SERVER_HOST}/server/node/get-previous-path?node_id={node_id}&with_self=1",
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 200:
                return result.get('data', {})
            else:
                logger.error(f"Failed to get branch path: {result.get('message')}")
                return {}
        except Exception as e:
            logger.error(f"Error calling data server for branch path: {str(e)}")
            # Fallback to local implementation
            return {
                "previousNodeList": [],
                "previousEdgeList": []
            }


inputs_service = InputsService()

import os
import uuid
from datetime import datetime
from typing import List, Dict, Any
from sss.porter_factory import PorterFactory
from log.logger_factory import logger_factory
import io

logger = logger_factory.create_logger(__name__)


class FileManagementService:
    def __init__(self):
        self.porter = PorterFactory.create_porter()

    def list_files(self, analysis_id: str, s3_prefix: str) -> List[Dict[str, Any]]:
        try:
            prefix = s3_prefix.split('/')[-1] if s3_prefix else ''
            if prefix and not prefix.endswith('/'):
                prefix += '/'
            target_prefix = f"v3-chat-workspace/{analysis_id}/{prefix}"
            self.porter.set_operation_target(target_prefix)
            object_keys = self.porter.list_files(recursive=True)
            files = []
            for object_key in object_keys:
                try:
                    self.porter.set_operation_target(object_key)
                    file_info = self.porter.get_file_info()
                    file_name = object_key.split('/')[-1]

                    size_bytes = file_info.get('Size', 0)
                    size_str = self._format_file_size(size_bytes) if size_bytes else None

                    last_modified = file_info.get('LastModified')
                    last_modified_str = last_modified.strftime('%Y-%m-%d %H:%M:%S') if last_modified else None

                    files.append({
                        'id': object_key,
                        'name': file_name,
                        'size': size_str,
                        'lastModified': last_modified_str
                    })
                except Exception as inner_e:
                    logger.warning(f"Error getting info for file {object_key}: {inner_e}")
                    continue
            return files

        except Exception as e:
            logger.error(f"Error listing files for analysis {analysis_id}: {e}")
            raise e

    def delete_file_by_id(self, file_id: str) -> bool:
        try:
            self.porter.set_operation_target(file_id)
            self.porter.remove_file()
            return True

        except Exception as e:
            raise e

    def upload_file(self, analysis_id: str, file_stream, file_name: str) -> Dict[str, Any]:
        """Upload file to S3 workspace for analysis"""
        try:
            file_key = f"v3-chat-workspace/{analysis_id}/{file_name}"
            self.porter.set_operation_target(file_key)

            self.porter.save_file_stream(file_stream)

            file_info = self.porter.get_file_info()
            size_bytes = file_info.get('Size', 0)
            size_str = self._format_file_size(size_bytes) if size_bytes else None

            last_modified = file_info.get('LastModified')
            last_modified_str = last_modified.strftime('%Y-%m-%d %H:%M:%S') if last_modified else None

            return {
                'id': file_key,
                'name': file_name,
                'size': size_str,
                'lastModified': last_modified_str
            }

        except Exception as e:
            logger.error(f"Error uploading file {file_name} for analysis {analysis_id}: {e}")
            raise e

    def read_file_content(self, file_key: str, analysis_id: str) -> bytes:
        """Read file content from S3 by file key"""
        try:
            file_key = file_key.split('/')[-1] if '/' in file_key else file_key
            workspace_prefix = f"v3-chat-workspace/{analysis_id}/" if analysis_id else ''
            file_path = f"{workspace_prefix}{file_key}"
            
            self.porter.set_operation_target(file_path)
            
            file_exists = self.porter.check_file()
            if not file_exists:
                logger.error(f"File does not exist in S3: {file_path}")
                raise FileNotFoundError(f"File not found in S3: {file_path}")
            
            content = self.porter.fetch_file_stream()
            return content
            
        except Exception as e:
            logger.error(f"Error reading file content for {file_key}: {e}")
            logger.error(f"Bucket: {self.porter.get_bucket_name()}, Object key: {file_path if 'file_path' in locals() else file_key}")
            raise e

    def _format_file_size(self, bytes_size: int) -> str:
        """Format file size in human readable format"""
        if bytes_size == 0:
            return "0 Bytes"

        size_names = ["Bytes", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(bytes_size, 1024)))
        p = math.pow(1024, i)
        s = round(bytes_size / p, 2)
        return f"{s} {size_names[i]}"


    def copy_file(self, file_name: str, source_key: str, destination_key: str) -> bool:
        try:
            self.porter.set_operation_target(source_key)
            if not self.porter.check_file():
                logger.error(f"Source file does not exist in S3: {source_key}")
                raise FileNotFoundError(f"Source file not found in S3: {source_key}")

            if destination_key.endswith('/'):
                if not file_name:
                    logger.error("file_name is required when destination_key is a directory")
                    raise ValueError("file_name is required when destination_key is a directory")
                destination_key = os.path.join(destination_key, f"copy_{file_name}")

            self.porter.set_operation_target(destination_key)
            if self.porter.check_file():
                logger.error(f"Destination file already exists in S3: {destination_key}")
                raise FileExistsError(f"Destination file already exists in S3: {destination_key}")

            self.porter.set_operation_target(source_key)
            content = self.porter.fetch_file_stream()
            
            if isinstance(content, (bytes, bytearray)):
                stream = io.BytesIO(content)
            else:
                stream = content

            self.porter.set_operation_target(destination_key)
            self.porter.save_file_stream(stream)

            return destination_key

        except Exception as e:
            logger.error(f"Error copying file from {source_key} to {destination_key}: {e}")
            raise e
        
    def rename_file(self, source_key: str, new_name: str) -> bool:
        try:
            self.porter.set_operation_target(source_key)
            if not self.porter.check_file():
                logger.error(f"Source file does not exist in S3: {source_key}")
                raise FileNotFoundError(f"Source file not found in S3: {source_key}")

            base_path = '/'.join(source_key.split('/')[:-1])
            destination_key = f"{base_path}/{new_name}"

            self.porter.set_operation_target(destination_key)
            if self.porter.check_file():
                logger.error(f"Destination file already exists in S3: {destination_key}")
                raise FileExistsError(f"Destination file already exists in S3: {destination_key}")

            self.porter.set_operation_target(source_key)
            content = self.porter.fetch_file_stream()
            
            if isinstance(content, (bytes, bytearray)):
                stream = io.BytesIO(content)
            else:
                stream = content

            self.porter.set_operation_target(destination_key)
            self.porter.save_file_stream(stream)

            self.porter.set_operation_target(source_key)
            self.porter.remove_file()

            return True

        except Exception as e:
            logger.error(f"Error renaming file from {source_key} to {new_name}: {e}")
            raise e
        
    def check_folder_exist(self, folder_key: str) -> bool:
        """Check if a folder exists by looking for objects with the folder path as prefix"""
        try:
            if not folder_key.endswith('/'):
                folder_key += '/'
            
            self.porter.set_operation_target(folder_key)
            object_keys = self.porter.list_files(max_keys=1, recursive=True)
            
            return len(object_keys) > 0
            
        except Exception as e:
            logger.error(f"Error checking existence of folder {folder_key}: {e}")
            raise e
        
file_management_service = FileManagementService()
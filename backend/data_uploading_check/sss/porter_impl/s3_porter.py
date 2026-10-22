from concurrent.futures import ThreadPoolExecutor
import io
import os
import boto3
from botocore.client import Config, ClientError
from exception.sss.copy_file import SSSCopyFileException
from exception.sss.fetch_file import SSSFetchFileException
from exception.sss.remove_file import SSSRemoveFileException
from exception.sss.upload_file import SSSUploadFileException

from sss.porter import Porter
from constants import BUCKET_NAME
from log.logger_factory import logger_factory

logger = logger_factory.create_logger(__name__)


class S3Porter(Porter):
    def __init__(self) -> None:
        self.client = None
        self._create_client()
        self.headers = None
        self.object_key = None
        self.bucket_name = BUCKET_NAME

    def _create_client(self):
        self.client = boto3.client(
            's3',
            region_name=os.environ.get('AWS_REGION'),
            endpoint_url=os.environ.get('S3_ENDPOINT_URL') or None
        )

    def get_bucket_name(self):
        return self.bucket_name

    def get_object_key(self):
        return self.object_key

    def set_headers(self, headers):
        self.headers = headers

    def set_operation_target(self, object_key):
        self.object_key = object_key

    # def save_file(self, file_path):
    #     file_size = os.path.getsize(file_path)
    #     if file_size < 100 * 1024 * 1024:
    #         return self._save_normal_size_file(file_path)
    #     else:
    #         return self._save_large_size_file(file_path, file_size)
    def save_file(self, file_path):
        try:
            upload_response = self.client.upload_file(
                Filename=file_path,
                Bucket=self.bucket_name,
                Key=self.object_key
            )
            return upload_response
        except ClientError as e:
            logger.error(e)
            raise SSSUploadFileException(f"upload unsuccessfully.")

    def save_file_text(self, text):
        try:
            upload_response = self.client.upload_fileobj(
                Bucket=self.bucket_name,
                Key=self.object_key,
                Fileobj=io.BytesIO(text.encode('utf-8'))
            )
            return upload_response
        except ClientError as e:
            logger.error(e)
            raise SSSUploadFileException(f"text upload unsuccessfully.")

    def save_file_stream(self, file_stream):
        try:
            upload_response = self.client.upload_fileobj(
                Bucket=self.bucket_name,
                Key=self.object_key,
                Fileobj=file_stream
            )
            return upload_response
        except ClientError as e:
            logger.error(
                f"upload unsuccessfully. object key: {self.object_key}, bucket name: {self.bucket_name}")
            logger.error(e)
            raise SSSUploadFileException(f"stream upload unsuccessfully.")

    def fetch_file(self, file_path):
        try:
            download_response = self.client.download_file(
                Bucket=self.bucket_name,
                Key=self.object_key,
                Filename=file_path
            )
            return download_response
        except ClientError as e:
            logger.error(e)
            raise SSSFetchFileException(f"download unsuccessfully.")

    def fetch_file_stream(self):
        try:
            buffer = io.BytesIO()
            download_response = self.client.download_fileobj(
                Bucket=self.bucket_name,
                Key=self.object_key,
                Fileobj=buffer
            )
            buffer.seek(0)
            return buffer.read()
        except ClientError as e:
            logger.error(e)
            raise SSSFetchFileException(f"download stream unsuccessfully.")

    def check_file(self):
        try:
            check_response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=self.object_key
            )
            return True
        except ClientError as e:
            return False

    def remove_file(self):
        try:
            remove_response = self.client.delete_object(
                Bucket=self.bucket_name,
                Key=self.object_key
            )
            return remove_response
        except ClientError as e:
            logger.error(e)
            raise SSSRemoveFileException(f"remove unsuccessfully.")

    def copy_file(self, source_bucket_name, source_object_key):
        try:
            copy_response = self.client.copy_object(
                Bucket=self.bucket_name,
                Key=self.object_key,
                CopySource={
                    'Bucket': source_bucket_name,
                    'Key': source_object_key
                }
            )
            return copy_response
        except ClientError as e:
            logger.error(e)
            raise SSSCopyFileException(f"copy unsuccessfully.")

    def list_files(self, start_after: str='', max_keys: int=1000, recursive=False):
        try:
            if recursive:
                list_response = self.client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=self.object_key,
                    MaxKeys=max_keys,
                    StartAfter=start_after
                )
                object_list = [item["Key"] for item in list_response.get('Contents', [])]
                return object_list
            else:
                list_response = self.client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=self.object_key,
                    Delimiter='/',
                    MaxKeys=max_keys,
                    StartAfter=start_after
                )
                object_list = [item["Prefix"] for item in list_response.get('CommonPrefixes', [])] + [item["Key"] for item in list_response.get("Contents", [])]
                return object_list
        except ClientError as e:
            logger.error(e)
            raise SSSCopyFileException(f"list unsuccessfully.")

    def get_head(self, object_key = None):
        if object_key is None:
            object_key = self.object_key
        try:
            head_response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return head_response
        except ClientError as e:
            logger.error(e)
            raise SSSCopyFileException(f"get head unsuccessfully.")

    def update_metadata(self, object_key, metadata):
        try:
            exists_metadata = self.get_head(object_key)["Metadata"]
            for key, value in metadata.items():
                exists_metadata[key] = value
            metadata_response = self.client.copy_object(
                Bucket=self.bucket_name,
                Key=object_key,
                CopySource={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                Metadata=exists_metadata,
                MetadataDirective='REPLACE'
            )
            return metadata_response
        except ClientError as e:
            logger.error(e)
            raise SSSCopyFileException(f"update metadata unsuccessfully.")

    def get_file_info(self):
        try:
            head_response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=self.object_key
            )
            return {
                'Size': head_response['ContentLength'],
                'LastModified': head_response['LastModified'],
                'ContentType': head_response['ContentType'],
            }
        except ClientError as e:
            logger.error(e)
            raise SSSFetchFileException(f"remove unsuccessfully.")

    def get_presigned_url(self, expiration):
        try:
            presigned_url = self.client.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': self.object_key
                },
                ExpiresIn=expiration
            )
            return presigned_url
        except ClientError as e:
            logger.error(e)
            raise SSSFetchFileException(f"generate presigned url unsuccessfully.")

    def get_presigned_post(self, file_size, expiration, fields=None):
        # multipart if file size > 300MB
        if file_size > 300 * 1024 * 1024:
            return self.get_multipart_upload_presigned_url(file_size, expiration)
        else:
            try:
                conditions = []
                presigned_url = self.client.generate_presigned_post(
                    Bucket=self.bucket_name,
                    Key=self.object_key,
                    Fields=fields,
                    Conditions=conditions,
                    ExpiresIn=expiration
                )
                return {
                    'object_key': self.object_key,
                    'presigned_url': presigned_url,
                    'multipart': False
                }
            except ClientError as e:
                logger.error(e)
                raise SSSFetchFileException(f"generate presigned post unsuccessfully.")

    def get_multipart_upload_presigned_url(self, file_size, expiration):
        file_size = int(file_size)
        upload_info = self.client.create_multipart_upload(
            Bucket=self.bucket_name,
            Key=self.object_key
        )
        upload_id = upload_info['UploadId']
        common_part_size = 20 * 1024 * 1024
        part_count = (file_size // common_part_size + 1) if (file_size % common_part_size > 0) else (file_size // common_part_size)
        part_info_list = []
        for i in range(part_count):
            presigned_url = self.client.generate_presigned_url(
                ClientMethod='upload_part',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': self.object_key,
                    'PartNumber': i + 1,
                    'UploadId': upload_id,
                },
                ExpiresIn=expiration
            )
            part_info_list.append(presigned_url)
        return {
            'uploadId': upload_id,
            'object_key': self.object_key,
            'part_count': part_count,
            'part_size': common_part_size,
            'partInfoList': part_info_list,
            'multipart': True
        }

    def complete_multipart_upload(self, upload_id, part_info_list):
        try:
            part_info_list = sorted(part_info_list, key=lambda part_info: part_info['PartNumber'])
            parts = []
            for part_info in part_info_list:
                parts.append({
                    'ETag': part_info['ETag'],
                    'PartNumber': part_info['PartNumber']
                })
            complete_response = self.client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=self.object_key,
                UploadId=upload_id,
                MultipartUpload={
                    'Parts': parts
                }
            )
            return complete_response
        except ClientError as e:
            logger.error(e)
            raise SSSUploadFileException(f"complete multipart upload unsuccessfully.")

    def abort_multipart_upload(self, upload_id):
        try:
            abort_response = self.client.abort_multipart_upload(
                Bucket=self.bucket_name,
                Key=self.object_key,
                UploadId=upload_id
            )
            return abort_response
        except ClientError as e:
            logger.error(e)
            raise SSSUploadFileException(f"abort multipart upload unsuccessfully.")

    def __del__(self):
        self.client.close()

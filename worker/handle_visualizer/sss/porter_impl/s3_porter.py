from concurrent.futures import ThreadPoolExecutor
import io
import os
import boto3
from botocore.client import Config, ClientError
from exception.sss.copy_file_exception import SSSCopyFileException
from exception.sss.fetch_file_exception import SSSFetchFileException
from exception.sss.remove_file_exception import SSSRemoveFileException
from exception.sss.upload_file_exception import SSSUploadFileException

from sss.porter import Porter
from constants import BUCKET_NAME
from logger_factory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class S3Porter(Porter):
    def __init__(self) -> None:
        self.client = None
        self._create_client()
        self.headers = None
        self.metadata = dict()
        self.object_key = None
        self.bucket_name = BUCKET_NAME

    def _create_client(self):
        self.client = boto3.client('s3')

    def get_bucket_name(self):
        return self.bucket_name

    def get_object_key(self):
        return self.object_key

    def set_headers(self, headers):
        self.headers = headers

    def set_metadata(self, key, value):
        self.metadata[key] = value

    def remove_metadata(self, key):
        del self.metadata[key]

    def set_operation_target(self, object_key):
        self.object_key = object_key

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
            upload_response = self.client.put_object(
                Bucket=self.bucket_name,
                Key=self.object_key,
                Body=text
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

    def copy_file(self, source_object_key):
        try:
            copy_response = self.client.copy_object(
                Bucket=self.bucket_name,
                Key=self.object_key,
                CopySource={
                    'Bucket': BUCKET_NAME,
                    'Key': source_object_key
                }
            )
            return copy_response
        except ClientError as e:
            logger.error(e)
            raise SSSCopyFileException(f"copy unsuccessfully.")

    def list_files(self, start_after: str = '', max_keys: int = 1000, recursive=False):
        try:
            if recursive:
                list_response = self.client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=self.object_key,
                    MaxKeys=max_keys,
                    StartAfter=start_after
                )
                object_list = [item["Key"]
                               for item in list_response.get('Contents', [])]
                return object_list
            else:
                list_response = self.client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=self.object_key,
                    Delimiter='/',
                    MaxKeys=max_keys,
                    StartAfter=start_after
                )
                object_list = list_response.get(
                    'CommonPrefixes', []) + [item["Key"] for item in list_response.get("Contents", [])]
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
            file_name = self.object_key.split('/')[-1]
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
            raise SSSFetchFileException(
                f"generate presigned url unsuccessfully.")

    def get_presigned_post(self, expiration, fields=None):
        try:
            presigned_post = self.client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=self.object_key,
                Fields=fields,
                ExpiresIn=expiration
            )
            return presigned_post
        except ClientError as e:
            logger.error(e)
            raise SSSFetchFileException(
                f"generate presigned post unsuccessfully.")

    def get_multipart_upload_presigned_post(self, file_size, expiration):
        upload_info = self.client.create_multipart_upload(
            Bucket=self.bucket_name,
            Key=self.object_key
        )
        upload_id = upload_info['UploadId']
        common_part_size = 20 * 1024 * 1024
        part_count = (file_size // common_part_size +
                      1) if file_size % common_part_size != 0 else file_size // common_part_size
        latest_part_size = (file_size - common_part_size * (part_count - 1)
                            ) if part_count * common_part_size != file_size else common_part_size
        part_info_list = []
        for i in range(part_count):
            part_size = common_part_size if i != part_count - 1 else latest_part_size
            part_number = i + 1
            presigned_post = self.client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=self.object_key,
                Fields={
                    'key': self.object_key,
                    'uploadId': upload_id,
                    'partNumber': str(part_number)
                },
                ExpiresIn=expiration
            )
            part_info_list.append(presigned_post)
        return {
            'uploadId': upload_id,
            'part_count': part_count,
            'part_size': common_part_size,
            'partInfoList': part_info_list
        }

    def __del__(self):
        self.client.close()

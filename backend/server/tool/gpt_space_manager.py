import os
from boto3.session import Session,Config
from constants.gpt import PROXIES
import tempfile

# Credentials are resolved by the standard boto3 credential chain
# (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY env vars, shared config, instance role, ...).
GPT_RELATED_REGION = os.environ.get("GPT_SPACE_REGION") or os.environ.get("AWS_REGION")
GPT_RELATED_BUCKET = os.environ.get("GPT_SPACE_BUCKET", "<YOUR_GPT_SPACE_BUCKET>")
GPT_SPACE_PREFIX = os.environ.get("GPT_SPACE_PREFIX", "gpt-space/")


class GptSpaceManager:

    def __init__(self) -> None:
        config = Config(
            proxies=PROXIES
        )
        session = Session(
            region_name=GPT_RELATED_REGION,
        )
        self.s3_client = session.client("s3", config=config)

    def list_files(self, owner_id, prefix, search_key, recursive=False):
        objects = []
        prefix = prefix or ""
        prefix = prefix.strip("/")
        space_prefix = f"{GPT_SPACE_PREFIX}{owner_id}/"
        prefix_path = f"{space_prefix}{prefix}"
        if recursive:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            # Use paginator to handle pagination if there are more than 1000 objects
            for result in paginator.paginate(Bucket=GPT_RELATED_BUCKET, Prefix=prefix_path):
                if 'Contents' in result:
                    objects.extend([obj['Key'][len(space_prefix):] for obj in result['Contents']])
        else:
            # Non-recursive listing
            response = self.s3_client.list_objects_v2(Bucket=GPT_RELATED_BUCKET, Prefix=prefix_path, Delimiter='/')
            if 'Contents' in response:
                objects.extend([obj["Key"].split("/")[-1] for obj in response['Contents']])

        # Now you can filter objects based on your search_key
        if search_key:
            objects = [obj for obj in objects if search_key in obj]

        return objects

    def upload_file(self, owner_id, file, prefix, file_name):
        prefix = prefix or ""
        prefix = prefix.strip("/")
        tempfile_path = tempfile.NamedTemporaryFile().name
        file.save(tempfile_path)
        object_key = f"{GPT_SPACE_PREFIX}{owner_id}/{prefix}/{file_name}"
        self.s3_client.upload_file(tempfile_path, GPT_RELATED_BUCKET, object_key)

    def download_file(self, owner_id, prefix, file_name):
        prefix = prefix or ""
        prefix = prefix.strip("/")
        object_key = f"{GPT_SPACE_PREFIX}{owner_id}/{prefix}/{file_name}"
        tempfile_path = tempfile.NamedTemporaryFile().name
        self.s3_client.download_file(GPT_RELATED_BUCKET, object_key, tempfile_path)
        return tempfile_path

    def delete_file(self, owner_id, prefix, file_name):
        prefix = prefix or ""
        prefix = prefix.strip("/")
        object_key = f"{GPT_SPACE_PREFIX}{owner_id}/{prefix}/{file_name}"
        self.s3_client.delete_object(Bucket=GPT_RELATED_BUCKET, Key=object_key)

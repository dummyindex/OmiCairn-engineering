from db import (
    Data,
    find_data_by_created_from_and_state,
    update_data
)
import os
import time
import boto3
from constants import (
    CreatedFrom,
    UploadType,
    DataState,
    BUCKET_NAME
)
from sss.porter_factory import PorterFactory

def _create_s3_client():
    return boto3.client(
        's3',
        region_name=os.environ.get('AWS_REGION'),
        endpoint_url=os.environ.get('S3_ENDPOINT_URL') or None
    )

def list_related_files_by_data_id(data_id: int, upload_type: str):
    if upload_type == UploadType.ANNDATA.value:
        return [f"adata/{data_id}.h5ad"]
    porter = PorterFactory.create_porter()
    porter.set_operation_target(f"adata/{data_id}-{upload_type}-")
    files = porter.list_files(recursive=True)
    return files

from datetime import datetime, timedelta

def get_latest_part_time(bucket_name, key):
    # Create S3 client
    s3_client = _create_s3_client()
    
    try:
        # List all in-progress multipart uploads
        response = s3_client.list_multipart_uploads(Bucket=bucket_name)
        
        # Find the multipart upload task for the specific file
        upload_id = None
        if 'Uploads' in response:
            for upload in response['Uploads']:
                if upload['Key'] == key:
                    upload_id = upload['UploadId']
                    break
        
        if not upload_id:
            print(f"No ongoing multipart upload found for key {key}.")
            return None
        
        # List all parts of the specific multipart upload
        parts_response = s3_client.list_parts(Bucket=bucket_name, Key=key, UploadId=upload_id)
        
        # Find the most recently uploaded part
        latest_part = None
        if 'Parts' in parts_response and len(parts_response['Parts']) > 0:
            latest_part = max(parts_response['Parts'], key=lambda x: x['LastModified'])
        
        if latest_part:
            latest_part_time = latest_part['LastModified']
            print(f"Latest part uploaded at: {latest_part_time}")
            return latest_part_time
        else:
            print(f"No parts have been uploaded for key {key}.")
            return None
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def is_multipart_upload_timed_out(created_time: datetime, bucket_name, key, timeout_hours=1):
    now = datetime.now(created_time.tzinfo)
    if now - created_time < timedelta(hours=timeout_hours):
        print(f"The multipart upload for key {key} is still active.")
        return False

    latest_part_time = get_latest_part_time(bucket_name, key)
    
    if latest_part_time:
        # Compute the difference between the current time and the last-modified time of the latest part
        current_time = datetime.now(latest_part_time.tzinfo)  # ensure consistent timezone
        time_diff = current_time - latest_part_time
        
        # Check whether it has timed out
        if time_diff > timedelta(hours=timeout_hours):
            print(f"The multipart upload for key {key} has timed out.")
            return True
        else:
            print(f"The multipart upload for key {key} is still active.")
            return False
    else:
        print(f"No ongoing multipart upload found for key {key}.")
        return False


def check():
    uploading_datas = find_data_by_created_from_and_state(
        CreatedFrom.UPLOAD.value,
        DataState.UPLOADING.value
    )
    for data in uploading_datas:
        files = list_related_files_by_data_id(data.id, data.upload_type)
        for file in files:
            if is_multipart_upload_timed_out(data.created_time, BUCKET_NAME, file):
                print(f"Data {data.id} has timed out. Marking as error.")
                update_data(data.id, {"state": DataState.ERROR.value, "error_message": "Multipart upload timed out."})
        

def main():
    while True:
        check()
        time.sleep(60 * 10)


if __name__ == "__main__":
    main()
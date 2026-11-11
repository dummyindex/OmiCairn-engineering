"""
Upload all outputs to S3 after Claude Code finishes.
"""
import os
import json
import boto3
from pathlib import Path
from datetime import datetime

from api_client import APIClient
from utils import generate_thumbnail
from constants import NODE_ID, BUCKET_NAME, USER_ID, COMPUTATION_ID

def get_s3_client():
    """Create S3 client."""
    return boto3.client("s3")

def upload_charts(s3_client, bucket_name, computation_id, node_id, api_client: APIClient, charts_dir="/omicairn/outputs/charts"):
    """
    Upload chart images with thumbnails to S3.

    This scans the outputs directory recursively for image files (PNG, JPG, JPEG, TIFF, TIF, PDF),
    generates thumbnails for each, and uploads both to S3 via the figure API.

    Args:
        s3_client: Boto3 S3 client
        bucket_name: S3 bucket name
        computation_id: The computation ID
        node_id: The node ID
        api_client: APIClient instance for creating figures
        charts_dir: Directory to scan for chart images (default: /omicairn/outputs/charts)

    Returns:
        Number of charts uploaded
    """
    charts_path = Path(charts_dir)
    chart_count = 0

    print(f"\n========== UPLOADING CHARTS ==========")
    print(f"Checking charts directory: {charts_dir}")

    if not charts_path.exists():
        print(f"Charts directory does not exist: {charts_dir}")
        print("========== CHARTS UPLOAD COMPLETE ==========\n")
        return 0

    print(f"Charts directory exists")

    # Supported image extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.tiff', '.tif', '.pdf')

    # Walk through all subdirectories recursively
    for root, dirs, files in os.walk(charts_dir):
        root_path = Path(root)
        image_files = [f for f in files if f.lower().endswith(image_extensions)]

        if image_files:
            print(f"Found {len(image_files)} chart images in {root}")

        for filename in files:
            if not filename.lower().endswith(image_extensions):
                continue

            chart_count += 1
            absolute_path = root_path / filename
            relative_path = absolute_path.relative_to(charts_path)

            print(f"Processing chart {chart_count}: {filename}")

            # Create figure_name with directory prefix
            if str(relative_path) != filename:
                dir_prefix = str(relative_path.parent).replace(os.sep, '_')
                figure_name = f"{dir_prefix}_{filename}"
            else:
                figure_name = filename

            # Get file suffix
            suffix = os.path.splitext(filename)[1][1:].lower()

            # Generate thumbnail
            thumbnail_path = root_path / f"thumbnail_{filename}"
            try:
                generate_thumbnail(str(absolute_path), str(thumbnail_path), 128)
            except Exception as e:
                print(f"Warning: Failed to generate thumbnail for {filename}: {e}")
                continue

            # Create figure entry via API
            upload_info = api_client.create_figure(
                computation_id,
                figure_name,
                suffix,
                node_id
            )

            if not upload_info:
                print(f"Warning: Failed to create figure entry for {filename}")
                continue

            key = upload_info.get("key")
            thumbnail_key = upload_info.get("thumbnailKey")

            if not key or not thumbnail_key:
                print(f"Warning: Missing S3 keys for {filename}")
                continue

            # Upload original image
            try:
                print(f"Uploading chart: {filename} -> {key}")
                s3_client.upload_file(str(absolute_path), bucket_name, key)
            except Exception as e:
                print(f"Error uploading chart {filename}: {e}")
                continue

            # Upload thumbnail
            try:
                print(f"Uploading thumbnail: thumbnail_{filename} -> {thumbnail_key}")
                s3_client.upload_file(str(thumbnail_path), bucket_name, thumbnail_key)
            except Exception as e:
                print(f"Error uploading thumbnail for {filename}: {e}")

            print(f"Successfully uploaded chart: {figure_name}")

    print(f"Uploaded {chart_count} chart images")
    print("========== CHARTS UPLOAD COMPLETE ==========\n")

    return chart_count


def create_manifest(s3_client, bucket_name, computation_id, uploaded_files):
    """Create and upload a manifest file."""
    status = "completed"

    manifest = {
        "computation_id": computation_id,
        "timestamp": datetime.utcnow().isoformat(),
        "files": uploaded_files,
        "status": status,
        "executor": "claude-code"
    }

    s3_key = f"omicairn/computation/{computation_id}/manifest.json"
    print(f"Uploading manifest to: {s3_key} (status: {status})")
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json.dumps(manifest, indent=2),
        ContentType="application/json"
    )


def get_execution_logs():
    """Read execution logs from the log file."""
    log_path = Path("/omicairn/outputs/claude_code.log")
    if log_path.exists():
        try:
            content = log_path.read_text()
            # Limit log size to avoid overwhelming the backend
            max_size = 100000  # 100KB
            if len(content) > max_size:
                content = content[-max_size:]
                content = "... (truncated) ...\n" + content
            return content
        except Exception as e:
            return f"Error reading log: {e}"
    return "No log file found"


def notify_completion(computation_id, user_id, success=True):
    """
    Notify the backend that computation is complete by calling the finished-report
    or failed-report API endpoint. This is critical for updating the node state.

    Args:
        computation_id: The computation ID
        user_id: The user ID for authentication
        success: Whether the execution was successful
    """
    status = "success" if success else "failed"
    print(f"Computation {computation_id} completed with status: {status}")

    # Check if API endpoints are configured
    computation_server_host = os.environ.get("COMPUTATION_SERVER_HOST", "")
    if not computation_server_host:
        print("WARNING: COMPUTATION_SERVER_HOST not configured, cannot report completion to backend")
        print("The node state will not be updated automatically.")
        return

    if not user_id:
        print("WARNING: USER_ID not set, cannot authenticate to report completion")
        return

    try:
        client = APIClient(user_id)
        logs = get_execution_logs()

        if success:
            # This executor does not run a separate automated output review.
            # job_review_passed=True only signals "no review error was raised";
            # it does not assert that the outputs were reviewed.
            result = client.report_finished(
                computation_id=computation_id,
                logs=logs,
                job_review_passed=True
            )
            if result:
                print("Successfully reported FINISHED state to backend")
            else:
                print("WARNING: Failed to report finished state to backend")
        else:
            error_description = os.environ.get(
                "PIPELINE_ERROR", "Claude Code execution failed"
            )
            result = client.report_failed(
                computation_id=computation_id,
                error_description=error_description,
                logs=logs
            )
            if result:
                print("Successfully reported FAILED state to backend")
            else:
                print("WARNING: Failed to report failed state to backend")

    except Exception as e:
        print(f"Error notifying completion to backend: {e}")
        import traceback
        traceback.print_exc()
        print("WARNING: Node state may not be updated correctly")


def upload_s3_folder(s3_client, object_key_prefix, local):
    """Upload a folder to S3, preserving the directory structure"""
    upload_files = []
    for root, dirs, files in os.walk(local):
        for filename in files:
            local_file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(local_file_path, local)
            s3_object_key = os.path.join(object_key_prefix, rel_path)
            s3_client.upload_file(local_file_path, BUCKET_NAME, s3_object_key)
            upload_files.append(rel_path)

    return upload_files

def upload_s3_file(s3_client, s3_object_key, local_file_path):
    s3_client.upload_file(local_file_path, BUCKET_NAME, s3_object_key)

def pipeline_succeeded():
    """Read the orchestration outcome passed in by start_claude_code.sh."""
    return os.environ.get("PIPELINE_SUCCESS", "0") == "1"


def close_out():
    """Main entry point."""
    success = pipeline_succeeded()
    s3_client = get_s3_client()

    api_client = APIClient(USER_ID)
    computation_details = api_client.get_computation_details(NODE_ID) or {}
    result_data_id = (computation_details.get("computation_basic_info") or {}).get("resultDataId", None)

    # upload charts, scan /omicairn/outputs/charts recursively
    upload_charts(
        s3_client,
        BUCKET_NAME,
        COMPUTATION_ID,
        NODE_ID,
        api_client,
        "/omicairn/outputs/charts"
    )

    # upload outputs
    output_s3_prefix = f"adata/{result_data_id}-general-s3-store/"
    local_path = "/omicairn/outputs/"
    uploaded_files = upload_s3_folder(s3_client, output_s3_prefix, local_path)

    # Create manifest
    create_manifest(s3_client, BUCKET_NAME, COMPUTATION_ID, uploaded_files)

    # Notify completion - THIS IS CRITICAL for updating node state
    # Report the real outcome of the orchestration loop (FINISHED or FAILED)
    notify_completion(COMPUTATION_ID, USER_ID, success=success)

    print("Close out complete!")

if __name__ == "__main__":
    close_out()

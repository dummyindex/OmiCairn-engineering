#!/usr/bin/env python3
"""
Upload completed step outputs to S3 incrementally.

This script is called by Claude Code after completing each step to upload
the step's outputs to S3 immediately, rather than waiting until the end.

Usage:
    python3 /app/scripts/upload_step.py step_01_data_loading
    python3 /app/scripts/upload_step.py step_02_quality_control
    python3 /app/scripts/upload_step.py --all  # Upload all step folders
"""
import os
import sys
import boto3
from pathlib import Path
from datetime import datetime


def get_s3_client():
    """Create S3 client."""
    return boto3.client("s3")


def upload_folder(s3_client, bucket_name, computation_id, folder_path, folder_name):
    """Upload a folder to S3."""
    uploaded_files = []
    folder = Path(folder_path)

    if not folder.exists():
        print(f"Warning: Folder does not exist: {folder_path}")
        return uploaded_files

    for file_path in folder.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(folder.parent)
            s3_key = f"computation/{computation_id}/outputs/{relative_path}"

            print(f"  Uploading: {relative_path}")
            try:
                s3_client.upload_file(str(file_path), bucket_name, s3_key)
                uploaded_files.append(str(relative_path))
            except Exception as e:
                print(f"  Error uploading {relative_path}: {e}")

    return uploaded_files


def upload_step(step_name: str):
    """Upload a single step folder to S3."""
    computation_id = os.environ.get("COMPUTATION_ID", "")
    bucket_name = os.environ.get("BUCKET_NAME", "")
    outputs_dir = "/omicairn/outputs"

    if not computation_id:
        print("Error: COMPUTATION_ID environment variable not set")
        return False

    if not bucket_name:
        print("Error: BUCKET_NAME environment variable not set")
        return False

    step_folder = Path(outputs_dir) / step_name

    if not step_folder.exists():
        print(f"Error: Step folder does not exist: {step_folder}")
        return False

    print(f"=== Uploading step: {step_name} ===")
    print(f"Computation ID: {computation_id}")
    print(f"Bucket: {bucket_name}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")

    s3_client = get_s3_client()
    uploaded_files = upload_folder(s3_client, bucket_name, computation_id, step_folder, step_name)

    print(f"Uploaded {len(uploaded_files)} files from {step_name}")
    print(f"=== Step {step_name} upload complete ===\n")
    return True


def upload_all_steps():
    """Upload all step folders found in outputs directory."""
    outputs_dir = Path("/omicairn/outputs")

    if not outputs_dir.exists():
        print("Error: Outputs directory does not exist")
        return False

    # Find all step folders (step_XX_*)
    step_folders = sorted([
        f.name for f in outputs_dir.iterdir()
        if f.is_dir() and f.name.startswith("step_")
    ])

    if not step_folders:
        print("No step folders found to upload")
        return True

    print(f"Found {len(step_folders)} step folders to upload")

    success = True
    for step_name in step_folders:
        if not upload_step(step_name):
            success = False

    return success


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 upload_step.py <step_folder_name>")
        print("       python3 upload_step.py --all")
        print("")
        print("Examples:")
        print("  python3 upload_step.py step_01_data_loading")
        print("  python3 upload_step.py step_02_quality_control")
        print("  python3 upload_step.py --all")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--all":
        success = upload_all_steps()
    else:
        success = upload_step(arg)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

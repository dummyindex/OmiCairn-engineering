#!/usr/bin/env python3
"""
Upload orchestration logs and control files to S3.

This script uploads all orchestration-related files including:
- Progress status snapshots
- Job logs and results
- Loop iteration logs
- Control file backups

Usage:
    python3 /app/scripts/upload_orchestration_logs.py
    python3 /app/scripts/upload_orchestration_logs.py --iteration 5
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import boto3

# Directories
OUTPUTS_DIR = Path("/omicairn/outputs")
ORCHESTRATION_DIR = OUTPUTS_DIR / "orchestration_logs"
CONTROL_DIR = Path("/omicairn/control")


def get_s3_client():
    """Create S3 client."""
    return boto3.client("s3")


def upload_file_to_s3(s3_client, bucket_name: str, computation_id: str,
                       file_path: Path, s3_key: str) -> bool:
    """Upload a single file to S3."""
    try:
        full_s3_key = f"computation/{computation_id}/outputs/{s3_key}"
        s3_client.upload_file(str(file_path), bucket_name, full_s3_key)
        print(f"  Uploaded: {s3_key}")
        return True
    except Exception as e:
        print(f"  Failed to upload {s3_key}: {e}")
        return False


def upload_orchestration_logs(iteration: int = None):
    """Upload all orchestration logs to S3."""
    bucket_name = os.environ.get("BUCKET_NAME", "")
    computation_id = os.environ.get("COMPUTATION_ID", "")

    if not bucket_name or not computation_id:
        print("Warning: S3 upload skipped (missing BUCKET_NAME or COMPUTATION_ID)")
        return False

    print("=" * 60)
    print("Uploading Orchestration Logs to S3")
    print("=" * 60)
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"Bucket: {bucket_name}")
    print(f"Computation ID: {computation_id}")
    if iteration:
        print(f"Iteration: {iteration}")
    print("-" * 60)

    s3_client = get_s3_client()
    uploaded_count = 0
    failed_count = 0

    # Ensure orchestration directory exists
    ORCHESTRATION_DIR.mkdir(parents=True, exist_ok=True)

    # Upload all files in orchestration_logs directory
    if ORCHESTRATION_DIR.exists():
        print("\nUploading orchestration log files:")
        for file_path in sorted(ORCHESTRATION_DIR.iterdir()):
            if file_path.is_file():
                s3_key = f"orchestration_logs/{file_path.name}"
                if upload_file_to_s3(s3_client, bucket_name, computation_id, file_path, s3_key):
                    uploaded_count += 1
                else:
                    failed_count += 1

    # Upload job_logs from each step folder
    print("\nUploading step job logs:")
    for step_dir in sorted(OUTPUTS_DIR.iterdir()):
        if step_dir.is_dir() and step_dir.name.startswith("step_"):
            job_logs_dir = step_dir / "job_logs"
            if job_logs_dir.exists():
                for file_path in sorted(job_logs_dir.iterdir()):
                    if file_path.is_file():
                        s3_key = f"{step_dir.name}/job_logs/{file_path.name}"
                        if upload_file_to_s3(s3_client, bucket_name, computation_id, file_path, s3_key):
                            uploaded_count += 1
                        else:
                            failed_count += 1

    # Summary
    print("-" * 60)
    print(f"Upload complete: {uploaded_count} files uploaded, {failed_count} failed")
    print("=" * 60)

    return failed_count == 0


def main():
    iteration = None
    if len(sys.argv) > 2 and sys.argv[1] == "--iteration":
        try:
            iteration = int(sys.argv[2])
        except ValueError:
            print(f"Invalid iteration number: {sys.argv[2]}")
            sys.exit(1)

    success = upload_orchestration_logs(iteration)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

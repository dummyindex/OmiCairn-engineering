#!/usr/bin/env python3
"""
Periodically upload claude_code.log to S3 for real-time monitoring.

This script runs in the background and uploads the log file
every N seconds, allowing users to monitor Claude Code's progress.

Usage:
    python3 /app/scripts/upload_conversation.py &

    # Or with custom interval (default 60 seconds):
    UPLOAD_INTERVAL=30 python3 /app/scripts/upload_conversation.py &
"""
import os
import sys
import time
import boto3
from pathlib import Path
from datetime import datetime


def get_s3_client():
    """Create S3 client."""
    return boto3.client("s3")


def upload_log():
    """Upload claude_code.log to S3."""
    computation_id = os.environ.get("COMPUTATION_ID", "")
    bucket_name = os.environ.get("BUCKET_NAME", "")

    if not computation_id or not bucket_name:
        return False

    log_path = Path("/omicairn/outputs/claude_code.log")

    s3_client = get_s3_client()
    uploaded = False

    # Upload log file if it exists
    if log_path.exists() and log_path.stat().st_size > 0:
        s3_key = f"computation/{computation_id}/outputs/claude_code.log"
        try:
            s3_client.upload_file(str(log_path), bucket_name, s3_key)
            uploaded = True
        except Exception as e:
            print(f"Error uploading log: {e}")

    return uploaded


def main():
    interval = int(os.environ.get("UPLOAD_INTERVAL", "300"))  # Default 5 minutes

    computation_id = os.environ.get("COMPUTATION_ID", "unknown")

    print(f"[log-uploader] Starting periodic upload for computation {computation_id}")
    print(f"[log-uploader] Upload interval: {interval} seconds")

    # Wait for log file to be created
    initial_wait = 30
    print(f"[log-uploader] Waiting {initial_wait}s for Claude Code to start...")
    time.sleep(initial_wait)

    upload_count = 0
    while True:
        try:
            if upload_log():
                upload_count += 1
                print(f"[log-uploader] Upload #{upload_count} complete at {datetime.utcnow().isoformat()}")
            time.sleep(interval)
        except KeyboardInterrupt:
            print("[log-uploader] Stopped")
            break
        except Exception as e:
            print(f"[log-uploader] Error: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    main()

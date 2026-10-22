#!/usr/bin/env python3
"""
Check if all analysis steps are completed.

This script is part of the orchestration loop that allows Claude Code sessions
to pause for long-running jobs and resume after completion.

Exit codes:
    0 - All steps completed (exit the loop)
    1 - Steps remaining (continue the loop)

Usage:
    python3 /app/scripts/all_steps_done.py

Input: Parses /omicairn/outputs/claude_code.log for TodoWrite entries
Output: Logs saved to /omicairn/outputs/orchestration_logs/ and uploaded to S3
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import boto3
from parse_todo_progress import find_last_todowrite, check_all_completed

# Persistent output directory
OUTPUTS_DIR = Path("/omicairn/outputs")
ORCHESTRATION_DIR = OUTPUTS_DIR / "orchestration_logs"

# Log file for todo extraction
CLAUDE_LOG_FILE = OUTPUTS_DIR / "claude_code.log"


def get_s3_client():
    """Create S3 client."""
    return boto3.client("s3")


def upload_file_to_s3(file_path: Path, s3_key: str) -> bool:
    """Upload a single file to S3."""
    bucket_name = os.environ.get("BUCKET_NAME", "")
    computation_id = os.environ.get("COMPUTATION_ID", "")

    if not bucket_name or not computation_id:
        return False

    try:
        s3_client = get_s3_client()
        full_s3_key = f"computation/{computation_id}/outputs/{s3_key}"
        s3_client.upload_file(str(file_path), bucket_name, full_s3_key)
        print(f"  Uploaded to S3: s3://{bucket_name}/{full_s3_key}")
        return True
    except Exception as e:
        print(f"  S3 upload failed: {e}")
        return False


class LogCapture:
    """Capture print output to both console and file."""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.lines = []

    def log(self, message: str):
        """Log a message to both console and buffer."""
        print(message)
        self.lines.append(message)

    def save(self):
        """Save buffered lines to file."""
        with open(self.log_file, "w") as f:
            for line in self.lines:
                f.write(line + "\n")


def main():
    """Check pipeline progress and return appropriate exit code."""

    # Ensure orchestration directory exists
    ORCHESTRATION_DIR.mkdir(parents=True, exist_ok=True)

    # Create log file for this check
    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_file = ORCHESTRATION_DIR / f"progress_check_{timestamp_str}.log"
    logger = LogCapture(log_file)

    logger.log("=" * 60)
    logger.log("Progress Status Check (Todo-Based)")
    logger.log("=" * 60)
    logger.log(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    logger.log(f"Checking: {CLAUDE_LOG_FILE}")
    logger.log("-" * 60)

    # Default: continue loop
    exit_code = 1

    # Extract todos from claude_code.log
    if not CLAUDE_LOG_FILE.exists():
        logger.log("Log file does not exist yet")
        logger.log("DECISION: Pipeline not started, continue loop")
        logger.log("EXIT CODE: 1 (continue)")
    else:
        try:
            todos = find_last_todowrite(CLAUDE_LOG_FILE)
            if todos:
                completed = sum(1 for t in todos if t.get("status") == "completed")
                in_progress = sum(1 for t in todos if t.get("status") == "in_progress")
                pending = sum(1 for t in todos if t.get("status") == "pending")
                total = len(todos)

                logger.log(f"Found {total} todos in log")
                logger.log(f"  Completed: {completed}")
                logger.log(f"  In Progress: {in_progress}")
                logger.log(f"  Pending: {pending}")
                logger.log("")

                if check_all_completed(todos):
                    logger.log("DECISION: All tasks completed!")
                    logger.log("EXIT CODE: 0 (exit loop - success)")
                    exit_code = 0
                else:
                    logger.log(f"DECISION: {total - completed} tasks remaining")
                    logger.log("EXIT CODE: 1 (continue loop)")
                    exit_code = 1
            else:
                logger.log("No TodoWrite entries found in log")
                logger.log("DECISION: No todo state found, continue loop")
                logger.log("EXIT CODE: 1 (continue)")
                exit_code = 1

        except Exception as e:
            logger.log(f"Error parsing todos from log: {e}")
            logger.log("DECISION: Error occurred, continue loop")
            logger.log("EXIT CODE: 1 (continue)")
            exit_code = 1

    logger.log("=" * 60)

    # Save log to file
    logger.save()

    # Upload logs to S3
    upload_file_to_s3(log_file, f"orchestration_logs/{log_file.name}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

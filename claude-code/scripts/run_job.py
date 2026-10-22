#!/usr/bin/env python3
"""
Execute long-running jobs requested by Claude Code session.

This script is part of the orchestration loop that allows Claude Code sessions
to pause for long-running jobs and resume after completion.

Usage:
    python3 /app/scripts/run_job.py

Input: /omicairn/control/job_request.json
Output: /omicairn/control/job_result.json (also copied to step folder and S3)
"""

import json
import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import boto3

# Control directory for orchestration state
CONTROL_DIR = Path("/omicairn/control")
JOB_REQUEST = CONTROL_DIR / "job_request.json"
JOB_RESULT = CONTROL_DIR / "job_result.json"

# Persistent output directory
OUTPUTS_DIR = Path("/omicairn/outputs")
ORCHESTRATION_DIR = OUTPUTS_DIR / "orchestration_logs"


def get_s3_client():
    """Create S3 client."""
    return boto3.client("s3")


def upload_file_to_s3(file_path: Path, s3_key: str) -> bool:
    """Upload a single file to S3."""
    bucket_name = os.environ.get("BUCKET_NAME", "")
    computation_id = os.environ.get("COMPUTATION_ID", "")

    if not bucket_name or not computation_id:
        print(f"  S3 upload skipped (missing BUCKET_NAME or COMPUTATION_ID)")
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


def extract_step_from_path(working_directory: str) -> str:
    """Extract step folder name from working directory path."""
    # e.g., /omicairn/outputs/step_02_cellranger -> step_02_cellranger
    path = Path(working_directory)
    for part in path.parts:
        if part.startswith("step_"):
            return part
    return "unknown_step"


def validate_command(command: str) -> tuple[bool, str | None]:
    """
    Validate that the command's executable exists and is accessible.

    Returns:
        tuple: (is_valid, error_message)
               - (True, None) if valid
               - (False, "error description") if invalid
    """
    if not command or not command.strip():
        return False, "Command is empty"

    # Parse the command to extract the executable
    # Handle both simple commands and complex shell commands
    try:
        # Use shlex to properly parse the command
        parts = shlex.split(command)
        if not parts:
            return False, "Command parsed to empty list"
        executable = parts[0]
    except ValueError as e:
        # shlex.split can fail on malformed strings
        # Fall back to simple split
        executable = command.split()[0]

    # Check if it's an absolute path
    if executable.startswith("/"):
        exe_path = Path(executable)
        if not exe_path.exists():
            return False, f"Executable not found at path: {executable}"
        if not exe_path.is_file():
            return False, f"Path exists but is not a file: {executable}"
        if not os.access(executable, os.X_OK):
            return False, f"File exists but is not executable: {executable}"
        return True, None

    # Check if it's a command in PATH
    which_result = shutil.which(executable)
    if which_result is None:
        # Also check common bioinformatics tool locations
        common_paths = [
            f"/omicairn/workspace/{executable}",
            f"/usr/local/bin/{executable}",
            f"/opt/{executable}",
        ]
        for path in common_paths:
            if Path(path).exists() and os.access(path, os.X_OK):
                return True, None

        return False, f"Executable '{executable}' not found in PATH or common locations"

    return True, None


def main():
    """Main entry point for job execution."""

    # Ensure directories exist
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    ORCHESTRATION_DIR.mkdir(parents=True, exist_ok=True)

    # Check if there's a job to run
    if not JOB_REQUEST.exists():
        print("No job request found at", JOB_REQUEST)
        print("Nothing to do.")
        return 0

    # Read job request
    try:
        with open(JOB_REQUEST) as f:
            request = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in job_request.json: {e}")
        return 1

    # Extract job parameters
    request_id = request.get("request_id", "unknown")
    command = request.get("command")
    cwd = request.get("working_directory", "/omicairn/workspace")
    description = request.get("description", "No description")
    expected_outputs = request.get("expected_outputs", [])

    if not command:
        print("ERROR: No command specified in job_request.json")
        return 1

    # Validate command executable exists before proceeding
    # This catches issues like missing Cell Ranger binaries early
    is_valid, validation_error = validate_command(command)
    if not is_valid:
        print(f"ERROR: Command validation failed: {validation_error}")
        print(f"Command was: {command}")
        print("")
        print("Possible causes:")
        print("  - The executable path is incorrect")
        print("  - The software was not installed or extracted properly")
        print("  - The file exists but lacks execute permissions")
        print("")
        print("Please verify the executable exists and is accessible.")

        # Create a job result indicating validation failure
        # This allows Claude to handle the failure gracefully
        validation_result = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "exit_code": 127,  # Standard "command not found" exit code
            "success": False,
            "duration_seconds": 0,
            "log_file": None,
            "outputs_found": [],
            "outputs_missing": expected_outputs,
            "error_message": f"Command validation failed: {validation_error}",
            "validation_failed": True
        }
        with open(JOB_RESULT, "w") as f:
            json.dump(validation_result, f, indent=2)

        # Remove request file to signal completion (even though it failed)
        try:
            JOB_REQUEST.unlink()
        except Exception:
            pass

        return 1

    print(f"Command validation passed: executable found")

    # Determine step name and create step-specific log directory
    step_name = extract_step_from_path(cwd)
    step_log_dir = OUTPUTS_DIR / step_name / "job_logs"
    step_log_dir.mkdir(parents=True, exist_ok=True)

    # Log file paths - both in step folder and orchestration folder
    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_filename = f"job_{request_id}_{timestamp_str}.log"
    step_log_file = step_log_dir / log_filename
    orchestration_log_file = ORCHESTRATION_DIR / log_filename

    # Also save a copy of the job request
    request_copy_path = step_log_dir / f"job_request_{request_id}.json"
    with open(request_copy_path, "w") as f:
        json.dump(request, f, indent=2)

    # Print job info (this goes to the main orchestration log)
    output_lines = []
    output_lines.append("=" * 60)
    output_lines.append("Job Runner - Starting Execution")
    output_lines.append("=" * 60)
    output_lines.append(f"Request ID: {request_id}")
    output_lines.append(f"Description: {description}")
    output_lines.append(f"Command: {command}")
    output_lines.append(f"Working Directory: {cwd}")
    output_lines.append(f"Step: {step_name}")
    output_lines.append(f"Log File: {step_log_file}")
    output_lines.append(f"Expected Outputs: {len(expected_outputs)} files")
    output_lines.append("=" * 60)

    for line in output_lines:
        print(line)

    start_time = datetime.utcnow()

    # Execute the command
    exit_code = -1
    success = False
    error_msg = None

    try:
        # Ensure working directory exists
        Path(cwd).mkdir(parents=True, exist_ok=True)

        with open(step_log_file, "w") as lf:
            lf.write(f"Job started at: {start_time.isoformat()}Z\n")
            lf.write(f"Request ID: {request_id}\n")
            lf.write(f"Description: {description}\n")
            lf.write(f"Command: {command}\n")
            lf.write(f"Working directory: {cwd}\n")
            lf.write(f"Step: {step_name}\n")
            lf.write("=" * 60 + "\n\n")
            lf.flush()

            # Executes an agent-written command from job_request.json.
            # Only run inside the isolated, ephemeral job container.
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                stdout=lf,
                stderr=subprocess.STDOUT
            )

            lf.write("\n" + "=" * 60 + "\n")
            lf.write(f"Job finished at: {datetime.utcnow().isoformat()}Z\n")
            lf.write(f"Exit code: {result.returncode}\n")

        exit_code = result.returncode
        success = exit_code == 0

    except Exception as e:
        exit_code = -2
        success = False
        error_msg = str(e)
        print(f"ERROR: {error_msg}")

        # Append error to log
        with open(step_log_file, "a") as lf:
            lf.write(f"\n\nERROR: {error_msg}\n")

    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    # Check expected outputs
    outputs_found = []
    outputs_missing = []
    for output_path in expected_outputs:
        if Path(output_path).exists():
            outputs_found.append(output_path)
        else:
            outputs_missing.append(output_path)

    # Build result
    job_result = {
        "request_id": request_id,
        "timestamp": end_time.isoformat() + "Z",
        "step": step_name,
        "description": description,
        "exit_code": exit_code,
        "success": success,
        "duration_seconds": int(duration),
        "log_file": str(step_log_file),
        "outputs_found": outputs_found,
        "outputs_missing": outputs_missing,
        "error_message": error_msg
    }

    # Write result to control directory (for orchestrator to read)
    with open(JOB_RESULT, "w") as f:
        json.dump(job_result, f, indent=2)

    # Also save result to step folder for persistence
    result_copy_path = step_log_dir / f"job_result_{request_id}.json"
    with open(result_copy_path, "w") as f:
        json.dump(job_result, f, indent=2)

    # Copy log to orchestration directory as well
    shutil.copy(step_log_file, orchestration_log_file)

    # Print completion summary
    summary_lines = []
    summary_lines.append("=" * 60)
    summary_lines.append("Job Execution Complete")
    summary_lines.append("=" * 60)
    summary_lines.append(f"Exit Code: {exit_code}")
    summary_lines.append(f"Success: {success}")
    summary_lines.append(f"Duration: {duration:.0f} seconds ({duration/60:.1f} minutes)")
    summary_lines.append(f"Outputs Found: {len(outputs_found)}/{len(expected_outputs)}")
    if outputs_missing:
        summary_lines.append(f"Missing Outputs: {outputs_missing}")
    if error_msg:
        summary_lines.append(f"Error: {error_msg}")
    summary_lines.append(f"Log saved to: {step_log_file}")
    summary_lines.append(f"Result saved to: {result_copy_path}")
    summary_lines.append("=" * 60)

    for line in summary_lines:
        print(line)

    # Append summary to log file
    with open(step_log_file, "a") as lf:
        lf.write("\n")
        for line in summary_lines:
            lf.write(line + "\n")

    # Upload to S3
    print("\n=== Uploading job logs to S3 ===")

    # Upload log file
    s3_log_key = f"{step_name}/job_logs/{log_filename}"
    upload_file_to_s3(step_log_file, s3_log_key)

    # Upload job result
    s3_result_key = f"{step_name}/job_logs/job_result_{request_id}.json"
    upload_file_to_s3(result_copy_path, s3_result_key)

    # Upload job request copy
    s3_request_key = f"{step_name}/job_logs/job_request_{request_id}.json"
    upload_file_to_s3(request_copy_path, s3_request_key)

    # Also upload to orchestration_logs folder
    s3_orch_log_key = f"orchestration_logs/{log_filename}"
    upload_file_to_s3(orchestration_log_file, s3_orch_log_key)

    print("=== S3 upload complete ===")

    # Remove request file to signal completion
    try:
        JOB_REQUEST.unlink()
        print(f"Removed job request file: {JOB_REQUEST}")
    except Exception as e:
        print(f"WARNING: Could not remove job request file: {e}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

from log.logger_factory import LoggerFactory
import boto3
import threading
from constants.computation import (
    PYTHON_JOB_DEFINITION_SCANPY,
    PYTHON_JOB_DEFINITION_DYN,
    PYTHON_JOB_DEFINITION_MEBOCOST,
    PYTHON_JOB_DEFINITION_SCVELO,
    PYTHON_JOB_DEFINITION_SCFATES,
    PYTHON_JOB_DEFINITION_DEFAULT,
    R_JOB_DEFINITION,
    BASH_JOB_DEFINITION,
    JOB_QUEUE,
    LARGE_JOB_QUEUE,
    PYTHON_JOB_DEFINITION_V2,
    PYTHON_JOB_DEFINITION_DEFAULT_V2,
    PYTHON_JOB_DEFINITION_LARGE_DEFAULT_V2,
    PYTHON_JOB_DEFINITION_SCANPY_V2,
    PYTHON_JOB_DEFINITION_DYN_V2,
    PYTHON_JOB_DEFINITION_MEBOCOST_V2,
    PYTHON_JOB_DEFINITION_SCVELO_V2,
    PYTHON_JOB_DEFINITION_SCFATES_V2,
    R_JOB_DEFINITION_V2,
    R_JOB_DEFINITION_V2_METABOANALYST,
    CLAUDE_CODE_JOB_DEFINITION,
    CLAUDE_CODE_EC2_JOB_QUEUE,
    CLAUDE_CODE_EC2_JOB_DEFINITION,
)
from constants.sss import BUCKET_NAME
from constants.common import DEPLOY_ENV
from constants.authority import SYSTEM_AGENT_KEY
from model.dynamic_generation import DynamicGeneration
from model.dynamic_generation_branch import DynamicGenerationBranch
from model.visualizer import Visualizer
from tool.batch_client import BatchClientFactory
import os
import subprocess
import uuid
import shutil
import json


# Root of the worker code inside the container (configurable for local runs).
CODE_SPACE_ROOT = os.environ.get("OMICAIRN_CODE_SPACE", "/omicairn/code_space")


def _child_env(extra: dict) -> dict:
    """Environment for a child worker process: inherit ours, add non-None extras."""
    env = dict(os.environ)
    env.update({k: str(v) for k, v in extra.items() if v is not None})
    return env
LOCAL_JOB_QUEUE = os.getenv("LOCAL_JOB_QUEUE")

logger = LoggerFactory.get_logger("computation_launcher")


class ProgressPercentage:
    """Thread-safe progress callback for S3 uploads that reports at 5% intervals."""

    def __init__(self, total_size: int, key: str):
        self._total_size = total_size
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self._last_reported_threshold = -1
        self._key = key
        self._progress_file = f"/tmp/data-{self._key}-sync-percent"

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            if self._total_size > 0:
                percentage = (self._seen_so_far / self._total_size) * 100
                current_threshold = int(percentage // 5) * 5  # Round down to nearest 5%

                if current_threshold > self._last_reported_threshold:
                    self._last_reported_threshold = current_threshold
                    with open(self._progress_file, 'w') as f:
                        f.write(str(current_threshold))


def _check_file_exists_in_dest(dest_client, dest_bucket: str, key: str, expected_size: int) -> bool:
    """
    Check if a file already exists in the destination bucket with matching size.

    Args:
        dest_client: Boto3 S3 client for the destination bucket
        dest_bucket: Destination bucket name
        key: S3 key to check
        expected_size: Expected file size in bytes

    Returns:
        True if file exists with matching size, False otherwise
    """
    from botocore.exceptions import ClientError
    try:
        response = dest_client.head_object(Bucket=dest_bucket, Key=key)
        existing_size = response.get('ContentLength', 0)
        return existing_size == expected_size
    except ClientError as e:
        # File doesn't exist (404) or other error
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == '404' or error_code == 'NoSuchKey':
            return False
        # For other errors, log and return False to trigger copy
        logger.warning(f"[claude code] Error checking file existence {key}: {e}")
        return False
    except Exception:
        return False


def sync_s3_data_to_claude_code_bucket(source_prefix: str, dest_prefix: str, uploading_key: str) -> bool:
    """
    Copy S3 data from the main storage bucket (BUCKET_NAME) to the Claude Code bucket
    (CLAUDE_CODE_BUCKET_NAME). No-op when both are the same bucket/credentials.
    Used to transfer previous computation outputs for Claude Code jobs.
    Skips files that already exist in the destination with matching size.
    Uses streaming upload with progress tracking that reports at 5% intervals.
    """
    try:
        # Main storage bucket (source)
        source_bucket = BUCKET_NAME
        source_client = boto3.client('s3')

        # Claude Code bucket (destination)
        dest_bucket = os.environ.get('CLAUDE_CODE_BUCKET_NAME') or BUCKET_NAME
        dest_profile = os.environ.get('CLAUDE_CODE_AWS_PROFILE') or None
        if dest_bucket == source_bucket and not dest_profile:
            return True
        dest_session = boto3.Session(profile_name=dest_profile)
        dest_client = dest_session.client('s3')

        paginator = source_client.get_paginator('list_objects_v2')

        files_to_transfer = []
        total_size = 0
        skipped_count = 0

        for page in paginator.paginate(Bucket=source_bucket, Prefix=source_prefix):
            if 'Contents' not in page:
                continue
            for obj in page['Contents']:
                source_key = obj['Key']

                source_size = obj.get('Size', 0)
                relative_path = source_key[len(source_prefix):]
                dest_key = dest_prefix + relative_path

                # Check if file already exists in the destination bucket with matching size
                if _check_file_exists_in_dest(dest_client, dest_bucket, dest_key, source_size):
                    skipped_count += 1
                    continue

                files_to_transfer.append({
                    'source_key': source_key,
                    'dest_key': dest_key,
                    'size': source_size
                })
                total_size += source_size

        logger.info(f"[claude code] Found {len(files_to_transfer)} files to transfer, total size: {total_size} bytes, skipped: {skipped_count} files (already exist)")

        if not files_to_transfer:
            logger.info(f"[claude code] No files to transfer from {source_bucket}/{source_prefix}")
            return True

        progress_tracker = ProgressPercentage(total_size, uploading_key)

        copied_count = 0
        for file_info in files_to_transfer:
            source_key = file_info['source_key']
            dest_key = file_info['dest_key']

            response = source_client.get_object(Bucket=source_bucket, Key=source_key)

            dest_client.upload_fileobj(
                response['Body'],
                dest_bucket,
                dest_key,
                Callback=progress_tracker
            )
            copied_count += 1

        logger.info(f"[claude code] Cross-bucket copy complete: {copied_count} files copied, {skipped_count} files skipped (already exist) from {source_bucket}/{source_prefix} to {dest_bucket}/{dest_prefix}")
        return True

    except Exception as e:
        logger.error(f"[claude code] Cross-bucket copy failed: {e}")
        return False


def sync_plan_to_claude_code_bucket(dynamic_generation_id: int, node_id: int) -> bool:
    """
    Copy plan file from the main storage bucket to the Claude Code bucket.
    Skips if the plan already exists in the destination with matching size.

    Args:
        dynamic_generation_id: Dynamic generation ID
        node_id: Node ID

    Returns:
        True if successful, False otherwise
    """
    try:
        plan_key = f"dynamic_generation/{dynamic_generation_id}/{node_id}/plan.json"

        # Main storage bucket (source)
        source_bucket = BUCKET_NAME
        source_client = boto3.client('s3')

        # Claude Code bucket (destination)
        dest_bucket = os.environ.get('CLAUDE_CODE_BUCKET_NAME') or BUCKET_NAME
        dest_profile = os.environ.get('CLAUDE_CODE_AWS_PROFILE') or None
        if dest_bucket == source_bucket and not dest_profile:
            return True
        dest_session = boto3.Session(profile_name=dest_profile)
        dest_client = dest_session.client('s3')

        # Get source file info
        source_head = source_client.head_object(Bucket=source_bucket, Key=plan_key)
        source_size = source_head.get('ContentLength', 0)

        # Check if plan already exists in the destination bucket with matching size
        if _check_file_exists_in_dest(dest_client, dest_bucket, plan_key, source_size):
            logger.info(f"[claude code] Plan already exists in destination bucket, skipping: {plan_key}")
            return True

        # Copy plan
        response = source_client.get_object(Bucket=source_bucket, Key=plan_key)
        body = response['Body'].read()

        dest_client.put_object(
            Bucket=dest_bucket,
            Key=plan_key,
            Body=body,
            ContentType='application/json'
        )

        logger.info(f"[claude code] Copied plan to Claude Code bucket: {plan_key}")
        return True

    except Exception as e:
        logger.error(f"[claude code] Failed to copy plan to Claude Code bucket: {e}")
        return False


def get_job_definition(program_language: str, preset_env: str) -> str:
    if program_language == "Python":
        if preset_env == "omicairn-py-sc-env":
            return PYTHON_JOB_DEFINITION_SCANPY
        elif preset_env == "omicairn-py-dyn-env":
            return PYTHON_JOB_DEFINITION_DYN
        elif preset_env == "omicairn-py-mebocost-env":
            return PYTHON_JOB_DEFINITION_MEBOCOST
        elif preset_env == "omicairn-py-scvelo-env":
            return PYTHON_JOB_DEFINITION_SCVELO
        elif preset_env == "omicairn-py-scfates-env":
            return PYTHON_JOB_DEFINITION_SCFATES
        else:
            return PYTHON_JOB_DEFINITION_DEFAULT
    elif program_language == "R":
        return R_JOB_DEFINITION
    elif program_language == "Bash":
        return BASH_JOB_DEFINITION
    else:
        raise ValueError("Unsupported programming language")

def get_job_definition_v2(program_language: str, preset_env: str, large: bool) -> str:
    program_language = program_language.strip().lower()
    if program_language == "python":
        if preset_env == "omicairn-py-sc-env":
            return PYTHON_JOB_DEFINITION_SCANPY_V2
        elif preset_env == "omicairn-py-dyn-env":
            return PYTHON_JOB_DEFINITION_DYN_V2
        elif preset_env == "omicairn-py-mebocost-env":
            return PYTHON_JOB_DEFINITION_MEBOCOST_V2
        elif preset_env == "omicairn-py-scvelo-env":
            return PYTHON_JOB_DEFINITION_SCVELO_V2
        elif preset_env == "omicairn-py-scfates-env":
            return PYTHON_JOB_DEFINITION_SCFATES_V2
        else:
            if large:
                return PYTHON_JOB_DEFINITION_LARGE_DEFAULT_V2
            else:
                return PYTHON_JOB_DEFINITION_DEFAULT_V2
    elif program_language == "r":
        if preset_env == "omicairn-r-metaboanalyst-env":
            return R_JOB_DEFINITION_V2_METABOANALYST
        return R_JOB_DEFINITION_V2
    else:
        raise ValueError("Unsupported programming language")


class ComputationLauncher:

    @staticmethod
    def launch_aws_computation(
        computation_id: str,
        previous_computation_id: str,
        program_language: str,
        computation_resource_configure: dict,
        preset_env: str,
        user_id: str,
        node_id: str
    ):
        vcpu = computation_resource_configure.get("vcpu", 4)
        memory = computation_resource_configure.get("ram", 8)
        timeout = computation_resource_configure.get("timeout", 300)

        job_definition = get_job_definition(program_language, preset_env)

        client = BatchClientFactory.create_batch_client()
        submit_result = client.submit_job(
            jobName=f"computation_{computation_id}",
            jobQueue=JOB_QUEUE,
            jobDefinition=job_definition,
            timeout={
                'attemptDurationSeconds': timeout
            },
            containerOverrides={
                'environment': [
                    {
                        "name": "COMPUTATION_ID",
                        "value": f"{computation_id}"
                    },
                    {
                        "name": "PREVIOUS_COMPUTATION_ID",
                        "value": f"{previous_computation_id}"
                    },
                    {
                        "name": "PORTER_TYPE",
                        "value": "s3-porter"
                    },
                    {
                        "name": "BUCKET_NAME",
                        "value": BUCKET_NAME
                    },
                    {
                        "name": "USER_ID",
                        "value": f"{user_id}"
                    },
                    {
                        "name": "NODE_ID",
                        "value": f"{node_id}"
                    }
                ],
                'resourceRequirements': [
                    {
                        'type': 'VCPU',
                        'value': str(vcpu)
                    },
                    {
                        'type': 'MEMORY',
                        'value': str(memory * 1024)
                    }
                ]
            },
            # retryStrategy={
            #     'attempts': 123,
            #     'evaluateOnExit': [
            #         {
            #             'onStatusReason': 'string',
            #             'onReason': 'string',
            #             'onExitCode': 'string',
            #             'action': 'RETRY' | 'EXIT'
            #         },
            #     ]
            # },
        )

        return submit_result["jobId"]

    @staticmethod
    def launch_aws_computation_v2(
        computation_id: str,
        previous_computation_id: str,
        program_language: str,
        computation_resource_configure: dict,
        preset_env: str,
        user_id: str,
        node_id: str,
        code_agent_config: dict = None,
        visualizer_agent_config: dict = None
    ):
        vcpu = computation_resource_configure.get("vcpu", 4)
        memory = computation_resource_configure.get("ram", 8)
        timeout = computation_resource_configure.get("timeout", 300)
        large = computation_resource_configure.get("large", False)

        job_definition = get_job_definition_v2(program_language, preset_env, large)
        job_queue = JOB_QUEUE if not large else LARGE_JOB_QUEUE

        client = BatchClientFactory.create_batch_client()
        submit_result = client.submit_job(
            jobName=f"computation_{computation_id}_v2",
            jobQueue=job_queue,
            jobDefinition=job_definition,
            timeout={
                'attemptDurationSeconds': timeout
            },
            containerOverrides={
                'environment': [
                    {
                        "name": "COMPUTATION_ID",
                        "value": f"{computation_id}"
                    },
                    {
                        "name": "PREVIOUS_COMPUTATION_ID",
                        "value": f"{previous_computation_id}"
                    },
                    {
                        "name": "PORTER_TYPE",
                        "value": "s3-porter"
                    },
                    {
                        "name": "BUCKET_NAME",
                        "value": BUCKET_NAME
                    },
                    {
                        "name": "USER_ID",
                        "value": f"{user_id}"
                    },
                    {
                        "name": "NODE_ID",
                        "value": f"{node_id}"
                    },
                    {
                        "name": "ENABLE_CODE_AGENT",
                        "value": "1" if (code_agent_config and code_agent_config.get("enable", False)) else "0"
                    },
                    {
                        "name": "CODE_AGENT_MODEL",
                        "value": code_agent_config.get("model", "gpt-4o-mini") if code_agent_config else "gpt-4o-mini"
                    },
                    {
                        "name": "CODE_AGENT_MAX_ATTEMPTS",
                        "value": str(code_agent_config.get("max_attempts", 10)) if code_agent_config else "10"
                    },
                    {
                        "name": "ENABLE_VISUALIZER_AGENT",
                        "value": "1" if (visualizer_agent_config and visualizer_agent_config.get("enable", False)) else "0"
                    },
                    {
                        "name": "VISUALIZER_AGENT_MODEL",
                        "value": visualizer_agent_config.get("model", "gpt-4o-mini") if visualizer_agent_config else "gpt-4o-mini"
                    },
                    {
                        "name": "VISUALIZER_DEMAND",
                        "value": str(visualizer_agent_config.get("visualizer_demand", 10)) if visualizer_agent_config else "10"
                    },
                    {
                        "name": "FIGURE_ALTERNATIVE_COUNTS",
                        "value": str(visualizer_agent_config.get("optional_figure_counts", 3)) if visualizer_agent_config else "3"
                    }
                ],
                'resourceRequirements': [
                    {
                        'type': 'VCPU',
                        'value': str(vcpu)
                    },
                    {
                        'type': 'MEMORY',
                        'value': str(memory * 1024)
                    }
                ]
            },
            # retryStrategy={
            #     'attempts': 123,
            #     'evaluateOnExit': [
            #         {
            #             'onStatusReason': 'string',
            #             'onReason': 'string',
            #             'onExitCode': 'string',
            #             'action': 'RETRY' | 'EXIT'
            #         },
            #     ]
            # },
        )

        return submit_result["jobId"]
    
    @staticmethod
    def launch_aws_notebook(
        computation_id: str,
        previous_computation_id: str,
        program_language: str,
        computation_resource_configure: dict,
        preset_env: str,
        user_id: str,
        node_id: str
    ):
        vcpu = computation_resource_configure.get("vcpu", 4)
        memory = computation_resource_configure.get("ram", 8)
        timeout = computation_resource_configure.get("timeout", 300)

        job_definition = os.environ.get("NOTEBOOK_JOB_DEFINITION", "<YOUR_NOTEBOOK_JOB_DEFINITION>")

        client = BatchClientFactory.create_batch_client()
        submit_result = client.submit_job(
            jobName=f"computation_{computation_id}_notebook",
            jobQueue=JOB_QUEUE,
            jobDefinition=job_definition,
            timeout={
                'attemptDurationSeconds': timeout
            },
            containerOverrides={
                'environment': [
                    {
                        "name": "COMPUTATION_ID",
                        "value": f"{computation_id}"
                    },
                    {
                        "name": "PREVIOUS_COMPUTATION_ID",
                        "value": f"{previous_computation_id}"
                    },
                    {
                        "name": "PORTER_TYPE",
                        "value": "s3-porter"
                    },
                    {
                        "name": "BUCKET_NAME",
                        "value": BUCKET_NAME
                    },
                    {
                        "name": "USER_ID",
                        "value": f"{user_id}"
                    },
                    {
                        "name": "NODE_ID",
                        "value": f"{node_id}"
                    }
                ],
                'resourceRequirements': [
                    {
                        'type': 'VCPU',
                        'value': str(vcpu)
                    },
                    {
                        'type': 'MEMORY',
                        'value': str(memory * 1024)
                    }
                ]
            },
        )

        return submit_result["jobId"]

    @staticmethod
    def launch_aws_claude_code(
        computation_id: str,
        previous_computation_id: str,
        computation_resource_configure: dict,
        user_id: str,
        node_id: str,
        dynamic_generation_id: int,
        claude_model: str = "sonnet",
        max_iterations: int = 100,
        source_data_ids: str = "[]",
        compute_type: str = "fargate"
    ):
        """
        Launch a Claude Code job on AWS Batch.

        Args:
            computation_id: The computation ID
            previous_computation_id: Previous computation for input files
            computation_resource_configure: Resource configuration dict
            user_id: User ID
            node_id: Node ID
            dynamic_generation_id: Dynamic generation ID (plan is fetched from S3)
            claude_model: Claude model to use (sonnet, opus, haiku)
            max_iterations: Maximum number of Claude Code turns
            source_data_ids: JSON array of source data IDs
            compute_type: Compute environment type - "fargate" (default) or "ec2"
        """
        vcpu = computation_resource_configure.get("vcpu", 4)
        memory = computation_resource_configure.get("ram", 16)
        timeout = computation_resource_configure.get("timeout", 129600)  # Timeout set by frontend
        claude_oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "")
        claude_code_aws_profile = os.environ.get('CLAUDE_CODE_AWS_PROFILE') or None
        claude_code_bucket = os.environ.get('CLAUDE_CODE_BUCKET_NAME') or BUCKET_NAME

        # Select job queue and definition based on compute type
        if compute_type == "ec2":
            claude_code_job_queue = CLAUDE_CODE_EC2_JOB_QUEUE
            job_definition = CLAUDE_CODE_EC2_JOB_DEFINITION
            logger.info(f"[claude code] Using EC2 compute environment (2TB disk)")
        else:
            claude_code_job_queue = os.environ.get('CLAUDE_CODE_JOB_QUEUE', '<YOUR_CLAUDE_CODE_JOB_QUEUE>')
            job_definition = CLAUDE_CODE_JOB_DEFINITION
            logger.info(f"[claude code] Using Fargate compute environment")

        try:
            session = boto3.Session(profile_name=claude_code_aws_profile)
            client = session.client('batch')
        except Exception as e:
            logger.warning(f"[claude code] Failed to create Claude Code profile client: {e}, falling back to default")
            client = BatchClientFactory.create_batch_client()

        submit_result = client.submit_job(
            jobName=f"computation_{computation_id}_claude_code",
            jobQueue=claude_code_job_queue,
            jobDefinition=job_definition,
            timeout={
                'attemptDurationSeconds': timeout
            },
            containerOverrides={
                'environment': [
                    {
                        "name": "COMPUTATION_ID",
                        "value": f"{computation_id}"
                    },
                    {
                        "name": "PREVIOUS_COMPUTATION_ID",
                        "value": f"{previous_computation_id}"
                    },
                    {
                        "name": "PORTER_TYPE",
                        "value": "s3-porter"
                    },
                    {
                        "name": "BUCKET_NAME",
                        "value": claude_code_bucket
                    },
                    {
                        "name": "USER_ID",
                        "value": f"{user_id}"
                    },
                    {
                        "name": "NODE_ID",
                        "value": f"{node_id}"
                    },
                    {
                        "name": "DYNAMIC_GENERATION_ID",
                        "value": str(dynamic_generation_id) if dynamic_generation_id else ""
                    },
                    {
                        "name": "CLAUDE_MODEL",
                        "value": claude_model
                    },
                    {
                        "name": "MAX_ITERATIONS",
                        "value": str(max_iterations)
                    },
                    {
                        "name": "CLAUDE_CODE_OAUTH_TOKEN",
                        "value": claude_oauth_token
                    },
                    {
                        "name": "MAIN_SERVER_HOST",
                        "value": os.environ.get("MAIN_SERVER_HOST", "")
                    },
                    {
                        "name": "COMPUTATION_SERVER_HOST",
                        "value": os.environ.get("COMPUTATION_SERVER_HOST", "")
                    },
                    {
                        "name": "SYSTEM_AGENT_KEY",
                        "value": SYSTEM_AGENT_KEY
                    },
                    {
                        "name": "SOURCE_DATA_IDS",
                        "value": source_data_ids
                    }
                ],
                'resourceRequirements': [
                    {
                        'type': 'VCPU',
                        'value': str(vcpu)
                    },
                    {
                        'type': 'MEMORY',
                        'value': str(memory * 1024)
                    }
                ]
            },
        )

        return submit_result["jobId"]

    @staticmethod
    def cancel_aws_computation(job_ident: str):
        client = BatchClientFactory.create_batch_client()
        if job_ident is not None:
            cancel_result = client.terminate_job(
                jobId=job_ident,
                reason="User cancelled"
            )
            logger.info("Cancel computation result: ")
            logger.info(cancel_result)
        else:
            logger.info("Computation has no job ident")

    @staticmethod
    def launch_local_computation(
        computation_id: str,
        previous_computation_id: str,
        program_language: str,
        preset_env: str,
        user_id: str,
        node_id: str
    ):
        queue_item = os.path.join(
            os.getenv("LOCAL_JOB_QUEUE"), f"{computation_id}")
        with open(queue_item, "w", encoding="utf-8") as f:
            json.dump({
                "computation_id": computation_id,
                "previous_computation_id": previous_computation_id,
                "program_language": program_language,
                "preset_env": preset_env,
                "user_id": user_id,
                "node_id": node_id
            }, f)
        logger.info(f"Write job to local job queue: {queue_item}")

    @staticmethod
    def launch_local_computation_v2(
        computation_id: str,
        previous_computation_id: str,
        program_language: str,
        preset_env: str,
        user_id: str,
        node_id: str,
        code_agent_config: dict = None,
        visualizer_agent_config: dict = None
    ):
        queue_item = os.path.join(
            os.getenv("LOCAL_JOB_QUEUE"), f"{computation_id}")
        with open(queue_item, "w", encoding="utf-8") as f:
            json.dump({
                "computation_id": computation_id,
                "previous_computation_id": previous_computation_id,
                "program_language": program_language,
                "preset_env": preset_env,
                "is_v2": True,
                "user_id": user_id,
                "node_id": node_id,
                "enable_code_agent": code_agent_config.get("enable", False) if code_agent_config else False,
                "code_agent_model": code_agent_config.get("model", "gpt-4o-mini") if code_agent_config else "gpt-4o-mini",
                "code_agent_max_attempts": code_agent_config.get("max_attempts", 10) if code_agent_config else 10,
                "enable_visualizer_agent": visualizer_agent_config.get("enable", False) if visualizer_agent_config else False,
                "visualizer_agent_model": visualizer_agent_config.get("model", "gpt-4o-mini") if visualizer_agent_config else "gpt-4o-mini",
                "visualizer_demand": visualizer_agent_config.get("visualizer_demand", "") if visualizer_agent_config else "",
                "optional_figure_counts": visualizer_agent_config.get("optional_figure_counts", 3) if visualizer_agent_config else 3
            }, f)
        logger.info(f"Write job to local job queue: {queue_item}")

    @staticmethod
    def launch_local_notebook(
        computation_id: str,
        previous_computation_id: str,
        program_language: str,
        preset_env: str,
        user_id: str,
        node_id: str
    ):
        queue_item = os.path.join(
            os.getenv("LOCAL_JOB_QUEUE"), f"{computation_id}")
        with open(queue_item, "w", encoding="utf-8") as f:
            json.dump({
                "computation_id": computation_id,
                "previous_computation_id": previous_computation_id,
                "program_language": program_language,
                "preset_env": preset_env,
                "user_id": user_id,
                "node_id": node_id,
                "is_notebook": True
            }, f)
        logger.info(f"Write notebook job to local job queue: {queue_item}")
        

    @staticmethod
    def cancel_local_computation(computation_id: str):
        canceled_signal_path = os.path.join(
            "/tmp/job-signal", f"{computation_id}.cancel")
        with open(canceled_signal_path, "w", encoding="utf-8") as f:
            f.write("cancel")

    @staticmethod
    def launch_dynamic_generation(dynamic_generation: DynamicGeneration, first_branch: DynamicGenerationBranch, user_id: str):
        dynamic_generation_id = dynamic_generation.generation_id
        _log_file = open(f"/tmp/dynamic_generation_{dynamic_generation_id}.log", "w")
        subprocess.Popen(
            ["python3", 'index.py'],
            cwd=os.path.join(CODE_SPACE_ROOT, 'handle_dynamic_generation'),
            env=_child_env({
                "DYNAMIC_GENERATION_ID": dynamic_generation_id,
                "DYNAMIC_GENERATION_BRANCH_ID": first_branch.id,
                "USER_ID": user_id,
                "PORTER_TYPE": 's3-porter',
            }),
            stdout=_log_file,
            stderr=subprocess.STDOUT
        )
        _log_file.close()
        return dynamic_generation_id

    @staticmethod
    def launch_dynamic_generation_with_plan(previous_node_id, dynamic_generation: DynamicGeneration, first_branch: DynamicGenerationBranch, user_id: str):
        dynamic_generation_id = dynamic_generation.generation_id
        subprocess.Popen(
            ["python3", 'index_with_plan.py'],
            cwd=os.path.join(CODE_SPACE_ROOT, 'handle_dynamic_generation'),
            env=_child_env({
                "PREVIOUS_NODE_ID": previous_node_id,
                "DYNAMIC_GENERATION_ID": dynamic_generation_id,
                "DYNAMIC_GENERATION_BRANCH_ID": first_branch.id,
                "USER_ID": user_id,
                "PORTER_TYPE": 's3-porter',
            })
        )
        return dynamic_generation_id

    @staticmethod
    def launch_visualizer(visualizer: Visualizer, user_id: str):
        visualizer_id = visualizer.id
        subprocess.Popen(
            ["python3", 'index.py'],
            cwd=os.path.join(CODE_SPACE_ROOT, 'handle_visualizer'),
            env=_child_env({
                "VISUALIZER_ID": visualizer_id,
                "USER_ID": user_id,
                "CURRENT_NODE_ID": visualizer.original_node_id,
                "PORTER_TYPE": 's3-porter',
            })
        )
        return visualizer_id

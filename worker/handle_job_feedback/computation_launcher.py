import boto3
from constants import (
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
    R_JOB_DEFINITION_V2, 
    PYTHON_JOB_DEFINITION_V2,
    PYTHON_JOB_DEFINITION_DEFAULT_V2,
    PYTHON_JOB_DEFINITION_LARGE_DEFAULT_V2,
    PYTHON_JOB_DEFINITION_SCANPY_V2,
    PYTHON_JOB_DEFINITION_DYN_V2,
    PYTHON_JOB_DEFINITION_MEBOCOST_V2,
    PYTHON_JOB_DEFINITION_SCVELO_V2,
    PYTHON_JOB_DEFINITION_SCFATES_V2,
    R_JOB_DEFINITION_V2_METABOANALYST
)

from constants import BUCKET_NAME
from constants import DEPLOY_ENV
from batch_client import BatchClientFactory
import os
import subprocess
import uuid
import json
import shutil
from logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("computation_launcher")


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
        code_agent_config: dict = None
    ):
        vcpu = computation_resource_configure.get("vcpu", 4)
        memory = computation_resource_configure.get("ram", 8)
        timeout = computation_resource_configure.get("timeout", 300)
        large = computation_resource_configure.get("large", False)

        job_definition = get_job_definition_v2(program_language, preset_env, large)
        client = BatchClientFactory.create_batch_client()
        submit_result = client.submit_job(
            jobName=f"computation_{computation_id}_v2",
            jobQueue=LARGE_JOB_QUEUE if large else JOB_QUEUE,
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
        code_agent_config: dict = None
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
                "code_agent_max_attempts": code_agent_config.get("max_attempts", 10) if code_agent_config else 10
            }, f)
        logger.info(f"Write job to local job queue: {queue_item}")
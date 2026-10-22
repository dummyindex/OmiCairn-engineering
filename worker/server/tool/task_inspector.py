from datetime import datetime, timedelta
import os
import boto3
from log.logger_factory import LoggerFactory
from dao.computation import computation_dao
from dao.node import node_dao
from constants.computation import ComputationState
from constants.node import NodeState, NodeType
from model.computation import Computation
from waiter.computation import ComputationWaiter
from tool.batch_client import batch_client_factory
from service.task import task_service
from service.dynamic_generation import dynamic_generation_service
from service.visualizer import visualizer_service
logger = LoggerFactory.get_logger("task_inspector")


def get_batch_client_for_computation(computation: Computation):
    """Get the appropriate batch client based on computation's node type."""
    try:
        node = node_dao.find_by_id(computation.node_id)
        if node and node.type == NodeType.CLAUDE_CODE_NODE.value:
            # Optional separate AWS profile for Claude Code jobs
            claude_code_aws_profile = os.environ.get('CLAUDE_CODE_AWS_PROFILE') or None
            session = boto3.Session(profile_name=claude_code_aws_profile)
            return session.client('batch')
    except Exception as e:
        logger.warning(f"Failed to determine batch client for computation {computation.id}: {e}")
    # Default batch client
    return batch_client_factory.create_batch_client()

INSPECT_INTERVAL = 60 * 5


class TaskInspector:

    def handle_running_computation(self, computation: Computation, job):
        started_at = job["startedAt"]
        logger.warning(
            f"Handled running computation: {computation.id}; started_at: {started_at}")
        task_service.handle_running_report(computation.id)

    def handle_succeeded_computation(self, computation: Computation, job):
        """
        Handle a computation that succeeded according to AWS Batch.
        This is a backup mechanism - normally the container should call /task/finished-report directly.
        """
        logger.info(f"Handling succeeded computation: {computation.id}")
        task_service.handle_finished_report(
            computation.id, "Job completed (detected by TaskInspector)", True, None)

    def handle_failed_computation(self, computation: Computation, status_reason):
        task_service.handle_failed_report(
            computation.id, status_reason, "no logs", False)

    def inspect_remains(self):
        try:
            generating_nodes = node_dao.find_by_state(
                NodeState.GENERATING.value)
            for node in generating_nodes:
                node_dao.update(node.id, {
                    "state": NodeState.FINISHED.value,
                })
            dynamic_generation_service.stop_all()
            beautifying_nodes = node_dao.find_by_state(
                NodeState.BEAUTIFYING.value)
            for node in beautifying_nodes:
                node_dao.update(node.id, {
                    "state": NodeState.FINISHED.value,
                })
            visualizer_service.stop_all()
            processing_computations = computation_dao.find_by_computation_state_list([
                ComputationState.QUEUING.value,
                ComputationState.RUNNING.value
            ])
            for computation in processing_computations:
                if computation.system_env == "aws-batch":
                    try:
                        batch_client = get_batch_client_for_computation(computation)
                        result = batch_client.describe_jobs(
                            jobs=[computation.job_ident])
                        jobs = result.get("jobs", [])
                        if len(jobs) == 0:
                            continue
                        job = jobs[0]
                        if job["status"] == "RUNNING":
                            self.handle_running_computation(computation, job)
                        elif job["status"] == "SUCCEEDED":
                            self.handle_succeeded_computation(computation, job)
                        elif job["status"] == "FAILED":
                            status_reason = job["statusReason"]
                            self.handle_failed_computation(
                                computation, status_reason)
                        else:
                            logger.warning(
                                f"[Remains Inspect] Unhandled computation status: {job['status']}")
                    except Exception as e:
                        logger.warning(f"[Remains Inspect] Failed to inspect computation {computation.id}: {e}")
        except Exception as e:
            logger.error(f"Failed to inspect on start: {e}")
            raise e

    def inspect_interval(self):
        # TODO: check if there are any timeout computations
        logger.info("[Interval Inspect] Inspecting running computations")
        running_computations = computation_dao.find_by_computation_state_list([
            ComputationState.QUEUING.value,
            ComputationState.RUNNING.value
        ])
        logger.info(
            f"[Interval Inspect] Found {len(running_computations)} running computations")
        if len(running_computations) == 0:
            return
        for computation in running_computations:
            logger.info(
                f"[Interval Inspect] Inspecting computation {computation.id}")
            if computation.system_env == "aws-batch":
                try:
                    batch_client = get_batch_client_for_computation(computation)
                    result = batch_client.describe_jobs(
                        jobs=[computation.job_ident])
                    jobs = result.get("jobs", [])
                    if len(jobs) == 0:
                        logger.warning(
                            f"[Interval Inspect] No job found for computation {computation.id}")
                        if computation.created_time is None:
                            self.handle_failed_computation(computation, "No created time found is computation record, it may be corrupted.")
                            continue
                    job = jobs[0]
                    job_status = job["status"]
                    logger.info(f"[Interval Inspect] Computation {computation.id} AWS Batch status: {job_status}")

                    if job_status == "SUCCEEDED":
                        logger.info(f"[Interval Inspect] Handling succeeded computation {computation.id}")
                        self.handle_succeeded_computation(computation, job)
                    elif job_status == "FAILED":
                        status_reason = job.get("statusReason", "Unknown error")
                        logger.info(f"[Interval Inspect] Handling failed computation {computation.id}: {status_reason}")
                        self.handle_failed_computation(computation, status_reason)
                    elif job_status == "RUNNING":
                        pass
                    else:
                        logger.info(f"[Interval Inspect] Unhandled job status: {job_status}")

                    logger.info(
                        f"[Interval Inspect] Inspected computation {computation.id}")
                except Exception as e:
                    logger.warning(f"[Interval Inspect] Failed to inspect computation {computation.id}: {e}")


task_inspector = TaskInspector()

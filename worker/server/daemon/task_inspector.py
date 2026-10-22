from datetime import datetime, timedelta
from threading import Thread
import time
import os
import boto3
from log.logger_factory import LoggerFactory
from dao.computation import computation_dao
from dao.node import node_dao
from constants.computation import ComputationState
from constants.node import NodeType
from model.computation import Computation
from waiter.computation import ComputationWaiter
from tool.batch_client import batch_client_factory
from db import alchemy_db as db
from service.task import task_service
logger = LoggerFactory.get_logger("task_inspector")


def get_batch_client_for_computation(computation: Computation):
    """Get the appropriate batch client based on computation's node type."""
    try:
        node = node_dao.find_by_id(computation.node_id)
        if node and node.type == NodeType.CLAUDE_CODE_NODE.value:
            claude_code_aws_profile = os.environ.get('CLAUDE_CODE_AWS_PROFILE') or None
            session = boto3.Session(profile_name=claude_code_aws_profile)
            return session.client('batch')
    except Exception as e:
        logger.warning(f"Failed to determine batch client for computation {computation.id}: {e}")
    
    return batch_client_factory.create_batch_client()

INSPECT_INTERVAL = 60 * 5


class TaskInspector:
    def __init__(self) -> None:
        self.app = None
        self.inspector = Thread(target=self.launch)
        self.inspector.daemon = True
        self.inspector.start()

    def set_app(self, app):
        self.app = app

    def handle_running_computation(self, computation: Computation, job):
        started_at = job["startedAt"]
        logger.warning(
            f"Handled running computation: {computation.id}; started_at: {started_at}")
        task_service.handle_running_report(computation.id)

    def handle_succeeded_computation(self, computation: Computation, job):
        task_service.handle_failed_report(
            computation.id, "Computation has been already out of time", "no logs", False)

    def handle_failed_computation(self, computation: Computation, job):
        status_reason = job["statusReason"]
        task_service.handle_failed_report(computation.id, status_reason, "no logs", False)

    def inspect_on_start(self):
        try:
            processing_computations = computation_dao.find_by_computation_state_list([
                ComputationState.QUEUING.value,
                ComputationState.RUNNING.value
            ])
            if len(processing_computations) == 0:
                return
            # Check each computation individually to handle different regions
            for computation in processing_computations:
                try:
                    batch_client = get_batch_client_for_computation(computation)
                    result = batch_client.describe_jobs(jobs=[computation.job_ident])
                    jobs = result.get("jobs", [])
                    if len(jobs) == 0:
                        continue
                    job = jobs[0]
                    if job["status"] == "RUNNING":
                        self.handle_running_computation(computation, job)
                    elif job["status"] == "SUCCEEDED":
                        self.handle_succeeded_computation(computation, job)
                    elif job["status"] == "FAILED":
                        self.handle_failed_computation(computation, job)
                except Exception as e:
                    logger.warning(f"Failed to inspect computation {computation.id}: {e}")
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to inspect on start: {e}")
            raise e

    def inspect_on_loop(self):
        # TODO: check if there are any timeout computations
        running_computations = computation_dao.find_by_computation_state_list([
            ComputationState.QUEUING.value,
            ComputationState.RUNNING.value
        ])
        if len(running_computations) == 0:
            return
        # Check each computation individually to handle different regions
        for computation in running_computations:
            try:
                batch_client = get_batch_client_for_computation(computation)
                result = batch_client.describe_jobs(jobs=[computation.job_ident])
                jobs = result.get("jobs", [])
                if len(jobs) == 0:
                    continue
                job = jobs[0]
                # mark the computation failed if the batch job has failed
                if job["status"] == "FAILED":
                    self.handle_failed_computation(computation, job)
            except Exception as e:
                logger.warning(f"Failed to inspect computation {computation.id}: {e}")
        db.session.commit()

    def launch(self):
        while self.app is None:
            logger.info("Waiting for app to be initialized.")
            time.sleep(2)
        logger.info("TaskInspector start running")
        with self.app.app_context():
            self.inspect_on_start()
        while True:
            try:
                with self.app.app_context():
                    self.inspect_on_loop()
            except Exception as e:
                logger.error(f"Failed to inspect on loop: {e}")
            time.sleep(INSPECT_INTERVAL)


task_inspector = TaskInspector()

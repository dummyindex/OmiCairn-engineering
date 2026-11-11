from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, BigInteger, Double, Text, and_, or_
from typing import List
import json
from datetime import datetime
from enum import Enum
import os
import time
import datetime
import logging
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

logging.basicConfig(
    level=logging.INFO,
    format="<FB Version Consumption Daemon> %(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("StatisticFbVersionConsumption")


class AugmentedEnum(Enum):
    def __hash__(self):
        return self.value.__hash__()

    def __eq__(self, other):
        if isinstance(other, type(self)) or isinstance(other, str):
            return self.value == other
        return False

    def __str__(self) -> str:
        return self.value


class InformType(AugmentedEnum):
    ANALYSIS_COLLABORATION_INVITATION = "analysis_collaboration_invitation"
    COMPUTATION_END_NOTICE = "computation_end_notice"
    TASK_END_NOTICE = "task_end_notice"


class Relation(AugmentedEnum):
    BELONG_TO = "belong-to"
    SHARED_WITH = "shared-with"


class Permission(AugmentedEnum):
    ADMIN = "admin"
    WRITE = "write"
    READ = "read"
    NO_PERMISSION = "no-permission"


class FigureExistType(AugmentedEnum):
    STATIC_IMAGE: str = "static-image"
    JSON_DATA: str = "json-data"
    IN_ADATA: str = "in-adata"


class SpecialUserId(AugmentedEnum):
    PUBLIC = 0
    ALL = -1
    SYSTEM = -2


class TaskNodeRelationType(AugmentedEnum):
    BELONG_TO = "belong to"
    BE_AFFECTED = "be affected"


class TaskState(AugmentedEnum):
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"


class DataState(AugmentedEnum):
    UPLOADING = "uploading"
    WAITING = "waiting"
    PREHANDLING = "prehandling"
    ERROR = "error"
    OK = "ok"


def create_folder_if_not_exist(folder_path):
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)


class PorterType(AugmentedEnum):
    S3_PORTER = "s3-porter"


class ComputationSystemEnv(AugmentedEnum):
    AWS_BATCH = "aws-batch"
    SERVER_LOCAL = "server-local"


class ComputationState(AugmentedEnum):
    PENDING = "pending"
    QUEUING = "queuing"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ComputationRetryProcessState(AugmentedEnum):
    RUNNING = "running"
    STOPPED = "stopped"


class NodeType(AugmentedEnum):
    DATA_NODE = "data node"
    COMPUTATION_NODE = "computation node"
    REPORT_NODE = "report node"
    DATA_NODE_V2 = "data node v2"
    COMPUTATION_NODE_V2 = "computation node v2"
    NOTEBOOK_NODE = "notebook node"


class NodeState(AugmentedEnum):
    ORIGINAL = "original"
    PENDING = "pending"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    DEBUGGING = "debugging"
    BEAUTIFYING = "beautifying"
    GENERATING = "generating"
    CANCELLED = "cancelled"


class NodeListFetchMode(AugmentedEnum):
    ANALYSIS = "analysis"
    IDX = "idx"


class CreatedFrom(AugmentedEnum):
    UPLOAD = "upload"
    COMPUTATION = "computation"


class DynamicGenerationState(AugmentedEnum):
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"


PORTER_TYPE = PorterType.S3_PORTER.value

BUCKET_NAME = os.environ.get("BUCKET_NAME")

DEPLOY_ENV = os.environ.get("DEPLOY_ENV", "dev")

GPT_WORKFLOW_SERVER_HOST = os.environ.get("GPT_WORKFLOW_SERVER_HOST")
GPT_WORKFLOW_SERVER_PORT = os.environ.get("GPT_WORKFLOW_SERVER_PORT")

NETWORK_PROXY_HOST = os.environ.get("NETWORK_PROXY_HOST")
NETWORK_PROXY_PORT = os.environ.get("NETWORK_PROXY_PORT")

# Optional outbound HTTP proxy; requests uses no proxy when unset.
PROXIES = {
    "http": f"http://{NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}",
    "https": f"http://{NETWORK_PROXY_HOST}:{NETWORK_PROXY_PORT}"
} if NETWORK_PROXY_HOST and NETWORK_PROXY_PORT else None

DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")
DB_PORT = os.environ.get("DB_PORT")

SYSTEM_AGENT_KEY = os.environ.get("SYSTEM_AGENT_KEY")

DYNAMIC_GENERATION_ID = os.environ.get("DYNAMIC_GENERATION_ID")
DYNAMIC_GENERATION_BRANCH_ID = os.environ.get("DYNAMIC_GENERATION_BRANCH_ID")

USER_ID = os.environ.get("USER_ID")

USER_REQUEST = os.environ.get("USER_REQUEST")

FUNCTION_BLOCK_VERSION_PREFIX = "function-block-version"

# Database connection configuration

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_size=10, max_overflow=10, pool_timeout=30, pool_recycle=-1,  connect_args={
        "connect_timeout": 60,
        "read_timeout": 60,
        "write_timeout": 60,
        "autocommit": True
    }
)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=True, bind=engine, expire_on_commit=False)

# Define the Base class
Base = declarative_base()


class FunctionBlockVersionV1(Base):
    __tablename__ = "function_block_version_v1"
    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment='ID')
    name = Column(String(100), nullable=False, comment='name')
    function_block_id = Column(
        BigInteger, nullable=False, comment='parent function block ID')
    args = Column(Text, comment='arguments')
    tag = Column(String(100), comment='tag')
    document_url = Column(Text, comment='documentation URL')
    description = Column(Text, comment='description')
    source = Column(String(100), comment='source')
    plot_only = Column(Boolean, comment='plot only')
    runtime_version = Column(String(45), comment='runtime version')
    created_time = Column(DateTime, comment='creation time')
    state = Column(String(50), comment='state')
    program_language = Column(String(45), comment='programming language')
    error_message = Column(Text, comment='error message')
    preset_env = Column(String(255), comment='preset environment')
    average_time = Column(Double, comment='average run time')
    is_v2 = Column(Boolean, nullable=True, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "functionBlockId": self.function_block_id,
            "args": self.args,
            "tag": self.tag,
            "documentUrl": self.document_url,
            "description": self.description,
            "source": self.source,
            "plotOnly": self.plot_only,
            "runtimeVersion": self.runtime_version,
            "createdTime": self.created_time.timestamp() * 1000,
            "state": self.state,
            "programLanguage": self.program_language,
            "errorMessage": self.error_message,
            "presetEnv": self.preset_env,
            "averageTime": self.average_time,
            "isV2": self.is_v2
        }


class Computation(Base):
    __tablename__ = 'computation'
    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment='ID')
    computation_params = Column(Text)
    created_time = Column(DateTime)
    start_time = Column(DateTime)
    duration = Column(Double)
    computation_state = Column(String(255))
    node_id = Column(BigInteger)
    source_data_ids = Column(String(255))
    result_data_id = Column(BigInteger)
    function_block_id = Column(BigInteger)
    function_block_version_id = Column(BigInteger)
    task_id = Column(BigInteger)
    error_description = Column(Text)
    job_ident = Column(String(200))
    optimized_error_description = Column(Text)
    buried = Column(Boolean)
    system_env = Column(String(100))
    computation_resource_configure = Column(String(200))
    previous_computation_id = Column(BigInteger)
    retry_process_id = Column(BigInteger)
    enable_code_agent = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "computationParams": self.computation_params,
            "createdTime": self.created_time.timestamp() * 1000,
            "startTime": self.start_time.timestamp() * 1000,
            "duration": self.duration,
            "computationState": self.computation_state,
            "nodeId": self.node_id,
            "sourceDataIds": self.source_data_ids,
            "resultDataId": self.result_data_id,
            "functionBlockId": self.function_block_id,
            "functionBlockVersionId": self.function_block_version_id,
            "taskId": self.task_id,
            "errorDescription": self.error_description,
            "jobIdent": self.job_ident,
            "optimizedErrorDescription": self.optimized_error_description,
            "buried": self.buried,
            "systemEnv": self.system_env,
            "computationResourceConfigure": self.computation_resource_configure,
            "previousComputationId": self.previous_computation_id,
            "retryProcessId": self.retry_process_id,
            "enableCodeAgent": self.enable_code_agent
        }


def find_all_function_block_version_v1():
    with SessionLocal() as session:
        function_block_version_v1_list = session.query(
            FunctionBlockVersionV1).all()
        return function_block_version_v1_list


def update_function_block_version_v1(fv_v_id, attr_dict):
    with SessionLocal() as session:
        session.query(FunctionBlockVersionV1).filter_by(
            id=fv_v_id).update(attr_dict)
        session.commit()


def find_computation_by_function_block_version_id(fbv_id):
    with SessionLocal() as session:
        computation_list = session.query(Computation).filter(
            and_(
                Computation.function_block_version_id == fbv_id,
                Computation.computation_state == ComputationState.FINISHED.value
            )
        )
        return computation_list


def statistic_fb_version_consumption(fb_v_id):
    computation_list = find_computation_by_function_block_version_id(fb_v_id)
    total_duration = 0
    total_count = 0
    for computation in computation_list:
        total_duration += computation.duration
        total_count += 1
    if total_count == 0:
        return -1
    return total_duration / total_count


def update():
    """Update average execution duration statistics for all Function Block Versions"""
    logger.info("Starting Function Block Version consumption statistics update")
    fb_v_list = find_all_function_block_version_v1()
    updated_count = 0
    no_data_count = 0
    
    for fb_v in fb_v_list:
        consumption = statistic_fb_version_consumption(fb_v.id)
        if consumption != -1:
            update_function_block_version_v1(
                fb_v.id, {"average_time": consumption})
            logger.info(
                f"Function block version {fb_v.id} consumption: {consumption}")
            updated_count += 1
        else:
            logger.debug(
                f"Function block version {fb_v.id} has no consumption data")
            no_data_count += 1
    
    logger.info(f"Statistics update completed: {updated_count} updated, {no_data_count} with no data")


def scheduled_update():
    """Scheduled job: update Function Block Version consumption statistics"""
    try:
        logger.info("[Scheduled Task] FB version consumption statistics update triggered")
        update()
    except Exception as e:
        logger.error(f"[Scheduled Task] Failed to update FB version consumption statistics: {e}", exc_info=True)


def main():
    logger.info("FB Version Consumption Statistics Daemon starting...")
    
    # Wait for the database connection to be ready
    logger.info("Waiting for database connection...")
    time.sleep(10)
    
    # Run statistics once immediately on startup
    logger.info("Running initial FB version consumption statistics...")
    try:
        update()
    except Exception as e:
        logger.error(f"Initial statistics update failed: {e}", exc_info=True)
        logger.info("Will retry in scheduled intervals...")
    
    # Create the scheduler
    logger.info("=" * 60)
    logger.info("Initializing APScheduler for periodic FB consumption statistics:")
    logger.info("  - Interval: every 2 hours")
    logger.info("=" * 60)
    
    scheduler = BlockingScheduler(
        timezone=os.environ.get('SCHEDULER_TIMEZONE', 'UTC'),
        job_defaults={
            'coalesce': True,  # Merge missed runs
            'max_instances': 1,  # At most one running instance per job
            'misfire_grace_time': 600  # Grace period for a missed run (10 minutes)
        }
    )
    
    # Add the scheduled job (every 2 hours)
    scheduler.add_job(
        func=scheduled_update,
        trigger=IntervalTrigger(hours=2),
        id='statistic_fb_version_consumption',
        name='Statistic FB Version Consumption',
        replace_existing=True
    )
    logger.info("✓ Added FB version consumption statistics job (every 2 hours)")
    
    # Start the scheduler (blocking)
    try:
        logger.info("=" * 60)
        logger.info("APScheduler started successfully")
        logger.info("FB Version Consumption Statistics Daemon is now running...")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("FB Version Consumption Statistics Daemon stopped by user")
        scheduler.shutdown(wait=False)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        scheduler.shutdown(wait=False)
        sys.exit(1)


if __name__ == '__main__':
    main()

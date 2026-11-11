from datetime import datetime
import json
import os
from typing import List
from constants import Relation, TaskNodeRelationType
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, BigInteger, Double, Text, and_, or_, Numeric, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from db_retry_decorator import retry_on_deadlock
from constants import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME
)

# Database connection configuration

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
    pool_size=1,  # Increase connection pool size
    max_overflow=1,  # Allow more overflow connections
    isolation_level="READ COMMITTED",  # Set the transaction isolation level to reduce lock scope
    connect_args={
        "connect_timeout": 60,
        "read_timeout": 60,
        "write_timeout": 60
        # Removed autocommit=True to avoid conflicting with SessionLocal's autocommit=False
    }
)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)  # autoflush set to False to reduce implicit flushes

# Define the Base class
Base = declarative_base()


class Analysis(Base):
    __tablename__ = 'analysis'
    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment='ID')
    created_time = Column(DateTime, nullable=False)
    disabled = Column(Boolean, nullable=False, default=False)
    name = Column(String(50), nullable=False)
    description = Column(String(200), nullable=True)
    bug_fixer_enabled = Column(Boolean, nullable=False, default=False)
    max_retry = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "createdTime": self.created_time.timestamp() * 1000,
            "disabled": self.disabled,
            "name": self.name,
            "description": self.description,
            "bugFixerEnabled": self.bug_fixer_enabled,
            "maxRetry": self.max_retry
        }


class Figure(Base):
    __tablename__ = "figure"
    id = Column(Integer, primary_key=True)
    computation_id = Column(BigInteger)
    figure_name = Column(String(255))
    figure_uuid = Column(String(255))
    created_time = Column(DateTime)
    node_id = Column(BigInteger)

    def to_dict(self):
        return {
            "id": self.id,
            "computationId": self.computation_id,
            "figureName": self.figure_name,
            "figureUuid": self.figure_uuid,
            "createdTime": self.created_time.timestamp() * 1000,
            "nodeId": self.node_id
        }


class FunctionBlockV1(Base):

    __tablename__ = "function_block_v1"

    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment='ID')
    name = Column(String(200), nullable=False)
    group_id = Column(BigInteger, nullable=False)
    current_version_id = Column(BigInteger, nullable=False)
    created_time = Column(DateTime, nullable=False)
    type = Column(String(50), nullable=False)
    occasion = Column(String(50), nullable=False)
    alt_name = Column(String(255), nullable=True)

    def to_dict(self):
        function_block_attrs_dict = dict()
        function_block_attrs_dict["id"] = self.id
        function_block_attrs_dict["name"] = self.name
        function_block_attrs_dict["groupId"] = self.group_id
        function_block_attrs_dict["currentVersionId"] = self.current_version_id
        function_block_attrs_dict["type"] = self.type
        function_block_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000 if self.created_time else None
        function_block_attrs_dict["occasion"] = self.occasion
        function_block_attrs_dict["altName"] = self.alt_name
        return function_block_attrs_dict


class FunctionBlockUserRelation(Base):
    __tablename__ = 'function_block_user_relation'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    function_block_id = Column(BigInteger)
    user_id = Column(BigInteger)
    relation = Column(String(100))
    permission = Column(String(100))

    def to_dict(self):
        function_block_user_relation_attrs_dict = dict()
        function_block_user_relation_attrs_dict["id"] = self.id
        function_block_user_relation_attrs_dict["functionBlockId"] = self.function_block_id
        function_block_user_relation_attrs_dict["userId"] = self.user_id
        function_block_user_relation_attrs_dict["relation"] = self.relation
        function_block_user_relation_attrs_dict["permission"] = self.permission
        return function_block_user_relation_attrs_dict


class FunctionBlockVersionV1(Base):
    __tablename__ = "function_block_version_v1"
    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment='ID')
    name = Column(String(100), nullable=False, comment='Name')
    function_block_id = Column(
        BigInteger, nullable=False, comment='Parent function block ID')
    args = Column(Text, comment='Arguments')
    tag = Column(String(100), comment='Tag')
    document_url = Column(Text, comment='Documentation URL')
    description = Column(Text, comment='Description')
    source = Column(String(100), comment='Source')
    plot_only = Column(Boolean, comment='Plot only')
    runtime_version = Column(String(45), comment='Runtime version')
    created_time = Column(DateTime, comment='Creation time')
    state = Column(String(50), comment='State')
    program_language = Column(String(45), comment='Programming language')
    error_message = Column(Text, comment='Error message')
    preset_env = Column(String(255), comment='Preset environment')
    average_time = Column(Double, comment='Average runtime')
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


class FunctionBlockGroup(Base):
    __tablename__ = "function_block_group"

    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment='ID')
    name = Column(String(255), nullable=False)
    created_time = Column(DateTime, nullable=False)
    serial_number = Column(BigInteger, nullable=True)
    alt_name = Column(String(255), nullable=True)

    def to_dict(self):
        function_block_group_attrs_dict = dict()
        function_block_group_attrs_dict["id"] = self.id
        function_block_group_attrs_dict["name"] = self.name
        function_block_group_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000
        function_block_group_attrs_dict["serialNumber"] = self.serial_number
        function_block_group_attrs_dict["altName"] = self.alt_name
        return function_block_group_attrs_dict


class FunctionBlockGroupUserRelation(Base):
    __tablename__ = 'function_block_group_user_relation'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    function_block_group_id = Column(BigInteger)
    user_id = Column(BigInteger)
    relation = Column(String(100))
    permission = Column(String(100))

    def to_dict(self):
        function_block_group_user_relation_attrs_dict = dict()
        function_block_group_user_relation_attrs_dict["id"] = self.id
        function_block_group_user_relation_attrs_dict["functionBlockGroupId"] = self.function_block_group_id
        function_block_group_user_relation_attrs_dict["userId"] = self.user_id
        function_block_group_user_relation_attrs_dict["relation"] = self.relation
        function_block_group_user_relation_attrs_dict["permission"] = self.permission
        return function_block_group_user_relation_attrs_dict


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
    is_review_error = Column(Boolean, default=False)
    s3_size_recorded = Column(Boolean, default=False)

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
            "enableCodeAgent": self.enable_code_agent,
            "isReviewError": self.is_review_error,
            "s3SizeRecorded": self.s3_size_recorded
        }


class ComputationRetryProcess(Base):
    __tablename__ = 'computation_retry_process'
    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment='Primary Key')
    node_id = Column(BigInteger, nullable=False, comment='Node ID')
    new_node_id = Column(
        BigInteger, nullable=True, comment='New Node ID')
    task_id = Column(BigInteger, nullable=False, comment='Task ID')
    analysis_id = Column(BigInteger, nullable=False, comment='Analysis ID')
    state = Column(String(100), nullable=False,
                   default='pending', comment='Status')
    max_retry = Column(Integer, nullable=False,
                       default=5, comment='Max Retry')
    rest_retry = Column(Integer, nullable=False,
                        default=5, comment='Rest Retry')
    user_id = Column(BigInteger, nullable=False, comment='User ID')
    created_time = Column(DateTime, nullable=False, comment='Created Time')
    completed_time = Column(
        DateTime, nullable=True, comment='Completed Time')
    user_prompt = Column(Text, nullable=True, comment='User Prompt')
    llm_model = Column(String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nodeId": self.node_id,
            "newNodeId": self.new_node_id,
            "taskId": self.task_id,
            "analysisId": self.analysis_id,
            "state": self.state,
            "maxRetry": self.max_retry,
            "restRetry": self.rest_retry,
            "userId": self.user_id,
            "createdTime": self.created_time.timestamp() * 1000,
            "completedTime": None if self.completed_time is None else self.completed_time.timestamp() * 1000,
            "userPrompt": self.user_prompt,
            "llmModel": self.llm_model
        }


class Data(Base):
    __tablename__ = "data"
    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False)
    created_time = Column(DateTime, nullable=False)
    collected = Column(Boolean, nullable=False)
    upload_type = Column(String(255), nullable=False)
    species = Column(String(255), nullable=True)
    created_from = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    state = Column(String(30), nullable=False)
    error_message = Column(Text, nullable=True)
    buried = Column(Boolean, nullable=False)
    summary = Column(Text, nullable=True)
    data_size = Column(BigInteger, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "createdTime": self.created_time.timestamp() * 1000,
            "collected": self.collected,
            "uploadType": self.upload_type,
            "species": self.species,
            "createdFrom": self.created_from,
            "description": self.description,
            "state": self.state,
            "errorMessage": self.error_message,
            "buried": self.buried,
            "summary": self.summary,
            "dataSize": self.data_size
        }


class Node(Base):
    __tablename__ = 'node'
    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment='ID')
    created_time = Column(DateTime)
    name = Column(String(255))
    x = Column(Double)
    y = Column(Double)
    type = Column(String(255))
    function_block_id = Column(BigInteger)
    function_block_version_id = Column(BigInteger)
    data_id = Column(BigInteger)
    computation_params = Column(Text)
    state = Column(String(255))
    analysis_id = Column(BigInteger)
    locked = Column(Boolean)
    tag = Column(String(200))
    system_env = Column(String(100))
    computation_resource_configure = Column(String(200))
    dynamic_generation_id = Column(BigInteger)
    dynamic_generation_locked = Column(Boolean)
    annotated = Column(Boolean, default=False)
    avg_duration = Column(Double, default=0.0)
    visualizer_id = Column(BigInteger)
    visualizer_previous_node_id = Column(BigInteger)
    visualizer_locked = Column(Boolean, default=False)
    is_review_error = Column(Boolean, default=False)
    replan_source_id = Column(BigInteger)

    def to_dict(self):
        return {
            "id": self.id,
            "createdTime": self.created_time.timestamp() * 1000,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "type": self.type,
            "functionBlockId": self.function_block_id,
            "functionBlockVersionId": self.function_block_version_id,
            "dataId": self.data_id,
            "computationParams": self.computation_params,
            "state": self.state,
            "analysisId": self.analysis_id,
            "locked": self.locked,
            "tag": self.tag,
            "systemEnv": self.system_env,
            "computationResourceConfigure": self.computation_resource_configure,
            "dynamicGenerationId": self.dynamic_generation_id,
            "dynamicGenerationLocked": self.dynamic_generation_locked,
            "annotated": self.annotated,
            "avgDuration": self.avg_duration,
            "visualizerId": self.visualizer_id,
            "visualizerPreviousNodeId": self.visualizer_previous_node_id,
            "visualizerLocked": self.visualizer_locked,
            "isReviewError": self.is_review_error,
            "replanSourceId": self.replan_source_id
        }


class Task(Base):
    __tablename__ = "task"
    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment='ID')
    created_time = Column(DateTime)
    analysis_id = Column(BigInteger)
    state = Column(String(50))

    def to_dict(self):
        return {
            "id": self.id,
            "createdTime": self.created_time.timestamp() * 1000,
            "analysisId": self.analysis_id,
            "state": self.state
        }


class TaskNodeRelation(Base):
    __tablename__ = "task_node_relation"
    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment='ID')
    task_id = Column(BigInteger)
    node_id = Column(BigInteger)
    created_time = Column(DateTime)
    is_root = Column(Boolean)
    is_leaf = Column(Boolean)
    relation_type = Column(String(50))

    def to_dict(self):
        return {
            "id": self.id,
            "taskId": self.task_id,
            "nodeId": self.node_id,
            "createdTime": self.created_time.timestamp() * 1000,
            "isRoot": self.is_root,
            "isLeaf": self.is_leaf,
            "relationType": self.relation_type
        }


class TaskEdgeRelation(Base):
    __tablename__ = "task_edge_relation"
    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment='ID')
    task_id = Column(BigInteger)
    edge_id = Column(BigInteger)
    created_time = Column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "taskId": self.task_id,
            "edgeId": self.edge_id,
            "createdTime": self.created_time.timestamp() * 1000
        }


class Edge(Base):
    __tablename__ = 'edge'
    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment='ID')
    created_time = Column(DateTime)
    source_node_id = Column(BigInteger)
    target_node_id = Column(BigInteger)
    analysis_id = Column(BigInteger)

    def to_dict(self):
        return {
            "id": self.id,
            "createdTime": self.created_time.timestamp() * 1000,
            "sourceNodeId": self.source_node_id,
            "targetNodeId": self.target_node_id,
            "analysisId": self.analysis_id
        }


class ComputationUserRelation(Base):
    __tablename__ = 'computation_user_relation'
    id = Column(BigInteger, primary_key=True)
    computation_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    relation = Column(String(100), nullable=False)
    permission = Column(String(100), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "computationId": self.computation_id,
            "userId": self.user_id,
            "relation": self.relation,
            "permission": self.permission
        }


class User(Base):
    __tablename__ = 'user'
    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment='ID')
    user_name = Column(String(30), nullable=True)
    phone_number = Column(String(18), nullable=False, unique=True)
    password = Column(String(255), nullable=False)  # werkzeug password hash; matches backend model/user.py
    created_time = Column(DateTime, nullable=False)
    disabled = Column(Boolean, nullable=False, default=False)
    email = Column(String(200), nullable=True)
    extend1 = Column(String(50), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "userName": self.user_name,
            "phoneNumber": self.phone_number,
            "createdTime": self.created_time.timestamp() * 1000,
            "disabled": self.disabled,
            "email": self.email,
            "extend1": self.extend1
        }


class Inform(Base):
    __tablename__ = 'inform'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sender_id = Column(BigInteger, nullable=False)
    receiver_id = Column(BigInteger, nullable=False)
    created_time = Column(DateTime, nullable=False)
    have_read = Column(Boolean, nullable=False, default=False)
    type = Column(String(255), nullable=False)
    payload = Column(Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "senderId": self.sender_id,
            "receiverId": self.receiver_id,
            "createdTime": self.created_time.timestamp() * 1000,
            "haveRead": self.have_read,
            "type": self.type,
            "payload": self.payload
        }


class DataUserRelation(Base):
    __tablename__ = 'data_user_relation'
    id = Column(BigInteger, primary_key=True)
    data_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    relation = Column(String(100), nullable=False)
    permission = Column(String(100), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "dataId": self.data_id,
            "userId": self.user_id,
            "relation": self.relation,
            "permission": self.permission
        }


class NodeUserRelation(Base):
    __tablename__ = 'node_user_relation'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    node_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    relation = Column(String(100), nullable=False)
    permission = Column(String(100), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "nodeId": self.node_id,
            "userId": self.user_id,
            "relation": self.relation,
            "permission": self.permission
        }


class TaskUserRelation(Base):
    __tablename__ = 'task_user_relation'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    relation = Column(String(100), nullable=False)
    permission = Column(String(100), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "taskId": self.task_id,
            "userId": self.user_id,
            "relation": self.relation,
            "permission": self.permission
        }


class BugFixerRecord(Base):
    __tablename__ = 'bug_fixer_record'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    analysis_id = Column(BigInteger, nullable=False)
    node_id = Column(BigInteger, nullable=False)
    function_block_id = Column(BigInteger, nullable=False)
    function_block_version_id = Column(BigInteger, nullable=False)
    computation_id = Column(BigInteger, nullable=False)
    gpt_api_input = Column(Text, nullable=False)
    gpt_api_output = Column(Text, nullable=False)
    created_time = Column(DateTime, nullable=False)
    retry_id = Column(BigInteger, nullable=False)
    to_create_function = Column(Boolean, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "analysisId": self.analysis_id,
            "nodeId": self.node_id,
            "functionBlockId": self.function_block_id,
            "functionBlockVersionId": self.function_block_version_id,
            "computationId": self.computation_id,
            "gptApiInput": self.gpt_api_input,
            "gptApiOutput": self.gpt_api_output,
            "createdTime": self.created_time.timestamp() * 1000,
            "retryId": self.retry_id,
            "toCreateFunction": self.to_create_function
        }


class DynamicGeneration(Base):
    __tablename__ = 'dynamic_generation'
    generation_id = Column(
        BigInteger, primary_key=True, autoincrement=True)
    analysis_id = Column(BigInteger)
    previous_node_id = Column(BigInteger)
    previous_computation_id = Column(BigInteger)
    max_node = Column(Integer)
    max_branch = Column(Integer)
    user_request = Column(Text)
    created_time = Column(DateTime)
    state = Column(String(50))
    rest_node_count = Column(Integer)
    computation_resource_configure = Column(String(150))
    generation_mode = Column(String(50))
    file_ids = Column(Text)
    max_debug = Column(Integer)
    plan_name = Column(String(255))
    plan_status = Column(String(255))
    plan_status_message = Column(String(255))
    llm_model = Column(String(255), nullable=True)
    version = Column(String(24), nullable=True)
    replan_count_limit = Column(Integer, nullable=True)

    def to_dict(self):
        dynamic_generation_attrs_dict = dict()
        dynamic_generation_attrs_dict["generationId"] = self.generation_id
        dynamic_generation_attrs_dict["analysisId"] = self.analysis_id
        dynamic_generation_attrs_dict["previousNodeId"] = self.previous_node_id
        dynamic_generation_attrs_dict["previousComputationId"] = self.previous_computation_id
        dynamic_generation_attrs_dict["maxNode"] = self.max_node
        dynamic_generation_attrs_dict["maxBranch"] = self.max_branch
        dynamic_generation_attrs_dict["userRequest"] = self.user_request
        dynamic_generation_attrs_dict["createdTime"] = self.created_time and self.created_time.timestamp(
        ) * 1000
        dynamic_generation_attrs_dict["state"] = self.state
        dynamic_generation_attrs_dict["restNodeCount"] = self.rest_node_count
        dynamic_generation_attrs_dict["computationResourceConfigure"] = self.computation_resource_configure
        dynamic_generation_attrs_dict["generationMode"] = self.generation_mode
        dynamic_generation_attrs_dict["fileIds"] = self.file_ids
        dynamic_generation_attrs_dict["maxDebug"] = self.max_debug
        dynamic_generation_attrs_dict["planName"] = self.plan_name
        dynamic_generation_attrs_dict["planStatus"] = self.plan_status
        dynamic_generation_attrs_dict["planStatusMessage"] = self.plan_status_message
        dynamic_generation_attrs_dict["llmModel"] = self.llm_model
        dynamic_generation_attrs_dict["version"] = self.version
        dynamic_generation_attrs_dict["replanCountLimit"] = self.replan_count_limit
        return dynamic_generation_attrs_dict


class DynamicGenerationBranch(Base):
    __tablename__ = 'dynamic_generation_branch'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dynamic_generation_id = Column(BigInteger, nullable=False)
    end_node_id = Column(BigInteger, nullable=False)
    state = Column(String(255), nullable=False)
    created_time = Column(DateTime, nullable=False)
    updated_time = Column(DateTime, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "dynamicGenerationId": self.dynamic_generation_id,
            "endNodeId": self.end_node_id,
            "state": self.state,
            "createdTime": self.created_time.timestamp() * 1000 if self.created_time else None,
            "updatedTime": self.updated_time.timestamp() * 1000 if self.updated_time else None
        }


class Visualizer(Base):
    __tablename__ = 'visualizer'
    id = Column(Integer, primary_key=True)
    original_node_id = Column(Integer, nullable=False)
    original_computation_id = Column(Integer, nullable=False)
    analysis_id = Column(Integer, nullable=False)
    max_count = Column(Integer, nullable=False, default=0)
    rest_count = Column(Integer, nullable=False, default=0)
    state = Column(String(50), nullable=True)
    user_prompt = Column(Text, nullable=False)
    user_id = Column(Integer, nullable=False)
    created_time = Column(DateTime, nullable=False)
    generation_mode = Column(String(50))
    computation_resource_configure = Column(String(255))

    def to_dict(self):
        visualizer_attrs_dict = dict()
        visualizer_attrs_dict["id"] = self.id
        visualizer_attrs_dict["originalNodeId"] = self.original_node_id
        visualizer_attrs_dict["originalComputationId"] = self.original_computation_id
        visualizer_attrs_dict["analysisId"] = self.analysis_id
        visualizer_attrs_dict["maxCount"] = self.max_count
        visualizer_attrs_dict["restCount"] = self.rest_count
        visualizer_attrs_dict["state"] = self.state
        visualizer_attrs_dict["userPrompt"] = self.user_prompt
        visualizer_attrs_dict["userId"] = self.user_id
        visualizer_attrs_dict["createdTime"] = self.created_time and self.created_time.timestamp(
        ) * 1000
        visualizer_attrs_dict["generationMode"] = self.generation_mode
        visualizer_attrs_dict["computationResourceConfigure"] = self.computation_resource_configure
        return visualizer_attrs_dict


class DynamicGenerationSession(Base):
    __tablename__ = "dynamic_generation_session"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dynamic_generation_id = Column(BigInteger)
    source_node_id = Column(BigInteger)
    consumption_id = Column(BigInteger)
    is_valid = Column(Boolean, default=True)
    errors = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    type = Column(String(255), nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "dynamicGenerationId": self.dynamic_generation_id,
            "sourceNodeId": self.source_node_id,
            "consumptionId": self.consumption_id,
            "isValid": self.is_valid,
            "errors": self.errors,
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "type": self.type,
            "startTime": self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else None,
            "endTime": self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None
        }

class LLMConsumption(Base):
    __tablename__ = 'llm_consumption'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    reasoning_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=False)
    cost = Column(Numeric(10, 4), nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    model = Column(String(255), nullable=False)
    functionality = Column(String(255), nullable=False)
    functionality_task_id = Column(BigInteger, nullable=False)
    node_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "promptTokens": self.prompt_tokens,
            "completionTokens": self.completion_tokens,
            "reasoningTokens": self.reasoning_tokens,
            "totalTokens": self.total_tokens,
            "cost": str(self.cost) if self.cost is not None else None,
            "createdAt": self.created_at and self.created_at.timestamp() * 1000,
            "model": self.model,
            "functionality": self.functionality,
            "functionalityTaskId": self.functionality_task_id,
            "nodeId": self.node_id,
            "userId": self.user_id
        }

class ComputationFileSize(Base):
    __tablename__ = "computation_file_size"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    computation_id = Column(BigInteger, nullable=False)
    log_size = Column(BigInteger)
    options_size = Column(BigInteger)
    output_size = Column(BigInteger)
    review_error_size = Column(BigInteger)
    result_size = Column(BigInteger)
    report_size = Column(BigInteger)
    figures_size = Column(BigInteger)
    created_time = Column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "computationId": self.computation_id,
            "logSize": self.log_size,
            "optionsSize": self.options_size,
            "outputSize": self.output_size,
            "reviewErrorSize": self.review_error_size,
            "resultSize": self.result_size,
            "reportSize": self.report_size,
            "figuresSize": self.figures_size,
            "createdTime": self.created_time.strftime("%Y-%m-%d %H:%M:%S") if self.created_time else None
        }



def find_computation_by_id(computation_id) -> Computation:
    with SessionLocal() as session:
        result = session.query(Computation).filter(Computation.id == computation_id).first()
        if result:
            session.expunge(result)
        return result


def find_computation_by_retry_process_id(retry_process_id) -> List[Computation]:
    with SessionLocal() as session:
        results = session.query(Computation).filter(Computation.retry_process_id == retry_process_id).order_by(Computation.created_time.asc()).all()
        for result in results:
            session.expunge(result)
        return results


@retry_on_deadlock(max_retries=3)
def update_computation(computation_id, attrs):
    with SessionLocal() as session:
        try:
            session.query(Computation).filter(
                Computation.id == computation_id).update(attrs, synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


@retry_on_deadlock(max_retries=3)
def update_node(node_id, attrs):
    with SessionLocal() as session:
        try:
            session.query(Node).filter(Node.id == node_id).update(attrs, synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


@retry_on_deadlock(max_retries=3)
def update_node_batch(node_id_list, attrs):
    if not node_id_list:
        return
    with SessionLocal() as session:
        try:
            # Sort the ID list so that concurrent transactions lock rows in the same order, avoiding deadlocks
            sorted_node_id_list = sorted(node_id_list)
            session.query(Node).filter(
                Node.id.in_(sorted_node_id_list)).update(attrs, synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


@retry_on_deadlock(max_retries=3)
def update_task(task_id, attrs):
    with SessionLocal() as session:
        try:
            session.query(Task).filter(Task.id == task_id).update(attrs, synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


@retry_on_deadlock(max_retries=3)
def update_data(data_id, attrs):
    with SessionLocal() as session:
        try:
            session.query(Data).filter(Data.id == data_id).update(attrs, synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def find_task_by_id(task_id) -> Task:
    with SessionLocal() as session:
        result = session.query(Task).filter(Task.id == task_id).first()
        if result:
            session.expunge(result)
        return result


def find_computation_user_relation_by_computation_id_and_relation(computation_id, relation) -> List[ComputationUserRelation]:
    with SessionLocal() as session:
        results = session.query(ComputationUserRelation).filter(
            and_(
                ComputationUserRelation.computation_id == computation_id,
                ComputationUserRelation.relation == relation
            )
        ).all()
        for result in results:
            session.expunge(result)
        return results


def find_user_by_id(user_id) -> User:
    with SessionLocal() as session:
        result = session.query(User).filter(User.id == user_id).first()
        if result:
            session.expunge(result)
        return result


def find_edge_by_source_node_id(source_node_id) -> List[Edge]:
    with SessionLocal() as session:
        results = session.query(Edge).filter(
            Edge.source_node_id == source_node_id
        ).all()
        for result in results:
            session.expunge(result)
        return results


def find_edge_by_target_node_id(target_node_id) -> List[Edge]:
    with SessionLocal() as session:
        results = session.query(Edge).filter(
            Edge.target_node_id == target_node_id
        ).all()
        for result in results:
            session.expunge(result)
        return results


def find_all_after_edges(node_id) -> List[Edge]:
    next_edge_path = find_edge_by_source_node_id(node_id)
    index = 0
    while index < len(next_edge_path):
        next_edge = next_edge_path[index]
        next_edge_path += find_edge_by_source_node_id(
            next_edge.target_node_id
        )
        index += 1
    return next_edge_path


def find_edges_by_target_node_id_list(target_node_id_list) -> List[Edge]:
    if not target_node_id_list:
        return []
    with SessionLocal() as session:
        results = session.query(Edge).filter(
            Edge.target_node_id.in_(target_node_id_list)
        ).all()
        for result in results:
            session.expunge(result)
        return results


def find_task_node_relations_by_task_id_and_relation_type(task_id, relation_type) -> List[TaskNodeRelation]:
    with SessionLocal() as session:
        results = session.query(TaskNodeRelation).filter(
            and_(
                TaskNodeRelation.task_id == task_id,
                TaskNodeRelation.relation_type == relation_type
            )
        ).all()
        for result in results:
            session.expunge(result)
        return results


@retry_on_deadlock(max_retries=3)
def delete_task_node_relations_by_task_id_and_node_id_list(task_id, node_id_list):
    if not node_id_list:
        return
    with SessionLocal() as session:
        try:
            # Sort the ID list so that concurrent transactions lock rows in the same order
            sorted_node_id_list = sorted(node_id_list)
            session.query(TaskNodeRelation).filter(
                and_(
                    TaskNodeRelation.task_id == task_id,
                    TaskNodeRelation.node_id.in_(sorted_node_id_list)
                )
            ).delete(synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


@retry_on_deadlock(max_retries=3)
def delete_task_edge_relations_by_task_id_and_edge_id_list(task_id, edge_id_list):
    if not edge_id_list:
        return
    with SessionLocal() as session:
        try:
            # Sort the ID list so that concurrent transactions lock rows in the same order
            sorted_edge_id_list = sorted(edge_id_list)
            session.query(TaskEdgeRelation).filter(
                and_(
                    TaskEdgeRelation.task_id == task_id,
                    TaskEdgeRelation.edge_id.in_(sorted_edge_id_list)
                )
            ).delete(synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def insert_inform(inform: Inform) -> None:
    with SessionLocal() as session:
        try:
            session.add(inform)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def insert_node(node: Node):
    with SessionLocal() as session:
        try:
            session.add(node)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def insert_computation(computation: Computation) -> None:
    with SessionLocal() as session:
        try:
            session.add(computation)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def insert_fb_group_user_relation(relation: FunctionBlockGroupUserRelation) -> None:
    with SessionLocal() as session:
        try:
            session.add(relation)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def insert_fb_group(fb_group: FunctionBlockGroup) -> None:
    with SessionLocal() as session:
        try:
            session.add(fb_group)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def insert_bug_fixer_record(record: BugFixerRecord) -> None:
    with SessionLocal() as session:
        try:
            session.add(record)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


@retry_on_deadlock(max_retries=3)
def update_bug_fixer_record(record_id, attrs) -> None:
    with SessionLocal() as session:
        try:
            session.query(BugFixerRecord).filter(
                BugFixerRecord.id == record_id).update(attrs, synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def find_analysis_by_id(analysis_id) -> Analysis:
    with SessionLocal() as session:
        result = session.query(Analysis).filter(Analysis.id == analysis_id).first()
        if result:
            session.expunge(result)
        return result


def find_node_by_id(node_id) -> Node:
    with SessionLocal() as session:
        result = session.query(Node).filter(Node.id == node_id).first()
        if result:
            session.expunge(result)
        return result

def find_node_by_replan_source_id(replan_source_id) -> List[Node]:
    if replan_source_id is None:
        return []
    with SessionLocal() as session:
        result = session.query(Node).filter(Node.replan_source_id == replan_source_id).all()
        if result:
            for node in result:
                session.expunge(node)
        return result


def find_edges_by_target_node_id(target_node_id) -> List[Edge]:
    with SessionLocal() as session:
        results = session.query(Edge).filter(
            Edge.target_node_id == target_node_id
        ).all()
        for result in results:
            session.expunge(result)
        return results


def find_edges_by_target_node_id_list(target_node_id_list) -> List[Edge]:
    if not target_node_id_list:
        return []
    with SessionLocal() as session:
        results = session.query(Edge).filter(
            Edge.target_node_id.in_(target_node_id_list)
        ).all()
        for result in results:
            session.expunge(result)
        return results


def find_next_edges_in_task(node_id, task_id):
    with SessionLocal() as session:
        results = session.query(
            Edge
        ).join(
            TaskEdgeRelation,
            Edge.id == TaskEdgeRelation.edge_id
        ).filter(
            and_(
                Edge.source_node_id == node_id,
                TaskEdgeRelation.task_id == task_id
            )
        ).all()
        for result in results:
            session.expunge(result)
        return results


def find_computation_retry_process_by_id(retry_process_id) -> ComputationRetryProcess:
    if retry_process_id is None:
        return None
    with SessionLocal() as session:
        result = session.query(ComputationRetryProcess).filter(ComputationRetryProcess.id == retry_process_id).first()
        if result:
            session.expunge(result)
        return result


def find_latest_computation_by_retry_process_id(retry_process_id) -> Computation:
    with SessionLocal() as session:
        result = session.query(Computation).filter(
            Computation.retry_process_id == retry_process_id
        ).order_by(
            Computation.created_time.desc()
        ).first()
        if result:
            session.expunge(result)
        return result


@retry_on_deadlock(max_retries=3)
def update_computation_retry_process(retry_process_id, attrs) -> None:
    with SessionLocal() as session:
        try:
            session.query(ComputationRetryProcess).filter(
                ComputationRetryProcess.id == retry_process_id).update(attrs, synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def find_latest_computation_by_node_id(node_id) -> Computation:
    with SessionLocal() as session:
        result = session.query(Computation).filter(
            Computation.node_id == node_id
        ).order_by(
            Computation.created_time.desc()
        ).first()
        if result:
            session.expunge(result)
        return result


def insert_computation_retry_process(retry_process: ComputationRetryProcess) -> None:
    with SessionLocal() as session:
        try:
            session.add(retry_process)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def find_data_by_id(data_id) -> Data:
    with SessionLocal() as session:
        result = session.query(Data).filter(Data.id == data_id).first()
        if result:
            session.expunge(result)
        return result




def insert_computation(computation: Computation) -> Computation:
    with SessionLocal() as session:
        try:
            session.add(computation)
            session.commit()
            session.refresh(computation)
            session.expunge(computation)
            return computation
        except Exception as e:
            session.rollback()
            raise e


def insert_computation_user_relation(relation: ComputationUserRelation) -> None:
    with SessionLocal() as session:
        try:
            session.add(relation)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e



def insert_data_user_relation(relation: DataUserRelation) -> None:
    with SessionLocal() as session:
        try:
            session.add(relation)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def insert_node_user_relation(relation: NodeUserRelation) -> None:
    with SessionLocal() as session:
        try:
            session.add(relation)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def insert_data(data: Data) -> None:
    with SessionLocal() as session:
        try:
            session.add(data)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def find_fb_by_id(fb_id) -> FunctionBlockV1:
    with SessionLocal() as session:
        result = session.query(FunctionBlockV1).filter(FunctionBlockV1.id == fb_id).first()
        if result:
            session.expunge(result)
        return result


def find_fb_version_by_id(fb_version_id) -> FunctionBlockVersionV1:
    with SessionLocal() as session:
        result = session.query(FunctionBlockVersionV1).filter(FunctionBlockVersionV1.id == fb_version_id).first()
        if result:
            session.expunge(result)
        return result


def find_fb_group_by_owner_id_and_name(owner_id, name) -> FunctionBlockGroup:
    with SessionLocal() as session:
        # Use a single JOIN query to avoid the deadlock risk of two separate queries
        result = session.query(FunctionBlockGroup).join(
            FunctionBlockGroupUserRelation,
            FunctionBlockGroup.id == FunctionBlockGroupUserRelation.function_block_group_id
        ).filter(
            and_(
                FunctionBlockGroupUserRelation.user_id == owner_id,
                FunctionBlockGroupUserRelation.relation == Relation.BELONG_TO.value,
                FunctionBlockGroup.name == name
            )
        ).first()
        
        if result:
            session.expunge(result)
        return result


def find_edges_by_analysis_id(analysis_id) -> List[Edge]:
    with SessionLocal() as session:
        results = session.query(Edge).filter(Edge.analysis_id == analysis_id).all()
        for result in results:
            session.expunge(result)
        return results


def find_nodes_by_analysis_id(analysis_id) -> List[Node]:
    with SessionLocal() as session:
        results = session.query(Node).filter(Node.analysis_id == analysis_id).all()
        for result in results:
            session.expunge(result)
        return results


def find_nodes_by_id_list(node_id_list) -> List[Node]:
    if not node_id_list:
        return []
    with SessionLocal() as session:
        results = session.query(Node).filter(Node.id.in_(node_id_list)).all()
        for result in results:
            session.expunge(result)
        return results


def find_computations_by_node_id_list(node_id_list) -> List[Computation]:
    if not node_id_list:
        return []
    with SessionLocal() as session:
        results = session.query(Computation).filter(Computation.node_id.in_(node_id_list)).all()
        for result in results:
            session.expunge(result)
        return results


def find_figures_by_computation_id_list(computation_id_list) -> List[Figure]:
    if not computation_id_list:
        return []
    with SessionLocal() as session:
        results = session.query(Figure).filter(Figure.computation_id.in_(computation_id_list)).all()
        for result in results:
            session.expunge(result)
        return results


def find_datas_by_id_list(data_id_list) -> List[Data]:
    if not data_id_list:
        return []
    with SessionLocal() as session:
        results = session.query(Data).filter(Data.id.in_(data_id_list)).all()
        for result in results:
            session.expunge(result)
        return results


def find_task_owner_relation_by_task_id(task_id) -> TaskUserRelation:
    with SessionLocal() as session:
        result = session.query(TaskUserRelation).filter(
            and_(
                TaskUserRelation.task_id == task_id,
                TaskUserRelation.relation == Relation.BELONG_TO.value
            )
        ).first()
        if result:
            session.expunge(result)
        return result


def insert_fb(fb: FunctionBlockV1) -> FunctionBlockV1:
    with SessionLocal() as session:
        try:
            session.add(fb)
            session.commit()
            session.refresh(fb)
            session.expunge(fb)
            return fb
        except Exception as e:
            session.rollback()
            raise e


def insert_fb_user_relation(relation: FunctionBlockUserRelation) -> FunctionBlockUserRelation:
    with SessionLocal() as session:
        try:
            session.add(relation)
            session.commit()
            session.refresh(relation)
            session.expunge(relation)
            return relation
        except Exception as e:
            session.rollback()
            raise e


def insert_fb_version(fb_version: FunctionBlockVersionV1) -> FunctionBlockVersionV1:
    with SessionLocal() as session:
        try:
            session.add(fb_version)
            session.commit()
            session.refresh(fb_version)
            session.expunge(fb_version)
            return fb_version
        except Exception as e:
            session.rollback()
            raise e


def find_previous_node_by_node_id(node_id) -> Node:
    with SessionLocal() as session:
        edge = session.query(Edge).filter(
            Edge.target_node_id == node_id).first()
        if not edge:
            return None
        result = session.query(Node).filter(Node.id == edge.source_node_id).first()
        if result:
            session.expunge(result)
        return result


def find_dynamic_generation_by_id(id) -> DynamicGeneration:
    with SessionLocal() as session:
        result = session.query(DynamicGeneration).filter(
            DynamicGeneration.generation_id == id).first()
        if result:
            session.expunge(result)
        return result


def insert_edge(edge: Edge) -> Edge:
    with SessionLocal() as session:
        try:
            session.add(edge)
            session.commit()
            session.refresh(edge)
            session.expunge(edge)
            return edge
        except Exception as e:
            session.rollback()
            raise e


def insert_task_node_relation(relation: TaskNodeRelation) -> TaskNodeRelation:
    with SessionLocal() as session:
        try:
            session.add(relation)
            session.commit()
            session.refresh(relation)
            session.expunge(relation)
            return relation
        except Exception as e:
            session.rollback()
            raise e


def insert_task_edge_relation(relation: TaskEdgeRelation) -> TaskEdgeRelation:
    with SessionLocal() as session:
        try:
            session.add(relation)
            session.commit()
            session.refresh(relation)
            session.expunge(relation)
            return relation
        except Exception as e:
            session.rollback()
            raise e


@retry_on_deadlock(max_retries=3)
def update_fb_version(fb_version_id, attrs) -> None:
    with SessionLocal() as session:
        try:
            session.query(FunctionBlockVersionV1).filter(
                FunctionBlockVersionV1.id == fb_version_id).update(attrs, synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


@retry_on_deadlock(max_retries=3)
def update_fb(fb_id, attrs) -> None:
    with SessionLocal() as session:
        try:
            session.query(FunctionBlockV1).filter(
                FunctionBlockV1.id == fb_id).update(attrs, synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


@retry_on_deadlock(max_retries=3)
def lock_nodes_in_dynamic_generation(node_ids) -> None:
    if not node_ids:
        return
    with SessionLocal() as session:
        try:
            # Sort the ID list so that concurrent transactions lock rows in the same order
            sorted_node_ids = sorted(node_ids)
            session.query(Node).filter(Node.id.in_(sorted_node_ids)).update(
                {"dynamic_generation_locked": True}, synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


@retry_on_deadlock(max_retries=3)
def unlock_nodes_in_dynamic_generation(node_ids) -> None:
    if not node_ids:
        return
    with SessionLocal() as session:
        try:
            # Sort the ID list so that concurrent transactions lock rows in the same order
            sorted_node_ids = sorted(node_ids)
            session.query(Node).filter(Node.id.in_(sorted_node_ids)).update(
                {"dynamic_generation_locked": False}, synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


@retry_on_deadlock(max_retries=3)
def update_dynamic_generation(generation_id, attrs) -> None:
    with SessionLocal() as session:
        try:
            session.query(DynamicGeneration).filter(
                DynamicGeneration.generation_id == generation_id).update(attrs, synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def insert_dynamic_generation_branch(branch: DynamicGenerationBranch) -> DynamicGenerationBranch:
    with SessionLocal() as session:
        try:
            session.add(branch)
            session.commit()
            session.refresh(branch)
            session.expunge(branch)
            return branch
        except Exception as e:
            session.rollback()
            raise e


@retry_on_deadlock(max_retries=3)
def update_dynamic_generation_branch(branch_id, attrs: dict) -> None:
    with SessionLocal() as session:
        try:
            session.query(DynamicGenerationBranch).filter(
                DynamicGenerationBranch.id == branch_id).update(attrs, synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def find_dynamic_generation_branch_by_dynamic_generation_id_and_end_node_id(dynamic_generation_id, end_node_id) -> DynamicGenerationBranch:
    with SessionLocal() as session:
        result = session.query(DynamicGenerationBranch).filter(
            and_(
                DynamicGenerationBranch.dynamic_generation_id == dynamic_generation_id,
                DynamicGenerationBranch.end_node_id == end_node_id
            )
        ).first()
        if result:
            session.expunge(result)
        return result


def find_dynamic_generation_branch_by_dynamic_generation_id(dynamic_generation_id) -> List[DynamicGenerationBranch]:
    with SessionLocal() as session:
        results = session.query(DynamicGenerationBranch).filter(
            DynamicGenerationBranch.dynamic_generation_id == dynamic_generation_id
        ).all()
        for result in results:
            session.expunge(result)
        return results


def find_visualizer_by_id(id: int):
    with SessionLocal() as session:
        result = session.query(Visualizer).filter(
            Visualizer.id == id).first()
        if result:
            session.expunge(result)
        return result


def insert_session(session: DynamicGenerationSession) -> DynamicGenerationSession:
    with SessionLocal() as db_session:
        try:
            db_session.add(session)
            db_session.commit()
            db_session.refresh(session)
            db_session.expunge(session)
            return session
        except Exception as e:
            db_session.rollback()
            raise e
    
def insert_consumption(llm_consumption: LLMConsumption) -> LLMConsumption:
    with SessionLocal() as session:
        try:
            session.add(llm_consumption)
            session.commit()
            session.refresh(llm_consumption)
            session.expunge(llm_consumption)
            return llm_consumption
        except Exception as e:
            session.rollback()
            raise e

def insert_computation_file_size(computation_file_size: ComputationFileSize) -> ComputationFileSize:
    with SessionLocal() as session:
        try:
            session.add(computation_file_size)
            session.commit()
            session.refresh(computation_file_size)
            session.expunge(computation_file_size)
            return computation_file_size
        except Exception as e:
            session.rollback()
            raise e

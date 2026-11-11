from datetime import datetime
import json
import os
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, BigInteger, Double, Text, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from constants import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    Relation
)

# Database connection configuration

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
    connect_args={
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

# Define the data models


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
    annotated = Column(Boolean)
    avg_duration = Column(Double)
    visualizer_id = Column(BigInteger)
    visualizer_previous_node_id = Column(BigInteger)
    visualizer_locked = Column(Boolean)
    is_review_error = Column(Boolean, default=False)

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
            "isReviewError": self.is_review_error
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
    llm_model = Column(String(255))

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
        visualizer_attrs_dict["llmModel"] = self.llm_model
        return visualizer_attrs_dict


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
    average_time = Column(Double, comment='Average run time')
    alt_name = Column(String(255), nullable=True)
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
            "altName": self.alt_name,
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
            "isReviewError": self.is_review_error
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
            "summary": self.summary
        }


def find_visualizer_by_id(id: int):
    session = SessionLocal()
    try:
        visualizer = session.query(Visualizer).filter(
            Visualizer.id == id).first()
        return visualizer
    finally:
        session.close()


def find_node_by_id(id: int):
    session = SessionLocal()
    try:
        node = session.query(Node).filter(Node.id == id).first()
        return node
    finally:
        session.close()


def update_visualizer(visualizer_id: int, attrs: dict):
    session = SessionLocal()
    try:
        session.query(Visualizer).filter(
            Visualizer.id == visualizer_id).update(attrs)
        session.flush()
        session.commit()
    finally:
        session.close()


def insert_fb(fb: FunctionBlockV1) -> FunctionBlockV1:
    with SessionLocal() as session:
        session.add(fb)

        session.commit()
        return fb


def insert_fb_user_relation(relation: FunctionBlockUserRelation) -> FunctionBlockUserRelation:
    with SessionLocal() as session:
        session.add(relation)

        session.commit()
        return relation


def insert_fb_version(fb_version: FunctionBlockVersionV1) -> FunctionBlockVersionV1:
    with SessionLocal() as session:
        session.add(fb_version)

        session.commit()
        return fb_version


def insert_fb_group_user_relation(relation: FunctionBlockGroupUserRelation) -> None:
    with SessionLocal() as session:
        session.add(relation)

        session.commit()


def insert_fb_group(fb_group: FunctionBlockGroup) -> None:
    with SessionLocal() as session:
        session.add(fb_group)

        session.commit()


def find_fb_v_by_id(fb_v_id: int) -> FunctionBlockVersionV1:
    with SessionLocal() as session:
        return session.query(FunctionBlockVersionV1).filter(
            FunctionBlockVersionV1.id == fb_v_id
        ).first()


def find_fb_group_by_owner_id_and_name(owner_id, name) -> FunctionBlockGroup:
    with SessionLocal() as session:
        user_relations = session.query(FunctionBlockGroupUserRelation).filter(
            and_(
                FunctionBlockGroupUserRelation.user_id == owner_id,
                FunctionBlockGroupUserRelation.relation == Relation.BELONG_TO.value
            )
        ).all()
        fb_group_id_list = [
            user_relation.function_block_group_id for user_relation in user_relations]
        if len(fb_group_id_list) == 0:
            return None
        return session.query(FunctionBlockGroup).filter(
            and_(
                FunctionBlockGroup.id.in_(fb_group_id_list),
                FunctionBlockGroup.name == name
            )
        ).first()


def update_fb_version(fb_version_id, attrs) -> None:
    with SessionLocal() as session:
        session.query(FunctionBlockVersionV1).filter(
            FunctionBlockVersionV1.id == fb_version_id).update(attrs)
        session.commit()


def update_fb(fb_id, attrs) -> None:
    with SessionLocal() as session:
        session.query(FunctionBlockV1).filter(
            FunctionBlockV1.id == fb_id).update(attrs)
        session.commit()


def find_latest_computation_by_node_id(node_id) -> Computation:
    with SessionLocal() as session:
        return session.query(Computation).filter(
            Computation.node_id == node_id
        ).order_by(
            Computation.created_time.desc()
        ).first()


def find_data_by_id(data_id) -> Data:
    with SessionLocal() as session:
        return session.query(Data).filter(
            Data.id == data_id
        ).first()

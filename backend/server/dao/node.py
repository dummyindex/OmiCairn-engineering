from model.node import Node
from model.edge import Edge
from model.node_user_relation import NodeUserRelation
from model.computation import Computation
from model.function_block_v1 import FunctionBlockV1
from model.function_block_version_v1 import FunctionBlockVersionV1
from model.data_vitessce import DataVitessce
from db import alchemy_db
from sqlalchemy import and_
from sqlalchemy import text
from typing import List
import json
from model.node import Node
from model.task import Task
from log.logger_factory import logger_factory

logger = logger_factory.create_logger(__name__)

class NodeDao:
    def insert(self, node: Node):
        alchemy_db.session.add(node)
        alchemy_db.session.flush()
        return node

    def insert_user_relation(self, user_relation: NodeUserRelation):
        alchemy_db.session.add(user_relation)
        alchemy_db.session.flush()
        return user_relation

    def insert_list(self, node_list: List[Node]):
        alchemy_db.session.bulk_save_objects(node_list)
        alchemy_db.session.flush()
        return node_list

    def delete(self, node_id):
        Node.query.filter(Node.id == node_id).delete()
        NodeUserRelation.query.filter(NodeUserRelation.node_id == node_id).delete()

    def find_by_id(self, node_id) -> Node:
        return Node.query.filter(Node.id == node_id).first()

    def find_raw_by_analysis_id(self, analysis_id) -> List[Node]:
        return Node.query.filter(Node.analysis_id == analysis_id).all()

    def find_by_analysis_id(self, analysis_id) -> List[Node]:
        return alchemy_db.session.query(
            Node.id,
            Node.analysis_id,
            Node.name,
            Node.type,
            Node.x,
            Node.y,
            Node.tag,
            Node.data_id,
            Node.function_block_id,
            Node.function_block_version_id,
            Node.state,
            Node.created_time,
            Node.locked,
            Node.retry_process_id,
            Node.retry_process_locked,
            Node.dynamic_generation_id,
            Node.dynamic_generation_locked,
            Node.computation_resource_configure,
            Node.annotated,
            Node.system_env,
            Node.avg_duration,
            Node.visualizer_id,
            Node.visualizer_locked,
            Node.visualizer_previous_node_id,
            Node.report_uuid,
            Node.report_model,
            Node.is_review_error,
            FunctionBlockV1.name.label('function_block_name'),
            FunctionBlockV1.type.label('function_block_type'),
            FunctionBlockV1.created_time.label('function_block_created_time'),
            FunctionBlockV1.current_version_id.label('function_block_current_version_id'),
            FunctionBlockV1.group_id.label('function_block_group_id'),
            FunctionBlockVersionV1.state.label('function_block_version_state'),
            FunctionBlockVersionV1.plot_only.label('function_block_version_plot_only'),
            FunctionBlockVersionV1.program_language.label('function_block_version_program_language')
        ).join(
            FunctionBlockV1, Node.function_block_id == FunctionBlockV1.id, isouter = True
        ).join(
            FunctionBlockVersionV1, Node.function_block_version_id == FunctionBlockVersionV1.id, isouter = True
        ).filter(
            Node.analysis_id == analysis_id
        ).all()

    def find_by_analysis_id_with_computation(self, analysis_id):
        return alchemy_db.session.query(
            Node.id.label('node_id'),
            Node.analysis_id.label('analysis_id'),
            Node.name.label('node_name'),
            Node.type.label('node_type'),
            Node.state.label('node_state'),
            Node.locked.label('node_locked'),
            Node.retry_process_id.label('node_retry_process_id'),
            Node.retry_process_locked.label('node_retry_process_locked'),
            Node.dynamic_generation_id.label('node_dynamic_generation_id'),
            Node.dynamic_generation_locked.label('node_dynamic_generation_locked'),
            Node.computation_resource_configure.label('node_computation_resource_configure'),
            Node.annotated.label('node_annotated'),
            Node.system_env.label('node_system_env'),
            Node.created_time.label('node_created_time'),
            Node.function_block_id.label('function_block_id'),
            Node.function_block_version_id.label('function_block_version_id'),
            Node.visualizer_id.label('visualizer_id'),
            Node.visualizer_locked.label('visualizer_locked'),
            Node.visualizer_previous_node_id.label('visualizer_previous_node_id'),
            Computation.id.label('computation_id'),
            Computation.computation_params.label('computation_params'),
            Computation.duration.label('computation_duration'),
            Computation.is_review_error.label('computation_is_review_error')
        ).join(
            Computation, Node.id == Computation.node_id, isouter = True
        ).filter(
            Node.analysis_id == analysis_id
        ).all()

    def find_page(self, offset, limit) -> List[Node]:
        return Node.query.offset(offset).limit(limit).all()

    def find_by_id_list(self, node_id_list) -> List[Node]:
        return Node.query.filter(Node.id.in_(node_id_list)).all()
    
    def find_branch_path(self, node_id) -> List[Node]:
        path: List[Node] = []
        next_edge_path: List[Edge] = Edge.query.filter(Edge.target_node_id == node_id).all()
        for edge in next_edge_path:
            path.append(self.find_by_id(edge.source_node_id))
        index = 0
        while index < len(next_edge_path):
            next_edge = next_edge_path[index]
            edges = Edge.query.filter(
                Edge.target_node_id == next_edge.source_node_id
            ).all()
            next_edge_path += edges
            for edge in edges:
                path.append(self.find_by_id(edge.source_node_id))
            index += 1
        path.reverse()
        next_edge_path.reverse()
        return path, next_edge_path

    def find_previte_list_by_analysis_id(self, analysis_id):
        node_list = Node.query.filter(Node.analysis_id == analysis_id).all()
        node_id_list = [node.id for node in node_list]
        if len(node_id_list) == 0:
            return []
        node_id_list_str = ','.join([str(node_id) for node_id in node_id_list])
        sql = f"""
            WITH ranked_comp AS (
                SELECT *,
                    ROW_NUMBER() OVER(PARTITION BY node_id ORDER BY created_time DESC) AS rn
                FROM computation
            )
            SELECT ranked_comp.node_id, data_vitessce.status
            FROM ranked_comp INNER JOIN data_vitessce ON ranked_comp.result_data_id = data_vitessce.data_id
            WHERE ranked_comp.rn = 1 and ranked_comp.node_id in ({node_id_list_str});
        """
        result = alchemy_db.session.execute(text(sql))
        return result.fetchall()

    def find_by_data_id(self, data_id) -> List[Node]:
        return Node.query.filter(Node.data_id == data_id).all()

    def find_user_relation_by_node_id_and_user_ids(self, node_id, user_ids) -> List[NodeUserRelation]:
        return NodeUserRelation.query.filter(
            and_(
                NodeUserRelation.node_id == node_id,
                NodeUserRelation.user_id.in_(user_ids)
            )
        ).all()

    def update(self, node_id, attrs: dict):
        Node.query.filter(Node.id == node_id).update(attrs)
        alchemy_db.session.flush()

    def update_node(self, node_id, data) -> Node:
        Node.query.filter(Node.id == node_id).update(data)
        alchemy_db.session.flush()
        return Node.query.filter(Node.id == node_id).first()

    def update_by_id_list(self, node_id_list, attrs: dict):
        Node.query.filter(Node.id.in_(node_id_list)).update(attrs)
        alchemy_db.session.flush()

    def delete_by_analysis_id(self, analysis_id):
        node_list = Node.query.filter(Node.analysis_id == analysis_id).all()
        node_id_list = [node.id for node in node_list]
        NodeUserRelation.query.filter(
            NodeUserRelation.node_id.in_(node_id_list)
        ).delete()
        Node.query.filter(Node.analysis_id == analysis_id).delete()

    def delete_user_relation_by_node_id_and_user_id(self, node_id, user_id):
        effect_row_count = NodeUserRelation.query.filter(
            and_(
                NodeUserRelation.node_id == node_id,
                NodeUserRelation.user_id == user_id
            )
        ).delete()
        return effect_row_count

    def find_by_analysis_id_and_fb_id_and_user_id(self, analysis_id, fb_id, user_id) -> List[Node]:
        return Node.query.join(
            NodeUserRelation, Node.id == NodeUserRelation.node_id
        ).filter(
            Node.analysis_id == analysis_id,
            Node.function_block_id == fb_id,
            NodeUserRelation.user_id == user_id
        ).all()

    def update_and_get_matching_average_duration(self, function_block_version_id=None, system_env=None, computation_resource_configure=None):
        if function_block_version_id is None or system_env is None or computation_resource_configure is None:
            return None

        if isinstance(computation_resource_configure, str):
            computation_resource_configure_json = computation_resource_configure
        else:
            computation_resource_configure_json = json.dumps(computation_resource_configure)

        sql = """
        SELECT avg_duration
        FROM function_block_average_duration
        WHERE function_block_version_id = :fb_version_id
        AND system_env = :sys_env
        AND (
            CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(computation_resource_configure, '$.gpu'), '0')) AS UNSIGNED) =
            CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(:comp_resource, '$.gpu'), '0')) AS UNSIGNED)
        )
        AND (
            CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(computation_resource_configure, '$.ram'), '0')) AS UNSIGNED) =
            CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(:comp_resource, '$.ram'), '0')) AS UNSIGNED)
        )
        AND (
            CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(computation_resource_configure, '$.vcpu'), '0')) AS UNSIGNED) =
            CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(:comp_resource, '$.vcpu'), '0')) AS UNSIGNED)
        )
        AND (
            CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(computation_resource_configure, '$.timeout'), '0')) AS UNSIGNED) =
            CAST(JSON_UNQUOTE(COALESCE(JSON_EXTRACT(:comp_resource, '$.timeout'), '0')) AS UNSIGNED)
        )
        LIMIT 1
        """

        result = alchemy_db.session.execute(
            text(sql),
            {
                'fb_version_id': function_block_version_id,
                'sys_env': system_env,
                'comp_resource': computation_resource_configure_json
            }
        )

        row = result.fetchone()
        if row is not None:
            return row[0]

        return None

    def get_information(self, node_id):
        return Node.query.filter(Node.id == node_id).first()

node_dao = NodeDao()

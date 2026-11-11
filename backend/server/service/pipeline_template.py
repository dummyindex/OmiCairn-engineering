from datetime import datetime
from typing import List
from dao.pipeline_template import (
    pipeline_template_dao as pt_dao
)
from dao.pipeline_template_edge import (
    pipeline_template_edge_dao as pt_edge_dao
)
from dao.pipeline_template_node import (
    pipeline_template_node_dao as pt_node_dao
)
from dao.function_block_v1 import (
    function_block_v1_dao as fb_v1_dao
)
from dao.node import node_dao
from dao.edge import edge_dao
from model.pipeline_template import PipelineTemplate
from model.node import Node
from model.edge import Edge
from model.pipeline_template_edge import PipelineTemplateEdge
from model.pipeline_template_node import PipelineTemplateNode
from dto.pipeline_template_detail import (
    PipelineTemplateDetailDto
)
from constants.pipeline_template import (
    CREATE_NODE_OFFSET_X,
    CREATE_NODE_OFFSET_Y
)
from dto.pipeline_template_import_result import PipelineTemplateImportResult
from constants.node import NodeState, NodeType
from constants.authority import Relation, Permission, SpecialUserId
from model.node_user_relation import NodeUserRelation
from model.pipeline_template_user_relation import PipelineTemplateUserRelation
from constants.computation import SystemEnv

class PipelineTemplateService:

    def create(
        self,
        name,
        node_id_list,
        edge_id_list,
        owner_id,
        group_name,
        description
    ) -> PipelineTemplateDetailDto:
        """Create a pipeline template.
        Steps:
            1. Create a pipeline template.
            2. Create pipeline template nodes.
            3. Use a dict to map node id to pipeline template node id.
            4. Use session.flush() to get the pipeline template node id.
            5. Use the dict to create pipeline template edges and map node id to pipeline template node id.

        Returns:
            _type_: PipelineTemplate
        """
        now = datetime.now()
        node_list = node_dao.find_by_id_list(node_id_list)
        edge_list = edge_dao.find_by_id_list(edge_id_list)

        min_x = min([node.x for node in node_list])
        min_y = min([node.y for node in node_list])

        pipeline_template = PipelineTemplate(
            created_time=now,
            name=name,
            group_name=group_name,
            description=description
        )
        pt_dao.insert(pipeline_template)
        pt_user_relation = PipelineTemplateUserRelation(
            pipeline_template_id=pipeline_template.id,
            user_id=owner_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        pt_dao.insert_user_relation(pt_user_relation)
        pt_id = pipeline_template.id
        pt_node_dict: dict = {
            node.id: PipelineTemplateNode(
                pipeline_template_id=pt_id,
                computation_params=node.computation_params,
                created_time=datetime.now(),
                function_block_id=node.function_block_id,
                function_block_version_id=node.function_block_version_id,
                name=node.name,
                relative_x=node.x - min_x,
                relative_y=node.y - min_y,
                computation_resource_configure=node.computation_resource_configure
            )
            for node in node_list
        }

        pt_node_list = list(pt_node_dict.values())
        pt_node_dao.insert_list(pt_node_list)

        pt_edge_list: List[PipelineTemplateEdge] = [
            PipelineTemplateEdge(
                pipeline_template_id=pt_id,
                created_time=datetime.now(),
                source_pt_node_id=pt_node_dict[edge.source_node_id].id,
                target_pt_node_id=pt_node_dict[edge.target_node_id].id
            )
            for edge in edge_list
        ]
        pt_edge_dao.insert_list(pt_edge_list)
        return PipelineTemplateDetailDto(
            pt=pipeline_template,
            pt_node_list=pt_node_list,
            pt_edge_list=pt_edge_list,
            group_name=group_name
        )

    def get_list_by_owner_id_and_group_name(self, user_id, group_name):
        return pt_dao.find_by_user_id_and_group_name(
            user_id=user_id,
            group_name=group_name
        )

    def get_detail(self, pt_id) -> PipelineTemplateDetailDto:
        pipeline_template = pt_dao.find_by_id(pt_id)
        pt_node_list = pt_node_dao.find_by_pt_id(pt_id)
        pt_edge_list = pt_edge_dao.find_by_pt_id(pt_id)
        return PipelineTemplateDetailDto(
            pt=pipeline_template,
            pt_node_list=pt_node_list,
            pt_edge_list=pt_edge_list
        )

    def get_group_name_list_by_user_id(self, user_id):
        return pt_dao.find_group_name_list(user_id)

    def get_function_block_list_by_pipeline_template_id(self, pt_id):
        pt_node_list: List[PipelineTemplateNode] = pt_node_dao.find_by_pt_id(pt_id)
        pt_edge_list: List[PipelineTemplateEdge] = pt_edge_dao.find_by_pt_id(pt_id)

        pt_node_id_2_pt_node_dict = { pt_node.id: pt_node for pt_node in pt_node_list }

        # sort pt_node_list by tree structure
        source_2_target_node_dict = { pt_node.id: [] for pt_node in pt_node_list }
        target_2_source_node_dict = { pt_node.id: [] for pt_node in pt_node_list }
        for pt_edge in pt_edge_list:
            source_2_target_node_dict[pt_edge.source_pt_node_id].append(pt_edge.target_pt_node_id)
            target_2_source_node_dict[pt_edge.target_pt_node_id].append(pt_edge.source_pt_node_id)
        pt_node_queue = [ pt_node_id_2_pt_node_dict[pt_node_id] for pt_node_id in target_2_source_node_dict.keys() if len(target_2_source_node_dict[pt_node_id]) == 0 ]
        sorted_function_block_list = []
        included_fb_id_set = set()
        while len(pt_node_queue) > 0:
            pt_node = pt_node_queue[0]
            pt_node_queue = pt_node_queue[1:]
            if pt_node.function_block_id not in included_fb_id_set:
                function_block = fb_v1_dao.find_by_id(pt_node.function_block_id)
                sorted_function_block_list.append(function_block)
                included_fb_id_set.add(pt_node.function_block_id)
            target_pt_node_id_list = source_2_target_node_dict[pt_node.id]
            for target_pt_node_id in target_pt_node_id_list:
                pt_node_queue.append(pt_node_id_2_pt_node_dict[target_pt_node_id])

        return sorted_function_block_list


    def edit_group_name_by_user_id_and_old_name(self, user_id, old_name, new_name):
        pt_dao.update_group_name_by_user_id_and_old_name(
            user_id=user_id,
            old_name=old_name,
            new_name=new_name
        )

    def edit_metadata(self, pt_id, name = None, group_name = None):
        if not name and not group_name:
            return
        updated_attrs = {}
        if name is not None:
            updated_attrs['name'] = name
        if group_name is not None:
            updated_attrs['group_name'] = group_name
        pt_dao.update(pt_id, updated_attrs)

    def remove_group_by_user_id_and_group_name(self, user_id, group_name):
        pt_list = pt_dao.find_by_user_id_and_group_name(
            user_id=user_id,
            group_name=group_name
        )
        pt_id_list = [pt.id for pt in pt_list]
        # delete pipeline template nodes
        pt_node_dao.delete_by_pt_id_list(pt_id_list)
        # delete pipeline template edges
        pt_edge_dao.delete_by_pt_id_list(pt_id_list)
        # delete pipeline template
        pt_dao.delete_by_user_id_and_group_name(
            user_id=user_id,
            group_name=group_name
        )

    def remove(self, pt_id):
        pt_node_dao.delete_by_pt_id(pt_id)
        pt_edge_dao.delete_by_pt_id(pt_id)
        pt_dao.delete(pt_id)

    def import_into_analysis(
        self,
        pipeline_template_id,
        analysis_id,
        owner_id
    ) -> PipelineTemplateImportResult:
        pt_node_list = pt_node_dao.find_by_pt_id(pipeline_template_id)
        pt_edge_list = pt_edge_dao.find_by_pt_id(pipeline_template_id)
        new_node_list = []
        new_edge_list = []
        pt_node_id_2_analysis_node_id_dict = {}
        for pt_node in pt_node_list:
            fb_version = fb_v1_dao.find_version_by_id(pt_node.function_block_version_id)
            node = Node(
                created_time=datetime.now(),
                name=pt_node.name,
                function_block_id=pt_node.function_block_id,
                function_block_version_id=pt_node.function_block_version_id,
                computation_params=pt_node.computation_params,
                analysis_id=analysis_id,
                x=pt_node.relative_x + CREATE_NODE_OFFSET_X,
                y=pt_node.relative_y + CREATE_NODE_OFFSET_Y,
                type=NodeType.COMPUTATION_NODE.value,
                data_id=None,
                locked=False,
                state=NodeState.ORIGINAL.value,
                tag=fb_version.tag,
                system_env=SystemEnv.AWS_BATCH.value,
                computation_resource_configure=pt_node.computation_resource_configure
            )
            node_dao.insert(node)
            node_user_relation = NodeUserRelation(
                node_id=node.id,
                user_id=owner_id,
                relation=Relation.BELONG_TO.value,
                permission=Permission.ADMIN.value
            )
            node_dao.insert_user_relation(node_user_relation)
            pt_node_id_2_analysis_node_id_dict[pt_node.id] = node.id
            new_node_list.append(node)
        for pt_edge in pt_edge_list:
            edge = Edge(
                created_time=datetime.now(),
                source_node_id=pt_node_id_2_analysis_node_id_dict[pt_edge.source_pt_node_id],
                target_node_id=pt_node_id_2_analysis_node_id_dict[pt_edge.target_pt_node_id],
                analysis_id=analysis_id
            )
            edge_dao.insert(edge)
            new_edge_list.append(edge)

        return PipelineTemplateImportResult(
            new_node_list=new_node_list,
            new_edge_list=new_edge_list
        )

    def turn_over_to_public(self, pipeline_template_id):
        pt_dao.update_relation_by_pt_id(pipeline_template_id, {'user_id': SpecialUserId.PUBLIC.value})

pipeline_template_service = PipelineTemplateService()

import hmac
from datetime import datetime
import json
from dao.analysis import analysis_dao
from dao.node import node_dao
from dao.edge import edge_dao
from dao.data import data_dao
from dao.analysis_data_relation import analysis_data_relation_dao
from model.analysis import Analysis
from model.analysis_data_relation import AnalysisDataRelation
from model.analysis_user_relation import AnalysisUserRelation
from model.node import Node
from model.node_user_relation import NodeUserRelation
from constants.node import NodeState, NodeType
from constants.authority import SpecialUserId
from model.edge import Edge
from constants.authority import Permission, Relation
from log.logger_factory import logger_factory
from exception.request.parameter_invalid import ParameterInvalidException
from tool.common_generator import CommonGenerator
from dao.inform import inform_dao
from dao.collaboration_invitation import collaboration_invitation_dao
from dao.open_ap_record import open_ap_record_dao
from constants.inform import InformType
from constants.invitation import InvitationStatus, ObjectType
from model.inform import Inform
from model.collaboration_invitation import CollaborationInvitation
from waiter.node_space_waiter import NodeSpaceWaiter
from dao.computation import ComputationDao
from exception.common.not_operatable import NotOperatableException
from constants.common import LONG_TEXT_MAX_LEN
from tool.db import convert_model_to_dict

logger = logger_factory.create_logger("AnalysisService")

class AnalysisService:

    def get_info_list(self, owner_id, add_latest_visit_time=False):
        analysis_list = analysis_dao.find_by_user_id(owner_id)
        if add_latest_visit_time:
            latest_visit_record_list = open_ap_record_dao.find_ones_latest_record_by_user_id(
                owner_id, [analysis.id for analysis in analysis_list]
            )
            latest_visit_time_dict = {
                record.analysis_id: record.open_time for record in latest_visit_record_list
            }
            new_analysis_list = []
            for analysis in analysis_list:
                latest_visit_time = latest_visit_time_dict.get(analysis.id, analysis.created_time)
                analysis_dict = convert_model_to_dict(analysis, camel_case=True)
                analysis_dict["latestVisitTime"] = latest_visit_time
                new_analysis_list.append(analysis_dict)
            analysis_list = new_analysis_list
        # sort by most recent access time
        return analysis_list

    def get_info(self, id):
        analysis = analysis_dao.find_by_id(id)
        return analysis

    def create(self, user_id, name, description, password, creation_source=None):
        now = datetime.now()
        analysis = Analysis(
            name=name,
            created_time=now,
            disabled=False,
            description=description,
            password=password,
            creation_source=creation_source
        )
        analysis = analysis_dao.insert(analysis)
        analysis_user_relation = AnalysisUserRelation(
            analysis_id=analysis.id,
            user_id=user_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        analysis_dao.insert_user_relation(analysis_user_relation)
        return analysis
    
    def validate_password(self, analysis_id, password):
        analysis = analysis_dao.find_by_id(analysis_id)
        if analysis is None:
            return False
        if not analysis.password:
            return True
        return hmac.compare_digest(str(analysis.password), str(password or ""))

    def import_data(self, analysis_id, data_id):
        now = datetime.now()
        # check if the data is ok
        data = data_dao.find_by_id(data_id)
        if data is None:
            raise ParameterInvalidException("data_id is invalid")
        analysis_data_relation = AnalysisDataRelation(
            analysis_id=analysis_id,
            data_id=data_id,
            created_time=now
        )
        analysis_data_relation_dao.insert(analysis_data_relation)
        return analysis_data_relation

    def import_data_batch(self, analysis_id, data_id_list):
        now = datetime.now()
        analysis_data_relation_list = []
        for data_id in data_id_list:
            # check if the data is ok
            data = data_dao.find_by_id(data_id)
            if data is None:
                raise ParameterInvalidException("data_id is invalid")
            # check if the data is already in the analysis
            relation = analysis_data_relation_dao.find_by_analysis_id_and_data_id(
                analysis_id, data_id
            )
            if relation is None:
                analysis_data_relation = AnalysisDataRelation(
                    analysis_id=analysis_id,
                    data_id=data_id,
                    created_time=now
                )
                analysis_data_relation_list.append(analysis_data_relation)
        analysis_data_relation_dao.insert_list(analysis_data_relation_list)
        return analysis_data_relation_list

    def remove_data_from_imported_list(self, analysis_id, data_id):
        analysis_data_relation_dao.delete_by_analysis_id_and_data_id(
            analysis_id, data_id)

    def copy(self, analysis_id, name, description ,owner_id):
        # copy analysis
        source_analysis = analysis_dao.find_by_id(analysis_id)
        analysis = Analysis(
            name=name if name is not None else source_analysis.name,
            created_time=datetime.now(),
            disabled=False,
            description=description if description is not None else source_analysis.description
        )
        analysis = analysis_dao.insert(analysis)
        # copy analysis_user_relation
        new_analysis_user_relation = AnalysisUserRelation(
            analysis_id=analysis.id,
            user_id=owner_id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )

        analysis_dao.insert_user_relation(new_analysis_user_relation)
        # copy nodes
        source_nodes = node_dao.find_raw_by_analysis_id(analysis_id)
        old_to_new_node_id_map = {}
        for source_node in source_nodes:
            new_node = Node(
                analysis_id=analysis.id,
                name=source_node.name,
                x=source_node.x,
                y=source_node.y,
                type=source_node.type,
                data_id=source_node.data_id,
                created_time=datetime.now(),
                locked=False,
                state=NodeState.ORIGINAL.value,
                function_block_id=source_node.function_block_id,
                function_block_version_id=source_node.function_block_version_id,
                computation_params=source_node.computation_params,
                tag=source_node.tag,
                system_env=source_node.system_env,
                computation_resource_configure=source_node.computation_resource_configure
            )
            node_dao.insert(new_node)
            node_user_relation = NodeUserRelation(
                node_id=new_node.id,
                user_id=owner_id,
                relation=Relation.BELONG_TO.value,
                permission=Permission.ADMIN.value
            )
            node_dao.insert_user_relation(node_user_relation)
            old_to_new_node_id_map[source_node.id] = new_node.id
        # copy edges
        source_edges = edge_dao.find_by_analysis_id(analysis_id)
        for source_edge in source_edges:
            new_edge = Edge(
                analysis_id=analysis.id,
                source_node_id=old_to_new_node_id_map[source_edge.source_node_id],
                target_node_id=old_to_new_node_id_map[source_edge.target_node_id],
                created_time=datetime.now()
            )
            edge_dao.insert(new_edge)
        # copy analysis_data_relation
        source_analysis_data_relations = analysis_data_relation_dao.find_by_analysis_id(
            analysis_id
        )
        for source_analysis_data_relation in source_analysis_data_relations:
            new_analysis_data_relation = AnalysisDataRelation(
                analysis_id=analysis.id,
                data_id=source_analysis_data_relation.data_id,
                created_time=datetime.now()
            )
            analysis_data_relation_dao.insert(new_analysis_data_relation)

        # copy node space
        # travel old_to_new_node_id_map
        for old_node_id, new_node_id in old_to_new_node_id_map.items():
            node_space_waiter = NodeSpaceWaiter(new_node_id)
            node_space_waiter.copy_from_another_node_space(old_node_id)
        return analysis

    def edit(self, id, name, description):
        attrs = {}
        if name is not None:
            attrs['name'] = name
        if description is not None:
            attrs['description'] = description
        analysis = analysis_dao.update(id, attrs)
        return analysis
    
    def edit_analyisis(self, analysis_id, data):
        analysis = analysis_dao.find_by_id(analysis_id)
        if analysis.disabled:
            raise NotOperatableException(f"Analysis {analysis_id} is disabled")
        if 'id' in data:
            del data['id']
        
        analysis_dao.update_analysis(analysis_id, data)

    def delete(self, id):
        analysis_dao.delete_by_id(id)
        node_dao.delete_by_analysis_id(id)
        edge_dao.delete_by_analysis_id(id)
        analysis_data_relation_dao.delete_by_analysis_id(id)

    def toggle_sharing(self, analysis_id):
        user_relation_with_all_role = analysis_dao.find_user_relation_by_analysis_id_and_user_ids(
            analysis_id, [SpecialUserId.ALL.value]
        )
        if user_relation_with_all_role is None:
            user_relation_with_all_role = AnalysisUserRelation(
                analysis_id=analysis_id,
                user_id=SpecialUserId.ALL.value,
                relation=Relation.SHARED_WITH.value,
                permission=Permission.READ.value
            )
            analysis_dao.insert_user_relation(user_relation_with_all_role)
        else:
            analysis_dao.delete_user_relation_by_analysis_id_and_user_id(
                analysis_id, SpecialUserId.ALL.value
            )

    def change_user_permission_by_invitation_id(self, invitation_id, permission):
        collaboration_invitation = collaboration_invitation_dao.find_by_id(invitation_id)
        analysis_id = collaboration_invitation.oid
        user_id = collaboration_invitation.invitee_id
        collaboration_invitation_dao.update(invitation_id, {"permission": permission})
        analysis_dao.update_user_relation(analysis_id, user_id, {"permission": permission})

    def invite_collaborator(self, analysis_id, sender_id, receiver_id_list, permission, message=""):
        analysis = analysis_dao.find_by_id(analysis_id)
        if message is not None and len(message) > LONG_TEXT_MAX_LEN:
            raise ParameterInvalidException("message is too long")
        if analysis is None:
            raise ParameterInvalidException("analysis_id is invalid")
        for receiver_id in receiver_id_list:
            invitation = CollaborationInvitation(
                inviter_id=sender_id,
                invitee_id=receiver_id,
                otype=ObjectType.ANALYSIS.value,
                oid=analysis_id,
                permission=permission,
                created_time=datetime.now(),
                status=InvitationStatus.PENDING.value,
                oname=analysis.name,
                message=message
            )
            collaboration_invitation_dao.insert(invitation)
            payload = json.dumps({
                "analysis_id": analysis_id,
                "invitation_id": invitation.id,
                "invitation_status": InvitationStatus.PENDING.value
            })
            inform = Inform(
                sender_id=sender_id,
                receiver_id=receiver_id,
                created_time=datetime.now(),
                have_read=False,
                type=InformType.ANALYSIS_COLLABORATION_INVITATION.value,
                payload=payload
            )
            inform = inform_dao.insert_inform(inform)
            collaboration_invitation_dao.update(invitation.id, {"inform_id": inform.id})
    
    def cancel_collaboration(self, invitation_id):
        invitation = collaboration_invitation_dao.find_by_id(invitation_id)
        analysis_id = invitation.oid
        if analysis_id is None:
            raise ParameterInvalidException("System error, analysis_id is None in the payload")
        if invitation_id is None:
            raise ParameterInvalidException("System error, invitation_id is None in the payload")
        collaboration_invitation_dao.delete(invitation_id)
        analysis_dao.delete_user_relation_by_analysis_id_and_user_id(
            analysis_id, invitation.invitee_id
        )

    def get_collaboration_list(self, analysis_id, user_id):
        invitation_list = collaboration_invitation_dao.find_by_inviter_id_and_otype_and_oid(
            user_id, ObjectType.ANALYSIS.value, analysis_id
        )
        return invitation_list

    def get_invitation_list(self, user_id, offset, limit):
        invitation_list = collaboration_invitation_dao.find_by_invitee_id_and_otype(
            user_id, ObjectType.ANALYSIS.value, offset, limit
        )
        return invitation_list

    def accept_invitation(self, invitation_id):
        invitation = collaboration_invitation_dao.find_by_id(invitation_id)
        inform_id = invitation.inform_id
        inform = inform_dao.find_inform_by_id(inform_id)
        if inform is not None:
            payload = json.loads(inform.payload)
            payload["invitation_status"] = InvitationStatus.ACCEPTED.value
            inform_dao.update_inform(inform_id, {"payload": json.dumps(payload)})
        analysis_user_relation = AnalysisUserRelation(
            analysis_id=invitation.oid,
            user_id=invitation.invitee_id,
            relation=Relation.SHARED_WITH.value,
            permission=invitation.permission
        )
        analysis_dao.insert_user_relation(analysis_user_relation)
        collaboration_invitation_dao.update(invitation_id, {"status": InvitationStatus.ACCEPTED.value})

    def reject_invitation(self, invitation_id):
        invitation = collaboration_invitation_dao.find_by_id(invitation_id)
        inform_id = invitation.inform_id
        inform = inform_dao.find_inform_by_id(inform_id)
        if inform is not None:
            payload = json.loads(inform.payload)
            payload["invitation_status"] = InvitationStatus.REJECTED.value
            inform_dao.update_inform(inform_id, {"payload": json.dumps(payload)})
        collaboration_invitation_dao.update(invitation_id, {"status": InvitationStatus.REJECTED.value})

    def get_updated_record(self, analysis_id):
        analysis_updated_record = analysis_dao.find_updated_record(analysis_id)
        return analysis_updated_record

    def export_without_data(self, analysis_id):
        analysis = analysis_dao.find_by_id(analysis_id)
        nodes = node_dao.find_raw_by_analysis_id(analysis_id)
        node_entity_list = []
        edge_entity_list = []
        uuid_dict = {}
        for node in nodes:
            if node.type == NodeType.DATA_NODE.value or node.type == NodeType.DATA_NODE_V2.value:
                continue
            uuid_dict[node.id] = CommonGenerator.generate_uuid()
            node_entity = node.to_dict()
            node_entity["id"] = uuid_dict[node.id]
            node_entity["state"] = NodeState.ORIGINAL.value
            node_entity["locked"] = False
            del node_entity["analysisId"]
            node_entity_list.append(node_entity)
        for edge in edge_dao.find_by_analysis_id(analysis_id):
            if edge.source_node_id not in uuid_dict or edge.target_node_id not in uuid_dict:
                continue
            edge_entity = edge.to_dict()
            edge_entity["sourceNodeId"] = uuid_dict[edge.source_node_id]
            edge_entity["targetNodeId"] = uuid_dict[edge.target_node_id]
            del edge_entity["analysisId"]
            edge_entity_list.append(edge_entity)
        return {
            "analysis": analysis.to_dict(),
            "nodes": node_entity_list,
            "edges": edge_entity_list
        }

    def tie_in(self, analysis_structure: dict, user_id):
        analysis = analysis_structure["analysis"]
        nodes = analysis_structure["nodes"]
        edges = analysis_structure["edges"]

        now = datetime.now()
        analysis = Analysis(
            name=analysis["name"],
            created_time=now,
            description=analysis["description"]
        )
        analysis = analysis_dao.insert(analysis)

        analysis_user_relation = AnalysisUserRelation(
            user_id=user_id,
            analysis_id=analysis.id,
            relation=Relation.BELONG_TO.value,
            permission=Permission.ADMIN.value
        )
        analysis_dao.insert_user_relation(analysis_user_relation)

        reversed_uuid_dict = {}
        for node_entity in nodes:
            node = Node()
            for key in node_entity:
                if key in ["id", "createdTime"]:
                    continue
                if key == "computationResourceConfigure":
                    value = json.dumps(node_entity[key]) if node_entity[key] is not None and type(node_entity[key]) == dict else node_entity
                else:
                    value = node_entity[key]
                # convert the camelCase key to snake_case
                key = CommonGenerator.camel_to_snake(key)
                setattr(node, key, value)
            setattr(node, "analysis_id", analysis.id)
            node.analysis_id = analysis.id
            node.created_time = now
            node = node_dao.insert(node)
            reversed_uuid_dict[node_entity["id"]] = node.id
            node_user_relation = NodeUserRelation(
                node_id=node.id,
                user_id=user_id,
                relation=Relation.BELONG_TO.value,
                permission=Permission.ADMIN.value
            )
            node_dao.insert_user_relation(node_user_relation)

        for edge_entity in edges:
            edge = Edge()
            for key in edge_entity:
                if key in ["id", "createdTime"]:
                    continue
                # convert the camelCase key to snake_case
                value = edge_entity[key]
                key = CommonGenerator.camel_to_snake(key)
                setattr(edge, key, value)
            setattr(edge, "analysis_id", analysis.id)
            edge.analysis_id = analysis.id
            edge.source_node_id = reversed_uuid_dict[edge_entity["sourceNodeId"]]
            edge.target_node_id = reversed_uuid_dict[edge_entity["targetNodeId"]]
            edge.created_time = now
            edge_dao.insert(edge)
    
    def calculate_total_duration(analysis_id):
        node_ids = [node.id for node in node_dao.find_by_analysis_id(analysis_id)]
        total_duration = 0
        for node_id in node_ids:
            computations = ComputationDao.find_by_node_id(node_id)
            total_duration += sum(comp.duration for comp in computations if comp.duration)
        return total_duration

analysis_service = AnalysisService()

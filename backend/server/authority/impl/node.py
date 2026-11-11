from authority.guardian import AuthorityGrardian
from exception.authority.no_authority import NoAuthorityException
from constants.authority import Permission,SpecialUserId, PermissionLevelDict
from constants.analysis import SpecialAnalysis
from model.node_user_relation import NodeUserRelation
from model.node import Node
from dao.node import node_dao
from dao.analysis import analysis_dao
from typing import List
from constants.authority import AuthorityCarrier
from log.logger_factory import logger_factory
logger = logger_factory.create_logger("NodeAuthorityGuardian")

class NodeGuardian(AuthorityGrardian):

    def __init__(self, analysis_guardian: AuthorityGrardian):
        super().__init__()
        self.analysis_guardian = analysis_guardian

    def get_user_relations(self, node: Node) -> List[NodeUserRelation]:
        pass

    def check_authority(self, node_id, check_writable=False):
        node = node_dao.find_by_id(node_id)
        if node is None:
            raise Exception("invalid node id")
        if node.analysis_id == SpecialAnalysis.MINI_TOOL.value:
            # mini tool node is public currently
            return
        return self.analysis_guardian.check_authority(
            node.analysis_id, check_writable=check_writable
        )
    
    def check_ownership(self, node_id):
        node = node_dao.find_by_id(node_id)
        if node is None:
            raise Exception("invalid node id")
        if node.analysis_id == SpecialAnalysis.MINI_TOOL.value:
            # mini tool node is public currently
            return
        return self.analysis_guardian.check_ownership(
            node.analysis_id 
        )

    def share_to_all(self, object_id):
        user_relation_for_all = NodeUserRelation(
            node_id=object_id,
            user_id=SpecialUserId.ALL.value,
            permission=Permission.READ.value
        )
        node_dao.insert_user_relation(user_relation_for_all)

    def cancel_share_to_all(self, object_id):
        node_dao.delete_user_relation_by_node_id_and_user_id(
            object_id, SpecialUserId.ALL.value
        )

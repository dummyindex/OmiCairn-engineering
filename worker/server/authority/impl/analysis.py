from authority.guardian import AuthorityGrardian
from exception.authority.no_authority import NoAuthorityException
from constants.authority import Permission, SpecialUserId, PermissionLevelDict
from model.analysis_user_relation import AnalysisUserRelation
from dao.analysis import analysis_dao
from typing import List
from log.logger_factory import LoggerFactory
logger = LoggerFactory.get_logger("AnalysisAuthorityGuardian")


class AnalysisGuardian(AuthorityGrardian):

    def get_user_relations_by_user_ids(self, analysis_id, user_ids) -> List[AnalysisUserRelation]:
        user_relation_list = analysis_dao.find_user_relation_by_analysis_id_and_user_ids(
            analysis_id, user_ids
        )
        return user_relation_list

    def get_user_relations(self, analysis_id) -> List[AnalysisUserRelation]:
        return self.get_user_relations_by_user_ids(
            analysis_id, [self.user_id, SpecialUserId.ALL.value,
                          SpecialUserId.PUBLIC.value]
        )

    def is_public(self, analysis_id):
        user_relation_list = self.get_user_relations_by_user_ids(
            analysis_id, [SpecialUserId.PUBLIC.value])
        return len(user_relation_list) > 0

    def check_authority(self, analysis_id, check_writable=False):
        is_for_public = self.is_public(analysis_id)
        if is_for_public:
            if check_writable and self.user_id != SpecialUserId.PUBLIC.value:
                raise NoAuthorityException(
                    "no authority for editing this analysis")
            else:
                return
        user_relation_list = self.get_user_relations_by_user_ids(
            analysis_id, [self.user_id, SpecialUserId.ALL.value])
        if len(user_relation_list) == 0:
            raise NoAuthorityException("no authority for this analysis")
        if check_writable:
            for user_relation in user_relation_list:
                if PermissionLevelDict[user_relation.permission] >= PermissionLevelDict[Permission.WRITE.value]:
                    return
            raise NoAuthorityException(
                "no authority for changing this analysis")
        return user_relation_list

    def share_to_all(self, object_id):
        user_relation_for_all = AnalysisUserRelation(
            analysis_id=object_id,
            user_id=SpecialUserId.ALL.value,
            permission=Permission.READ.value
        )
        analysis_dao.insert_user_relation(user_relation_for_all)

    def cancel_share_to_all(self, object_id):
        analysis_dao.delete_user_relation_by_analysis_id_and_user_id(
            object_id, SpecialUserId.ALL.value
        )

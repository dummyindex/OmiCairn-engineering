from authority.guardian import AuthorityGrardian
from exception.authority.no_authority import NoAuthorityException
from constants.authority import Permission, SpecialUserId, PermissionLevelDict
from model.task_user_relation import TaskUserRelation
from dao.analysis import analysis_dao
from dao.task import task_dao
from typing import List
from log.logger_factory import LoggerFactory
logger = LoggerFactory.get_logger("TaskAuthorityGuardian")


class TaskGuardian(AuthorityGrardian):

    def get_user_relations_by_user_ids(self, task_id, user_ids) -> List[TaskUserRelation]:
        user_relation_list = task_dao.find_user_relation_by_task_id_and_user_ids(
            task_id, user_ids
        )
        return user_relation_list

    def get_user_relations(self, task_id) -> List[TaskUserRelation]:
        return self.get_user_relations_by_user_ids(
            task_id, [self.user_id, SpecialUserId.ALL.value,
                       SpecialUserId.PUBLIC.value]
        )

    def is_public(self, task_id):
        user_relation_list = self.get_user_relations_by_user_ids(
            task_id, [SpecialUserId.PUBLIC.value])
        return len(user_relation_list) > 0

    def check_authority(self, task_id, check_writable=False):
        is_for_public = self.is_public(task_id)
        if is_for_public:
            if check_writable and self.user_id != SpecialUserId.PUBLIC.value:
                raise NoAuthorityException(
                    "no authority for editing this task")
            else:
                return
        user_relation_list = self.get_user_relations_by_user_ids(
            task_id, [self.user_id, SpecialUserId.ALL.value])
        if len(user_relation_list) == 0:
            raise NoAuthorityException("no authority for this task")
        if check_writable:
            for user_relation in user_relation_list:
                if PermissionLevelDict[user_relation.permission] >= PermissionLevelDict[Permission.WRITE.value]:
                    return
            raise NoAuthorityException(
                "no authority for changing this analysis")
        return user_relation_list

    def share_to_all(self, object_id):
        pass

    def cancel_share_to_all(self, object_id):
        pass

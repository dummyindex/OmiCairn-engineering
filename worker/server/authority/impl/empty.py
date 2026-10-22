
from authority.guardian import AuthorityGrardian


class EmptyGuardian(AuthorityGrardian):

    def get_user_relations(self, object_id):
        return []

    def check_authority(self, object_id, check_writable=False):
        return

    def share_to_all(self, object_id):
        return

    def cancel_share_to_all(self, object_id):
        return

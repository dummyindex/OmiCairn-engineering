from constants.authority import Permission, Relation, AuthorityCarrier
from authority.impl.analysis import AnalysisGuardian
from authority.guardian import AuthorityGrardian
from authority.impl.empty import EmptyGuardian
from authority.impl.node import NodeGuardian


class AuthorityGuardianFactory:

    @staticmethod
    def get_authority_guardian(carrier=None) -> AuthorityGrardian:
        if carrier == AuthorityCarrier.ANALYSIS.value:
            return AnalysisGuardian()
        if carrier == AuthorityCarrier.NODE.value:
            return NodeGuardian(AnalysisGuardian())
        return EmptyGuardian()

from constants.common import AugmentedEnum

class InvitationStatus(AugmentedEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class ObjectType(AugmentedEnum):
    ANALYSIS = "analysis"
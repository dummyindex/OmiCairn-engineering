from db import alchemy_db as db

class CollaborationInvitation(db.Model):
    __tablename__ = 'collaboration_invitation'
    id = db.Column(db.BIGINT, primary_key=True, autoincrement=True)
    inviter_id = db.Column(db.BIGINT, nullable=False)
    invitee_id = db.Column(db.BIGINT, nullable=False)
    otype = db.Column(db.VARCHAR(255), nullable=False)
    oid = db.Column(db.BIGINT, nullable=False)
    permission = db.Column(db.VARCHAR(255), nullable=False)
    created_time = db.Column(db.DATETIME, nullable=False)
    status = db.Column(db.VARCHAR(255), nullable=False)
    response_time = db.Column(db.DATETIME)
    message = db.Column(db.TEXT)
    oname = db.Column(db.VARCHAR(255))
    inform_id = db.Column(db.BIGINT)

    def to_dict(self):
        return {
            "id": self.id,
            "inviterId": self.inviter_id,
            "inviteeId": self.invitee_id,
            "otype": self.otype,
            "oid": self.oid,
            "permission": self.permission,
            "createdTime": None if self.created_time is None else self.created_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": self.status,
            "responseTime": None if self.response_time is None else self.response_time.strftime("%Y-%m-%d %H:%M:%S"),
            "message": self.message,
            "oname": self.oname,
            "informId": self.inform_id
        }
from db import alchemy_db as db
from model.collaboration_invitation import CollaborationInvitation
from model.user import User
from typing import List

class CollaborationInvitationDao:
    def insert(self, collaboration_invitation: CollaborationInvitation) -> CollaborationInvitation:
        db.session.add(collaboration_invitation)
        db.session.flush()
        return collaboration_invitation

    def find_by_id(self, id) -> CollaborationInvitation:
        return CollaborationInvitation.query.filter(CollaborationInvitation.id == id).first()
    
    def find_by_inviter_id_and_otype_and_oid(self, inviter_id, otype, oid) -> List[CollaborationInvitation]:
        return db.session.query(
            CollaborationInvitation.id.label("id"),
            CollaborationInvitation.inviter_id.label("inviter_id"),
            CollaborationInvitation.invitee_id.label("invitee_id"),
            CollaborationInvitation.otype.label("otype"),
            CollaborationInvitation.oid.label("oid"),
            CollaborationInvitation.status.label("status"),
            CollaborationInvitation.permission.label("permission"),
            CollaborationInvitation.created_time.label("created_time"),
            CollaborationInvitation.message.label("message"),
            CollaborationInvitation.oname.label("oname"),
            User.user_name.label("invitee_name")
        ).join(
            User,
            CollaborationInvitation.invitee_id == User.id
        ).filter(
            CollaborationInvitation.inviter_id == inviter_id,
            CollaborationInvitation.otype == otype,
            CollaborationInvitation.oid == oid
        ).order_by(CollaborationInvitation.created_time.desc()).all()
    
    def find_by_invitee_id_and_otype(self, invitee_id, otype, offset, limit):
        return db.session.query(
            CollaborationInvitation.id.label("id"),
            CollaborationInvitation.inviter_id.label("inviter_id"),
            CollaborationInvitation.invitee_id.label("invitee_id"),
            CollaborationInvitation.otype.label("otype"),
            CollaborationInvitation.oid.label("oid"),
            CollaborationInvitation.status.label("status"),
            CollaborationInvitation.permission.label("permission"),
            CollaborationInvitation.created_time.label("created_time"),
            CollaborationInvitation.message.label("message"),
            CollaborationInvitation.oname.label("oname"),
            User.user_name.label("inviter_name")
        ).join(
            User,
            CollaborationInvitation.inviter_id == User.id
        ).filter(
            CollaborationInvitation.invitee_id == invitee_id,
            CollaborationInvitation.otype == otype
        ).order_by(CollaborationInvitation.created_time.desc()).offset(offset).limit(limit).all()
    
    def update(self, invitation_id, updated_attrs: dict):
        CollaborationInvitation.query.filter(CollaborationInvitation.id == invitation_id).update(updated_attrs)
        db.session.flush()

    def delete(self, invitation_id):
        CollaborationInvitation.query.filter(CollaborationInvitation.id == invitation_id).delete()
        db.session.flush()
    
collaboration_invitation_dao = CollaborationInvitationDao()
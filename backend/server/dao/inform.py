from db import alchemy_db as db
from model.announcement import Announcement
from model.announcement_read_record import AnnouncementReadRecord
from model.inform import Inform
from sqlalchemy import and_
from typing import List

class InformDao:
    def find_announcement_by_id(self, announcement_id) -> Announcement:
        announcement = Announcement.query.filter(Announcement.id == announcement_id).first()
        return announcement

    def find_inform_by_id(self, inform_id) -> Inform:
        inform = Inform.query.filter(Inform.id == inform_id).first()
        return inform

    def find_unread_informs_by_receiver_id(self, user_id, offset, limit) -> List[Inform]:
        unread_informs = Inform.query.filter(
            and_(
                Inform.receiver_id == user_id,
                Inform.have_read == False
            )
        ).order_by(Inform.created_time.desc()).offset(offset).limit(limit).all()
        return unread_informs

    def find_unread_inform_count_by_receiver_id(self, user_id) -> int:
        unread_inform_count = Inform.query.filter(
            and_(
                Inform.receiver_id == user_id,
                Inform.have_read == False
            )
        ).count()
        return unread_inform_count

    def find_unread_informs_by_receiver_id_and_type(self, user_id, inform_type) -> List[Inform]:
        unread_informs = Inform.query.filter(
            and_(
                Inform.receiver_id == user_id,
                Inform.have_read == False,
                Inform.type == inform_type
            )
        ).order_by(Inform.created_time.desc()).all()
        return unread_informs

    def find_unread_announcements_by_receiver_id(self, user_id) -> List[Announcement]:
        unread_announcements = Announcement.query.filter(
            Announcement.id.notin_(
                db.session.query(AnnouncementReadRecord.announcement_id).filter(
                    AnnouncementReadRecord.user_id == user_id
                )
            )
        ).order_by(Announcement.created_time.desc()).all()
        return unread_announcements

    def find_inform_history_by_receiver_id(self, user_id, inform_type, offset, limit) -> List[Inform]:
        query_contition = Inform.receiver_id == user_id if inform_type is None else and_(
            Inform.receiver_id == user_id,
            Inform.type == inform_type
        )
        inform_history = Inform.query.filter(
            query_contition
        ).order_by(Inform.created_time.desc()).offset(offset).limit(limit).all()
        return inform_history

    def find_announcement_history(self, user_id, offset, limit) -> List[Announcement]:
        announcement_history = db.session.query(Announcement).join(
            AnnouncementReadRecord,
            and_(
                Announcement.id == AnnouncementReadRecord.announcement_id,
                AnnouncementReadRecord.user_id == user_id
            ),
            isouter=True
        ).order_by(Announcement.created_time.desc()).offset(offset).limit(limit).all()
        return announcement_history

    def find_announcement_read_record(self, user_id, announcement_id) -> AnnouncementReadRecord:
        announcement_read_record = AnnouncementReadRecord.query.filter(
            and_(
                AnnouncementReadRecord.user_id == user_id,
                AnnouncementReadRecord.announcement_id == announcement_id
            )
        ).first()
        return announcement_read_record

    def find_inform_history_by_sender_id_and_type(self, user_id, type) -> List[Inform]:
        inform_history = Inform.query.filter(
            and_(
                Inform.sender_id == user_id,
                Inform.type == type
            )
        ).order_by(Inform.created_time.desc()).all()
        return inform_history

    def find_inform_count_by_receiver_id(self, user_id) -> int:
        inform_count = Inform.query.filter(Inform.receiver_id == user_id).count()
        return inform_count

    def insert_inform(self, inform: Inform) -> Inform:
        db.session.add(inform)
        db.session.flush()
        return inform

    def insert_announcement(self, announcement: Announcement) -> Announcement:
        db.session.add(announcement)
        db.session.flush()
        return announcement

    def insert_announcement_read_record(self, announcement_read_record: AnnouncementReadRecord) -> AnnouncementReadRecord:
        db.session.add(announcement_read_record)
        db.session.flush()
        return announcement_read_record

    def update_inform(self, inform_id, updated_attrs: dict) -> None:
        Inform.query.filter(Inform.id == inform_id).update(updated_attrs)
        db.session.flush()

    def update_inform_batch(self, inform_id_list, updated_attrs: dict) -> None:
        Inform.query.filter(Inform.id.in_(inform_id_list)).update(updated_attrs, synchronize_session=False)
        db.session.flush()

    def delete_inform(self, inform_id) -> None:
        Inform.query.filter(Inform.id == inform_id).delete()
        db.session.flush()

    def delete_informs_by_receiver_id(self, user_id) -> None:
        Inform.query.filter(Inform.receiver_id == user_id).delete()
        db.session.flush()

inform_dao = InformDao()

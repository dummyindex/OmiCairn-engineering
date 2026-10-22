from dao.inform import inform_dao
import json
from model.announcement import Announcement
from model.announcement_read_record import AnnouncementReadRecord
from model.inform import Inform
from datetime import datetime
from constants.inform import InformType
from constants.invitation import InvitationStatus

class InformService:
    def get_announcement_detail(self, announcement_id):
        announcement = inform_dao.find_announcement_by_id(announcement_id)
        return announcement

    def get_inform_detail(self, inform_id):
        inform = inform_dao.find_inform_by_id(inform_id)
        return inform

    def get_unread_informs_by_user_id(self, user_id, offset, limit):
        unread_informs = inform_dao.find_unread_informs_by_receiver_id(user_id, offset, limit)
        total = inform_dao.find_unread_inform_count_by_receiver_id(user_id)
        return unread_informs, total

    def get_unread_announcements_by_user_id(self, user_id):
        unread_announcements = inform_dao.find_unread_announcements_by_receiver_id(user_id)
        return unread_announcements

    def get_inform_history_by_receiver_id(self, receiver_id, inform_type, offset, limit):
        inform_history = inform_dao.find_inform_history_by_receiver_id(receiver_id, inform_type, offset, limit)
        return inform_history

    def get_announcement_list(self, user_id, offset, limit):
        announcement_list = inform_dao.find_announcement_history(user_id, offset, limit)
        return announcement_list

    def create_announcement(self, title, content):
        now = datetime.now()
        content = json.dumps({
            "title": title,
            "content": content
        })
        announcement = Announcement(
            content=content,
            created_time=now
        )
        return announcement

    def read_announcement(self, user_id, announcement_id):
        now = datetime.now()
        read_record = inform_dao.find_announcement_read_record(user_id, announcement_id)
        if read_record is not None:
            return read_record
        read_record = AnnouncementReadRecord(
            user_id=user_id,
            announcement_id=announcement_id,
            read_time=now
        )
        inform_dao.insert_announcement_read_record(read_record)
        return read_record

    def read_informs(self, inform_id_list):
        inform = inform_dao.update_inform_batch(inform_id_list, {"have_read": True})
        return inform

    def create_computation_end_notice_inform(self, sender_id, receiver_id, computation_id):
        now = datetime.now()
        payload = json.dumps({
            "computationId": computation_id
        })
        inform = Inform(
            sender_id=sender_id,
            receiver_id=receiver_id,
            created_time=now,
            have_read=False,
            type=InformType.COMPUTATION_END_NOTICE.value,
            payload=payload
        )
        return inform

    def insert_announcement_read_record(self, announcement_read_record):
        announcement_read_record = inform_dao.insert_announcement_read_record(announcement_read_record)
        return announcement_read_record

    def get_inform_count(self, user_id):
        unread_inform_count = inform_dao.find_inform_count_by_receiver_id(user_id)
        return unread_inform_count

inform_service = InformService()

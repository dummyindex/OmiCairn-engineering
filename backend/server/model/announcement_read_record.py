from db import alchemy_db as db

class AnnouncementReadRecord(db.Model):
    __tablename__ = 'announcement_read_record'

    id = db.Column(db.BIGINT, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BIGINT, nullable=False)
    announcement_id = db.Column(db.BIGINT, nullable=False)
    read_time = db.Column(db.DATETIME, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "announcementId": self.announcement_id,
            "readTime": None if self.read_time is None else self.read_time.strftime("%Y-%m-%d %H:%M:%S")
        }
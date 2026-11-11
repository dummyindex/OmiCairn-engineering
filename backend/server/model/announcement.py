from db import alchemy_db as db

class Announcement(db.Model):
    __tablename__ = 'announcement'

    id = db.Column(db.BIGINT, primary_key=True, autoincrement=True)
    content = db.Column(db.TEXT, nullable=False)
    created_time = db.Column(db.DATETIME, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "createdTime": None if self.created_time is None else self.created_time.strftime("%Y-%m-%d %H:%M:%S")
        }
from db import alchemy_db as db

class Inform(db.Model):
    __tablename__ = 'inform'

    id = db.Column(db.BIGINT, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.BIGINT, nullable=False)
    receiver_id = db.Column(db.BIGINT, nullable=False)
    created_time = db.Column(db.DATETIME, nullable=False)
    have_read = db.Column(db.BOOLEAN, nullable=False, default=False)
    type = db.Column(db.String(255), nullable=False)
    payload = db.Column(db.TEXT, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "senderId": self.sender_id,
            "receiverId": self.receiver_id,
            "createdTime": None if self.created_time is None else self.created_time.strftime("%Y-%m-%d %H:%M:%S"),
            "haveRead": self.have_read,
            "type": self.type,
            "payload": self.payload
        }
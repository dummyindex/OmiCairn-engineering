from db import alchemy_db as db

class APIKey(db.Model):
    __tablename__ = 'api_key'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger)
    name = db.Column(db.String(255))
    value = db.Column(db.String(255))
    created_time = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'name': self.name,
            'value': self.value,
            'createdTime': self.created_time
        }
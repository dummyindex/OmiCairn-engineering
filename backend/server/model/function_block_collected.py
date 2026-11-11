# CREATE TABLE function_block_collected(
#     id BIGINT PRIMARY KEY AUTO_INCREMENT,
#     function_block_id BIGINT NOT NULL,
#     user_id BIGINT NOT NULL,
#     created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
# );

from db import alchemy_db as db

class FunctionBlockCollected(db.Model):
    __tablename__ = "function_block_collected"
    id = db.Column(db.BIGINT, primary_key=True, autoincrement=True)
    function_block_id = db.Column(db.BIGINT, nullable=False)
    user_id = db.Column(db.BIGINT, nullable=False)
    created_time = db.Column(db.DATETIME)

    def to_dict(self):
        return {
            "id": self.id,
            "functionBlockId": self.function_block_id,
            "userId": self.user_id,
            "createdTime": self.created_time
        }
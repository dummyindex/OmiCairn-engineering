from db import alchemy_db as db


class DynamicGenerationBranch(db.Model):
    __tablename__ = 'dynamic_generation_branch'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    dynamic_generation_id = db.Column(db.BigInteger, nullable=False)
    end_node_id = db.Column(db.BigInteger, nullable=False)
    state = db.Column(db.String(255), nullable=False)
    created_time = db.Column(db.DateTime, nullable=False)
    updated_time = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "dynamicGenerationId": self.dynamic_generation_id,
            "endNodeId": self.end_node_id,
            "state": self.state,
            "createdTime": self.created_time.timestamp() * 1000 if self.created_time else None,
            "updatedTime": self.updated_time.timestamp() * 1000 if self.updated_time else None
        }

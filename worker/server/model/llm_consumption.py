from db import alchemy_db as db


class LLMConsumption(db.Model):
    __tablename__ = 'llm_consumption'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    prompt_tokens = db.Column(db.Integer, nullable=False)
    completion_tokens = db.Column(db.Integer, nullable=False)
    reasoning_tokens = db.Column(db.Integer, nullable=True)
    total_tokens = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Numeric(10, 4), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    model = db.Column(db.String(255), nullable=False)
    functionality = db.Column(db.String(255), nullable=False)
    functionality_task_id = db.Column(db.BigInteger, nullable=False)
    node_id = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.BigInteger, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "promptTokens": self.prompt_tokens,
            "completionTokens": self.completion_tokens,
            "reasoningTokens": self.reasoning_tokens,
            "totalTokens": self.total_tokens,
            "cost": str(self.cost) if self.cost is not None else None,
            "createdAt": self.created_at and self.created_at.timestamp(
            ) * 1000,
            "model": self.model,
            "functionality": self.functionality,
            "functionalityTaskId": self.functionality_task_id,
            "nodeId": self.node_id,
            "userId": self.user_id
        }

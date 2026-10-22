from db import alchemy_db as db

class TaskUserRelation(db.Model):
    __tablename__ = 'task_user_relation'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    task_id = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.BigInteger, nullable=False)
    relation = db.Column(db.String(100), nullable=False)
    permission = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        task_user_relation_attrs_dict = dict()
        task_user_relation_attrs_dict["id"] = self.id
        task_user_relation_attrs_dict["taskId"] = self.task_id
        task_user_relation_attrs_dict["userId"] = self.user_id
        task_user_relation_attrs_dict["relation"] = self.relation
        task_user_relation_attrs_dict["permission"] = self.permission
        return task_user_relation_attrs_dict
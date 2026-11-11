from db import alchemy_db as db


class TaskEdgeRelation(db.Model):
    __tablename__ = "task_edge_relation"
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    task_id = db.Column(db.BigInteger)
    edge_id = db.Column(db.BigInteger)
    created_time = db.Column(db.DateTime)

    def to_dict(self):
        task_edge_relation_attrs_dict = dict()
        task_edge_relation_attrs_dict["id"] = self.id
        task_edge_relation_attrs_dict["taskId"] = self.task_id
        task_edge_relation_attrs_dict["edgeId"] = self.edge_id
        task_edge_relation_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000
        return task_edge_relation_attrs_dict

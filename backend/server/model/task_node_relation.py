from db import alchemy_db as db


class TaskNodeRelation(db.Model):
    __tablename__ = "task_node_relation"
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    task_id = db.Column(db.BigInteger)
    node_id = db.Column(db.BigInteger)
    created_time = db.Column(db.DateTime)
    is_root = db.Column(db.Boolean)
    is_leaf = db.Column(db.Boolean)
    relation_type = db.Column(db.String(50))

    def to_dict(self):
        task_node_relation_attrs_dict = dict()
        task_node_relation_attrs_dict["id"] = self.id
        task_node_relation_attrs_dict["taskId"] = self.task_id
        task_node_relation_attrs_dict["nodeId"] = self.node_id
        task_node_relation_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000
        task_node_relation_attrs_dict["isRoot"] = self.is_root
        task_node_relation_attrs_dict["isLeaf"] = self.is_leaf
        task_node_relation_attrs_dict["relationType"] = self.relation_type
        return task_node_relation_attrs_dict

from db import alchemy_db as db


class Edge(db.Model):
    __tablename__ = 'edge'
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    created_time = db.Column(db.DateTime)
    source_node_id = db.Column(db.BigInteger)
    target_node_id = db.Column(db.BigInteger)
    analysis_id = db.Column(db.BigInteger)

    def to_dict(self):
        edge_attrs_dict = dict()
        edge_attrs_dict["id"] = self.id
        edge_attrs_dict["createdTime"] = self.created_time.timestamp(
        ) * 1000
        edge_attrs_dict["sourceNodeId"] = self.source_node_id
        edge_attrs_dict["targetNodeId"] = self.target_node_id
        edge_attrs_dict["analysisId"] = self.analysis_id
        return edge_attrs_dict

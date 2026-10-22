from db import alchemy_db as db

# CREATE TABLE `figure` (
#   `id` bigint NOT NULL AUTO_INCREMENT,
#   `computation_id` bigint DEFAULT NULL,
#   `figure_name` varchar(255) DEFAULT NULL,
#   `figure_uuid` varchar(255) DEFAULT NULL,
#   `created_time` datetime DEFAULT NULL,
#   `node_id` bigint DEFAULT NULL,
#   PRIMARY KEY (`id`),
#   KEY `figure_name` (`figure_name`),
#   KEY `computation_id` (`computation_id`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3


class Figure(db.Model):
    __tablename__ = 'figure'
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    computation_id = db.Column(db.BigInteger, comment='computation id')
    figure_name = db.Column(db.String(255), comment='figure name')
    figure_uuid = db.Column(db.String(255), comment='figure uuid')
    created_time = db.Column(db.DateTime, comment='created time')
    node_id = db.Column(db.BigInteger, comment='node id')

    def to_dict(self):
        figure_attrs_dict = dict()
        figure_attrs_dict["id"] = self.id
        figure_attrs_dict["computationId"] = self.computation_id
        figure_attrs_dict["figureName"] = self.figure_name
        figure_attrs_dict["figureUuid"] = self.figure_uuid
        figure_attrs_dict["createdTime"] = self.created_time.strftime(
            "%Y-%m-%d %H:%M:%S") if self.created_time else None
        figure_attrs_dict["nodeId"] = self.node_id
        return figure_attrs_dict

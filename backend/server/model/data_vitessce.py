from db import alchemy_db as db
# CREATE TABLE `data_vitessce` (
#   `id` bigint NOT NULL AUTO_INCREMENT,
#   `data_id` bigint NOT NULL,
#   `vitessce_query_string` text NOT NULL,
#   `status` varchar(255) NOT NULL,
#   `status_reason` text NOT NULL,
#   `created_time` datetime NOT NULL,
#   `name` varchar(255) NOT NULL DEFAULT '',
#   `job_ident` varchar(255) NOT NULL DEFAULT '',
#   PRIMARY KEY (`id`),
#   KEY `data_vitessce_data_id` (`data_id`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3


class DataVitessce(db.Model):
    __tablename__ = 'data_vitessce'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    data_id = db.Column(db.BigInteger, nullable=False)
    vitessce_query_string = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(255), nullable=False)
    status_reason = db.Column(db.Text, nullable=False)
    created_time = db.Column(db.DateTime, nullable=False)
    name = db.Column(db.String(255), nullable=False, default='')
    job_ident = db.Column(db.String(255), nullable=False, default='')
    options = db.Column(db.Text, nullable=False)
    node_id = db.Column(db.BigInteger, nullable=False)

    def to_dict(self):
        attrs = dict()
        attrs['id'] = self.id
        attrs['dataId'] = self.data_id
        attrs['vitessceQueryString'] = self.vitessce_query_string
        attrs['status'] = self.status
        attrs['statusReason'] = self.status_reason
        attrs['createdTime'] = self.created_time
        attrs['name'] = self.name
        attrs['jobIdent'] = self.job_ident
        attrs['options'] = self.options
        attrs['nodeId'] = self.node_id
        return attrs
    
    def __repr__(self):
        return str(self.to_dict())
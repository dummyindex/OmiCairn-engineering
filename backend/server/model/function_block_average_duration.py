from db import alchemy_db as db


class FunctionBlockAverageDuration(db.Model):
    __tablename__ = 'function_block_average_duration'
    id = db.Column(db.BigInteger, primary_key=True,
                   autoincrement=True, comment='ID')
    function_block_version_id = db.Column(db.BigInteger)
    avg_duration = db.Column(db.Double)
    system_env = db.Column(db.String(100))
    computation_resource_configure = db.Column(db.String(150))

    def to_dict(self):
        result_dict = dict()
        result_dict["id"] = self.id
        result_dict["functionBlockVersionId"] = self.function_block_version_id
        result_dict["avgDuration"] = self.avg_duration
        result_dict["systemEnv"] = self.system_env
        result_dict["computationResourceConfigure"] = self.computation_resource_configure
        return result_dict

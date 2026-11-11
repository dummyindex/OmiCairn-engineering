from db import alchemy_db
from model.computation_log import ComputationLog


class ComputationLogDao:

    def insert(self, computation_log: ComputationLog):
        alchemy_db.session.add(computation_log)
        alchemy_db.session.commit()

    def get_by_id(self, id: int):
        return ComputationLog.query.filter_by(id=id).first()

    def get_by_computation_id(self, computation_id: int) -> ComputationLog:
        return ComputationLog.query.filter_by(computation_id=computation_id).first()


computation_log_dao = ComputationLogDao()

from db import alchemy_db as db
from model.data import Data
from model.data_user_relation import DataUserRelation
from model.data_change_history import DataChangeHistory
from sqlalchemy import and_


class DataDao:
    def insert(self, data):
        db.session.add(data)
        db.session.flush()
        return data

    def insert_user_relation(self, data_user_relation: DataUserRelation):
        db.session.add(data_user_relation)
        db.session.flush()
        return data_user_relation

    def find_by_id(self, data_id) -> Data:
        return Data.query.filter(Data.id == data_id).first()

    def find_change_history_by_data_id(self, data_id):
        l = DataChangeHistory.query.filter(
            and_(
                DataChangeHistory.data_id == data_id,
                DataChangeHistory.merged == False
            )).order_by(DataChangeHistory.created_time.asc()).all()
        return [i.to_dict() for i in l]

    def update(self, data_id, attrs: dict) -> None:
        Data.query.filter(
            Data.id == data_id
        ).update(attrs)
        db.session.flush()

    def delete(self, data_id) -> None:
        Data.query.filter(
            Data.id == data_id
        ).delete()

    def delete_by_id_list(self, id_list) -> None:
        Data.query.filter(
            Data.id.in_(id_list)
        ).delete()


data_dao = DataDao()

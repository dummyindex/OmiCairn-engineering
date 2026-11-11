from db import alchemy_db as db
from model.data import Data
from model.computation import Computation
from model.task import Task
from constants.authority import Relation
from model.analysis_data_relation import AnalysisDataRelation
from sqlalchemy import and_, or_, func, extract
from typing import List
from model.data_user_relation import DataUserRelation
from log.logger_factory import logger_factory
from constants.data import CreatedFrom, DataState

logger = logger_factory.create_logger("data_dao")

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
    
    def find_isolated_and_not_buried_by_created_from_with_page(self, created_from, offset, limit) -> List[Data]:
        return db.session.query(
            Data.id.label('data_id'),
            Computation.id.label('computation_id')
        ).outerjoin(
            Computation,
            Data.id == Computation.result_data_id
        ).filter(
            and_(
                Data.created_from == created_from,
                Data.buried == False,
                Computation.id == None
            )
        ).offset(offset).limit(limit).all()

    def find_by_user_id_and_upload_type(self, user_id, upload_type, search_key) -> List[Data]:
        if upload_type is None:
            return self.find_by_user_id(user_id)
        if type(upload_type) == str:
            upload_type = [upload_type]
        user_relation_list = self.find_user_relation_by_user_id(user_id)
        data_id_list = [user_relation.data_id for user_relation in user_relation_list]
        query = Data.query.filter(
            and_(
                Data.id.in_(data_id_list),
                Data.upload_type.in_(upload_type)
            )
        )
        if search_key is None:
            return query.all()
        return query.filter(
            or_(
                Data.name.like(f"%{search_key}%"),
                Data.species.like(f"%{search_key}%")
            )
        ).all()
    
    def find_by_user_id_and_created_from(self, user_id, created_from, search_key) -> List[Data]:
        user_relation_list = self.find_user_relation_by_user_id(user_id)
        data_id_list = [user_relation.data_id for user_relation in user_relation_list]
        query = Data.query.filter(
            and_(
                Data.id.in_(data_id_list),
                Data.created_from == created_from
            )
        )
        if search_key is None:
            return query.all()
        return query.filter(
            or_(
                Data.name.like(f"%{search_key}%"),
                Data.species.like(f"%{search_key}%")
            )
        ).all()
    
    def find_by_user_id_and_created_from_and_state(self, user_id, created_from, state, search_key) -> List[Data]:
        user_relation_list = self.find_user_relation_by_user_id(user_id)
        data_id_list = [user_relation.data_id for user_relation in user_relation_list]
        query = Data.query.filter(
            and_(
                Data.id.in_(data_id_list),
                Data.created_from == created_from,
                Data.state == state
            )
        )
        if search_key is None:
            return query.all()
        return query.filter(
            or_(
                Data.name.like(f"%{search_key}%"),
                Data.species.like(f"%{search_key}%")
            )
        ).all()

    def find_by_id_list(self, data_id_list) -> List[Data]:
        return Data.query.filter(
            Data.id.in_(data_id_list)
        ).all()

    def find_user_relation_by_user_id(self, user_id) -> List[DataUserRelation]:
        return DataUserRelation.query.filter(
            DataUserRelation.user_id == user_id
        ).all()
    
    def find_user_relation_by_data_id_and_user_id(self, data_id, user_id, relation) -> DataUserRelation:
        if relation is not None:
            return DataUserRelation.query.filter(
                and_(
                    DataUserRelation.data_id == data_id,
                    DataUserRelation.user_id == user_id,
                    DataUserRelation.relation == relation
                )
            ).first()
        return DataUserRelation.query.filter(
            and_(
                DataUserRelation.data_id == data_id,
                DataUserRelation.user_id == user_id
            )
        ).first()

    def find_recent_unrecorded_size(self) -> List[Data]:
        return Data.query.filter(
            Data.data_size == None
        ).all()

    def update(self, data_id, attrs: dict) -> None:
        Data.query.filter(
            Data.id == data_id
        ).update(attrs)
        db.session.flush()

    def update_by_id_list(self, id_list, attrs: dict) -> None:
        Data.query.filter(
            Data.id.in_(id_list)
        ).update(attrs)
        db.session.flush()

    def find_by_user_id_and_collected(self, owner_id, collected, search_key) -> List[Data]:
        user_relation_list = self.find_user_relation_by_user_id(owner_id)
        data_id_list = [user_relation.data_id for user_relation in user_relation_list]
        query = Data.query.filter(
            and_(
                Data.id.in_(data_id_list),
                Data.collected == collected
            )
        )
        if search_key is None:
            return query.all()
        return query.filter(
            or_(
                Data.name.like(f"%{search_key}%"),
                Data.species.like(f"%{search_key}%")
            )
        ).all()

    def find_by_user_id(self, user_id, search_key = None) -> List[Data]:
        user_relation_list = self.find_user_relation_by_user_id(user_id)
        data_id_list = [user_relation.data_id for user_relation in user_relation_list]
        if search_key is None or not search_key:
            return Data.query.filter(
                Data.id.in_(data_id_list)
            ).all()

        return Data.query.filter(
            and_(
                Data.id.in_(data_id_list),
                or_(
                    Data.name.like(f"%{search_key}%"),
                    Data.species.like(f"%{search_key}%"),
                    Data.description.like(f"%{search_key}%")
                )
            )
        ).all()

    def find_by_user_id_and_state(self, user_id, state, search_key = None) -> List[Data]:
        user_relation_list = self.find_user_relation_by_user_id(user_id)
        data_id_list = [user_relation.data_id for user_relation in user_relation_list]
        if search_key is None:
            return Data.query.filter(
                and_(
                    Data.id.in_(data_id_list),
                    Data.state == state
                )
            ).all()
        return Data.query.filter(
            and_(
                Data.id.in_(data_id_list),
                Data.state == state,
                or_(
                    Data.name.like(f"%{search_key}%"),
                    Data.species.like(f"%{search_key}%"),
                    Data.description.like(f"%{search_key}%")
                )
            )
        ).order_by(Data.created_time.desc()).all()
    
    def find_data_source_count_by_user_id(self, user_id, search_key, only_ok):
        search_key = search_key if search_key is not None else ""
        conditions = and_(
                DataUserRelation.user_id == user_id,
                DataUserRelation.relation == Relation.BELONG_TO.value,
                Data.state == DataState.OK.value,
                Data.name.like(f"%{search_key}%")
            ) if only_ok else and_(
                DataUserRelation.user_id == user_id,
                DataUserRelation.relation == Relation.BELONG_TO.value,
                Data.name.like(f"%{search_key}%")
            )

        return db.session.query(
            Data
        ).join(
            DataUserRelation,
            Data.id == DataUserRelation.data_id
        ).filter(
            conditions
        ).order_by(Data.created_time.desc()).count()
    
    def find_data_source_page_by_user_id(self, user_id, page, page_size, search_key, only_ok):
        search_key = search_key if search_key is not None else ""
        conditions = and_(
                DataUserRelation.user_id == user_id,
                DataUserRelation.relation == Relation.BELONG_TO.value,
                Data.state == DataState.OK.value,
                Data.name.like(f"%{search_key}%")
            ) if only_ok else and_(
                DataUserRelation.user_id == user_id,
                DataUserRelation.relation == Relation.BELONG_TO.value,
                Data.name.like(f"%{search_key}%")
            )
        return db.session.query(
            Data
        ).join(
            DataUserRelation,
            Data.id == DataUserRelation.data_id
        ).filter(
            conditions
        ).order_by(Data.created_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    def find_index_by_user_id(self, data_id, user_id, search_key, only_ok):
        data = self.find_by_id(data_id)
        search_key = search_key if search_key is not None else ""
        conditions = and_(
                DataUserRelation.user_id == user_id,
                DataUserRelation.relation == Relation.BELONG_TO.value,
                Data.state == DataState.OK.value,
                Data.name.like(f"%{search_key}%"),
                Data.created_time > data.created_time
            ) if only_ok else and_(
                DataUserRelation.user_id == user_id,
                DataUserRelation.relation == Relation.BELONG_TO.value,
                Data.name.like(f"%{search_key}%"),
                Data.created_time > data.created_time
            )
        return db.session.query(
            Data
        ).join(
            DataUserRelation,
            Data.id == DataUserRelation.data_id
        ).filter(
            conditions
        ).order_by(Data.created_time.desc()).count()
    
    def find_by_state(self, state) -> List[Data]:
        return Data.query.filter(
            Data.state == state
        ).all()

    def delete(self, data_id) -> None:
        Data.query.filter(
            Data.id == data_id
        ).delete()
        DataUserRelation.query.filter(
            DataUserRelation.data_id == data_id
        ).delete()
        AnalysisDataRelation.query.filter(
            AnalysisDataRelation.data_id == data_id
        ).delete()

    def delete_by_id_list(self, id_list) -> None:
        Data.query.filter(
            Data.id.in_(id_list)
        ).delete()
        DataUserRelation.query.filter(
            DataUserRelation.data_id.in_(id_list)
        ).delete()

    def find_imported_by_analysis_id(self, analysis_id) -> List[Data]:
        """Find all data associated with a given analysis ID"""
        return db.session.query(
            Data
        ).join(
            AnalysisDataRelation,
            Data.id == AnalysisDataRelation.data_id
        ).filter(
            AnalysisDataRelation.analysis_id == analysis_id
        ).all()

    def find_computation_result_by_analysis_id(self, analysis_id, month=None) -> List[Data]:
        """Find all computation results associated with a given analysis ID"""
        query = db.session.query(
            Data
        ).join(
            Computation,
            Data.id == Computation.result_data_id
        ).join(
            Task,
            Computation.task_id == Task.id
        ).filter(
            Task.analysis_id == analysis_id
        )

        # If month is specified, filter by month
        if month:
            # Parse month string (e.g., "2025-01") to year and month
            year, month_num = map(int, month.split('-'))
            query = query.filter(
                and_(
                    extract('year', Data.created_time) == year,
                    extract('month', Data.created_time) == month_num
                )
            )

        return query.all()


data_dao = DataDao()

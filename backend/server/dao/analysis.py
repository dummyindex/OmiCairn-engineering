from typing import List
from db import alchemy_db
from model.analysis import Analysis
from model.analysis_user_relation import AnalysisUserRelation
from model.analysis_updated_record import AnalysisUpdatedRecord
from model.analysis_data_relation import AnalysisDataRelation
from sqlalchemy import and_
from log.logger_factory import logger_factory
logger = logger_factory.create_logger("AnalysisDao")

class AnalysisDao:
    def insert(self, analysis: Analysis):
        alchemy_db.session.add(analysis)
        alchemy_db.session.flush()
        return analysis

    def insert_user_relation(self, analysis_user_relation: AnalysisUserRelation) -> AnalysisUserRelation:
        alchemy_db.session.add(analysis_user_relation)
        alchemy_db.session.flush()
        return analysis_user_relation

    def find_by_id(self, id):
        analysis: Analysis = Analysis.query.filter(
            Analysis.id == id
        ).first()
        return analysis
    
    def find_count_by_user_id(self, user_id):
        return AnalysisUserRelation.query.filter(
            AnalysisUserRelation.user_id == user_id
        ).count()

    def find_user_relation_by_user_id(self, owner_id) -> List[AnalysisUserRelation]:
        return AnalysisUserRelation.query.filter(
            AnalysisUserRelation.user_id == owner_id
        ).all()

    def find_user_relation_by_analysis_id(self, analysis_id) -> List[AnalysisUserRelation]:
        return AnalysisUserRelation.query.filter(
            AnalysisUserRelation.analysis_id == analysis_id
        ).all()

    def find_user_relation_by_analysis_id_and_user_ids(self, analysis_id, user_ids) -> List[AnalysisUserRelation]:
        return AnalysisUserRelation.query.filter(
            and_(
                AnalysisUserRelation.analysis_id == analysis_id,
                AnalysisUserRelation.user_id.in_(user_ids)
            )
        ).all()

    def update_user_relation(self, analysis_id, user_id, attrs: dict):
        AnalysisUserRelation.query.filter(
            and_(
                AnalysisUserRelation.analysis_id == analysis_id,
                AnalysisUserRelation.user_id == user_id
            )
        ).update(attrs)
        alchemy_db.session.flush()

    def delete_by_id(self, id):
        effect_row_count = Analysis.query.filter(
            Analysis.id == id
        ).delete()
        AnalysisUserRelation.query.filter(
            AnalysisUserRelation.analysis_id == id
        ).delete()
        AnalysisDataRelation.query.filter(
            AnalysisDataRelation.analysis_id == id
        ).delete()
        return effect_row_count

    def delete_by_user_id(self, user_id):
        related_relation_list = AnalysisUserRelation.query.filter(
            AnalysisUserRelation.user_id == user_id
        ).all()
        related_analysis_id_list = [relation.analysis_id for relation in related_relation_list]
        effect_row_count = Analysis.query.filter(
            Analysis.id.in_(related_analysis_id_list)
        ).delete(synchronize_session=False)
        AnalysisUserRelation.query.filter(
            AnalysisUserRelation.user_id == user_id
        ).delete(synchronize_session=False)
        AnalysisDataRelation.query.filter(
            AnalysisDataRelation.analysis_id.in_(related_analysis_id_list)
        ).delete(synchronize_session=False)
        return effect_row_count

    def delete_user_relation_by_analysis_id_and_user_id(self, analysis_id, user_id):
        effect_row_count = AnalysisUserRelation.query.filter(
            and_(
                AnalysisUserRelation.analysis_id == analysis_id,
                AnalysisUserRelation.user_id == user_id
            )
        ).delete()
        return effect_row_count

    def update(self, analysis_id: str, attrs: dict):
        Analysis.query.filter(
            Analysis.id == analysis_id
        ).update(attrs)
        alchemy_db.session.flush()
        
    def update_analysis(self, analysis_id: str, data) -> Analysis:
        Analysis.query.filter(
            Analysis.id == analysis_id 
        ).update(data)
        alchemy_db.session.flush()
        return Analysis.query.filter(Analysis.id == analysis_id).first()

    def update_by_id_list(self, analysis_id_list, attrs: dict):
        Analysis.query.filter(
            Analysis.id.in_(analysis_id_list)
        ).update(attrs)
        alchemy_db.session.flush()

    def find_by_user_id(self, user_id) -> List[Analysis]:
        analysis_columns = [getattr(Analysis, column.name) for column in Analysis.__table__.columns]
        return alchemy_db.session.query(
            *analysis_columns,
            AnalysisUserRelation.relation,
            AnalysisUserRelation.permission
        ).join(
            AnalysisUserRelation, Analysis.id == AnalysisUserRelation.analysis_id
        ).filter(
            AnalysisUserRelation.user_id == user_id
        ).all()
    
    def find_updated_record(self, analysis_id: str) -> AnalysisUpdatedRecord:
        return AnalysisUpdatedRecord.query.filter(
            AnalysisUpdatedRecord.analysis_id == analysis_id
        ).first()

analysis_dao = AnalysisDao()

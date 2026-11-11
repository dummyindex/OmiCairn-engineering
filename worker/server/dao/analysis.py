from typing import List
from db import alchemy_db
from model.analysis import Analysis
from model.analysis_user_relation import AnalysisUserRelation
from sqlalchemy import and_
from log.logger_factory import LoggerFactory
logger = LoggerFactory.get_logger("AnalysisDao")

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

    def delete_by_id(self, id):
        effect_row_count = Analysis.query.filter(
            Analysis.id == id
        ).delete()
        AnalysisUserRelation.query.filter(
            AnalysisUserRelation.analysis_id == id
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
        return effect_row_count

    def delete_user_relation_by_analysis_id_and_user_id(self, analysis_id, user_id):
        effect_row_count = AnalysisUserRelation.query.filter(
            and_(
                AnalysisUserRelation.analysis_id == analysis_id,
                AnalysisUserRelation.user_id == user_id
            )
        ).delete()
        return effect_row_count

    def update(self, analysis_id: Analysis, attrs: dict):
        Analysis.query.filter(
            Analysis.id == analysis_id
        ).update(attrs)
        alchemy_db.session.flush()

    def find_by_user_id(self, user_id) -> List[Analysis]:
        relation_list = self.find_user_relation_by_user_id(user_id)
        analysis_id_list = [relation.analysis_id for relation in relation_list]
        return Analysis.query.filter(
            Analysis.id.in_(analysis_id_list)
        ).all()

analysis_dao = AnalysisDao()

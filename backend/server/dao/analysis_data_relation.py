from model.analysis_data_relation import AnalysisDataRelation
from db import alchemy_db as db
from typing import List

class AnalysisDataRelationDao:
    def insert(self, analysis_data_relation: AnalysisDataRelation):
        db.session.add(analysis_data_relation)
        db.session.flush()
        return analysis_data_relation

    def insert_list(self, analysis_data_relation_list: List[AnalysisDataRelation]):
        db.session.bulk_save_objects(analysis_data_relation_list)
        db.session.flush()
        return analysis_data_relation_list

    def find_by_id(self, analysis_data_relation_id):
        return AnalysisDataRelation.query.filter(
            AnalysisDataRelation.id == analysis_data_relation_id
        ).first()

    def delete(self, analysis_data_relation_id):
        AnalysisDataRelation.query.filter(
            AnalysisDataRelation.id == analysis_data_relation_id
        ).delete()

    def delete_by_analysis_id(self, analysis_id):
        AnalysisDataRelation.query.filter(
            AnalysisDataRelation.analysis_id == analysis_id
        ).delete()

    def delete_by_data_id(self, data_id):
        AnalysisDataRelation.query.filter(
            AnalysisDataRelation.data_id == data_id
        ).delete()

    def delete_by_analysis_id_and_data_id(self, analysis_id, data_id):
        AnalysisDataRelation.query.filter(
            AnalysisDataRelation.analysis_id == analysis_id,
            AnalysisDataRelation.data_id == data_id
        ).delete()

    def find_by_analysis_id(self, analysis_id):
        return AnalysisDataRelation.query.filter(
            AnalysisDataRelation.analysis_id == analysis_id
        ).all()

    def find_by_data_id(self, data_id):
        return AnalysisDataRelation.query.filter(
            AnalysisDataRelation.data_id == data_id
        ).all()

    def find_by_analysis_id_and_data_id(self, analysis_id, data_id) -> AnalysisDataRelation:
        return AnalysisDataRelation.query.filter(
            AnalysisDataRelation.analysis_id == analysis_id,
            AnalysisDataRelation.data_id == data_id
        ).first()


analysis_data_relation_dao = AnalysisDataRelationDao()

from db import alchemy_db
from model.pipeline_template import PipelineTemplate
from model.pipeline_template_user_relation import PipelineTemplateUserRelation
from typing import List
from sqlalchemy import and_


class PipelineTemplateDao:
    def insert(self, pt: PipelineTemplate) -> PipelineTemplate:
        alchemy_db.session.add(pt)
        alchemy_db.session.flush()
        return pt

    def insert_user_relation(self, pt_user_relation: PipelineTemplateUserRelation) -> PipelineTemplateUserRelation:
        alchemy_db.session.add(pt_user_relation)
        alchemy_db.session.flush()
        return pt_user_relation

    def update(self, pt_id, attrs: dict):
        PipelineTemplate.query.filter(
            PipelineTemplate.id == pt_id).update(attrs)
        alchemy_db.session.flush()

    def update_relation_by_pt_id(self, pt_id, attrs: dict):
        PipelineTemplateUserRelation.query.filter(
            PipelineTemplateUserRelation.pipeline_template_id == pt_id).update(attrs)
        alchemy_db.session.flush()

    def update_group_name_by_user_id_and_old_name(self, user_id, old_name, new_name):
        relation_list: List[PipelineTemplateUserRelation] = PipelineTemplateUserRelation.query.filter(
            and_(
                PipelineTemplateUserRelation.user_id == user_id
            )
        ).all()
        pt_id_list = [relation.pipeline_template_id for relation in relation_list]
        PipelineTemplate.query.filter(
            and_(
                PipelineTemplate.id.in_(pt_id_list),
                PipelineTemplate.group_name == old_name
            )
        ).update({
            "group_name": new_name
        })
        alchemy_db.session.flush()

    def delete(self, pt_id):
        PipelineTemplate.query.filter(
            PipelineTemplate.id == pt_id).delete()
        PipelineTemplate.query.filter(
            PipelineTemplate.id == pt_id).delete()
        alchemy_db.session.flush()

    def delete_by_user_id_and_group_name(self, user_id, group_name):
        relation_list: List[PipelineTemplateUserRelation] = PipelineTemplateUserRelation.query.filter(
            and_(
                PipelineTemplateUserRelation.user_id == user_id
            )
        ).all()
        pt_id_list = [relation.pipeline_template_id for relation in relation_list]
        pt_list: List[PipelineTemplate] = PipelineTemplate.query.filter(
            PipelineTemplate.id.in_(pt_id_list)
        )
        for pt in pt_list:
            if pt.group_name == group_name:
                PipelineTemplate.query.filter(
                    PipelineTemplate.id == pt.id
                ).delete()
        alchemy_db.session.flush()

    def find_by_id(self, pt_id) -> PipelineTemplate:
        return PipelineTemplate.query.filter(
            PipelineTemplate.id == pt_id).first()

    def find_by_user_id(self, owner_id) -> List[PipelineTemplate]:
        relation_list: List[PipelineTemplateUserRelation] = PipelineTemplateUserRelation.query.filter(
            and_(
                PipelineTemplateUserRelation.user_id == owner_id
            )
        ).all()
        pt_id_list = [relation.pipeline_template_id for relation in relation_list]
        return PipelineTemplate.query.filter(
            PipelineTemplate.id.in_(pt_id_list)
        ).all()

    def find_by_user_id_and_group_name(self, user_id, group_name) -> List[PipelineTemplate]:
        relation_list: List[PipelineTemplateUserRelation] = PipelineTemplateUserRelation.query.filter(
            and_(
                PipelineTemplateUserRelation.user_id == user_id
            )
        ).all()
        pt_id_list = [relation.pipeline_template_id for relation in relation_list]
        return PipelineTemplate.query.filter(
            and_(
                PipelineTemplate.id.in_(pt_id_list),
                PipelineTemplate.group_name == group_name
            )
        ).all()

    def find_group_name_list(self, user_id) -> List[str]:
        record_list = PipelineTemplate.query.join(
            PipelineTemplateUserRelation,
            PipelineTemplate.id == PipelineTemplateUserRelation.pipeline_template_id
        ).filter(
            PipelineTemplateUserRelation.user_id == user_id
        ).with_entities(
            PipelineTemplate.group_name
        ).distinct().all()

        return [record[0] for record in record_list]


pipeline_template_dao = PipelineTemplateDao()

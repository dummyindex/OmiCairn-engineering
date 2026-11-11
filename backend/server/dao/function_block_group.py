from model.function_block_group import FunctionBlockGroup
from db import alchemy_db
from typing import List
from model.function_block_group_user_relation import FunctionBlockGroupUserRelation


class FunctionBlockGroupDao:
    def insert(self, function_block_group: FunctionBlockGroup):
        alchemy_db.session.add(function_block_group)
        alchemy_db.session.flush()
        return function_block_group

    def insert_user_relation(self, function_block_group_user_relation: FunctionBlockGroupUserRelation):
        alchemy_db.session.add(function_block_group_user_relation)
        alchemy_db.session.flush()
        return function_block_group_user_relation

    def find_by_user_id(self, user_id) -> List[FunctionBlockGroup]:
        relation_list: List[FunctionBlockGroupUserRelation] = FunctionBlockGroupUserRelation.query.filter(
            FunctionBlockGroupUserRelation.user_id == user_id
        ).all()
        function_block_group_id_list = [relation.function_block_group_id for relation in relation_list]
        return FunctionBlockGroup.query.filter(
            FunctionBlockGroup.id.in_(function_block_group_id_list)
        ).all()

    def find_by_id(self, id):
        return FunctionBlockGroup.query.filter(
            FunctionBlockGroup.id == id
        ).first()

    def update(self, id, attrs):
        FunctionBlockGroup.query.filter(
            FunctionBlockGroup.id == id
        ).update(attrs)
        alchemy_db.session.flush()

    def delete(self, id):
        FunctionBlockGroup.query.filter(
            FunctionBlockGroup.id == id
        ).delete()
        FunctionBlockGroupUserRelation.query.filter(
            FunctionBlockGroupUserRelation.function_block_group_id == id
        ).delete()
        alchemy_db.session.flush()

    def delete_by_user_id(self, user_id):
        relation_list: List[FunctionBlockGroupUserRelation] = FunctionBlockGroupUserRelation.query.filter(
            FunctionBlockGroupUserRelation.user_id == user_id
        ).all()
        function_block_group_id_list = [relation.function_block_group_id for relation in relation_list]
        FunctionBlockGroup.query.filter(
            FunctionBlockGroup.id.in_(function_block_group_id_list)
        ).delete()
        FunctionBlockGroupUserRelation.query.filter(
            FunctionBlockGroupUserRelation.user_id == user_id
        ).delete()
        alchemy_db.session.flush()


function_block_group_dao = FunctionBlockGroupDao()

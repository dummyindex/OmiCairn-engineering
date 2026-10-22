from datetime import datetime
from sqlalchemy import and_, case, or_
from model.function_block_v1 import FunctionBlockV1
from model.function_block_user_relation import FunctionBlockUserRelation
from typing import List
from db import alchemy_db, alchemy_db as db
from constants.authority import Relation, SpecialUserId
from model.function_block_version_v1 import FunctionBlockVersionV1
from model.function_block_updated_record import FunctionBlockUpdatedRecord
from model.function_block_collected import FunctionBlockCollected
from constants.function_block import FBOccasion


class FunctionBlockV1Dao:
    def insert(self, function_block: FunctionBlockV1) -> FunctionBlockV1:
        alchemy_db.session.add(function_block)
        alchemy_db.session.flush()
        return function_block

    def insert_user_relation(self, function_block_user_relation: FunctionBlockUserRelation) -> FunctionBlockUserRelation:
        alchemy_db.session.add(function_block_user_relation)
        alchemy_db.session.flush()
        return function_block_user_relation

    def find_by_user_id(self, user_id) -> List[FunctionBlockV1]:
        relation_list: List[FunctionBlockUserRelation] = FunctionBlockUserRelation.query.filter(
            FunctionBlockUserRelation.user_id == user_id
        ).all()
        function_block_id_list = [relation.function_block_id for relation in relation_list]
        return FunctionBlockV1.query.filter(
            FunctionBlockV1.id.in_(function_block_id_list)
        ).all()
    
    def find_id_list_by_user_id(self, user_id) -> List[int]:
        relation_list: List[FunctionBlockUserRelation] = FunctionBlockUserRelation.query.filter(
            FunctionBlockUserRelation.user_id == user_id
        ).all()
        return [relation.function_block_id for relation in relation_list]

    def find_by_id(self, id) -> FunctionBlockV1:
        return FunctionBlockV1.query.filter(
            FunctionBlockV1.id == id
        ).first()
    
    def find_user_relation_by_fb_id(self, fb_id) -> List[FunctionBlockUserRelation]:
        return FunctionBlockUserRelation.query.filter(
            FunctionBlockUserRelation.function_block_id == fb_id
        ).all()

    def find_by_group_id(self, group_id) -> List[FunctionBlockV1]:
        # return FunctionBlockV1.query.filter(
        #     FunctionBlockV1.group_id == group_id
        # ).all()
        return db.session.query(
            FunctionBlockV1.id,
            FunctionBlockV1.name,
            FunctionBlockV1.alt_name,
            FunctionBlockV1.type,
            FunctionBlockV1.created_time,
            FunctionBlockV1.current_version_id,
            FunctionBlockV1.group_id,
            FunctionBlockVersionV1.state,
            FunctionBlockVersionV1.program_language,
            FunctionBlockVersionV1.preset_env,
            FunctionBlockVersionV1.document_url,
            FunctionBlockVersionV1.is_v2,
            FunctionBlockVersionV1.alt_name,
            FunctionBlockVersionV1.plot_only
        ).join(
            FunctionBlockVersionV1, FunctionBlockV1.current_version_id == FunctionBlockVersionV1.id, isouter = True
        ).filter(
            FunctionBlockV1.group_id == group_id
        ).all()

    # TODO: find_by_keyname
    def find_by_keyname(self, keyname) -> List[FunctionBlockV1]:
        return FunctionBlockV1.query.filter(
            or_(
                FunctionBlockV1.name.contains(keyname),
                FunctionBlockV1.alt_name.contains(keyname)
            )
        ).all()
    
    def find_updated_record_list_by_id_list_and_start_time(self, fb_id_list, start_time: datetime) -> List:
        updated_records = FunctionBlockUpdatedRecord.query.filter(
            and_(
                FunctionBlockUpdatedRecord.function_block_id.in_(fb_id_list),
                FunctionBlockUpdatedRecord.updated_time > start_time
            )
        ).all()
        return updated_records
    

    def update(self, id, attrs) -> None:
        FunctionBlockV1.query.filter(
            FunctionBlockV1.id == id
        ).update(attrs)
        alchemy_db.session.flush()

    def update_version(self, version_id, attrs) -> None:
        FunctionBlockVersionV1.query.filter(
            FunctionBlockVersionV1.id == version_id
        ).update(attrs)
        alchemy_db.session.flush()

    def delete(self, id) -> None:
        FunctionBlockV1.query.filter(
            FunctionBlockV1.id == id
        ).delete()
        FunctionBlockUserRelation.query.filter(
            FunctionBlockUserRelation.function_block_id == id
        ).delete()

    def delete_by_user_id(self, user_id) -> None:
        relation_list: List[FunctionBlockUserRelation] = FunctionBlockUserRelation.query.filter(
            FunctionBlockUserRelation.user_id == user_id
        ).all()
        function_block_id_list = [relation.function_block_id for relation in relation_list]
        FunctionBlockV1.query.filter(
            FunctionBlockV1.id.in_(function_block_id_list)
        ).delete()
        FunctionBlockUserRelation.query.filter(
            FunctionBlockUserRelation.user_id == user_id
        ).delete()

    def delete_by_group_id(self, group_id) -> None:
        function_block_list: List[FunctionBlockV1] = FunctionBlockV1.query.filter(
            FunctionBlockV1.group_id == group_id
        ).all()
        function_block_id_list = [function_block.id for function_block in function_block_list]
        FunctionBlockV1.query.filter(
            FunctionBlockV1.id.in_(function_block_id_list)
        ).delete()
        FunctionBlockUserRelation.query.filter(
            FunctionBlockUserRelation.function_block_id.in_(function_block_id_list)
        ).delete()

    # -------------------------------------------

    def find_version_by_id(self, function_block_version_id) -> FunctionBlockVersionV1:
        return FunctionBlockVersionV1.query.filter(
            FunctionBlockVersionV1.id == function_block_version_id
        ).first()

    def find_version_by_function_block_id(self, function_block_id) -> List[FunctionBlockVersionV1]:
        return FunctionBlockVersionV1.query.filter(
            FunctionBlockVersionV1.function_block_id == function_block_id
        ).all()

    def find_version_by_function_block_id_and_name(self, function_block_id, name) -> FunctionBlockVersionV1:

        return FunctionBlockVersionV1.query.filter(
            and_(
                FunctionBlockVersionV1.function_block_id == function_block_id,
                FunctionBlockVersionV1.name == name
            )
        ).first()
    
    def find_version_by_is_v2_and_user_id(self, is_v2, user_id):
        user_relations: List[FunctionBlockUserRelation] = FunctionBlockUserRelation.query.filter(
            and_(
            FunctionBlockUserRelation.user_id == user_id,
            FunctionBlockUserRelation.relation == Relation.BELONG_TO.value
            )
        ).all()
        return db.session.query(
            FunctionBlockV1.id.label("fb_id"),
            FunctionBlockV1.name.label("fb_name"),
            FunctionBlockVersionV1.id.label("fb_version_id"),
            FunctionBlockVersionV1.name.label("fbv_name"),
            FunctionBlockVersionV1.description.label("fbv_description"),
            FunctionBlockVersionV1.source.label("fbv_source"),
            FunctionBlockVersionV1.program_language.label("fbv_program_language"),
            FunctionBlockVersionV1.preset_env.label("fbv_preset_env"),
            FunctionBlockVersionV1.args.label("fbv_args")
        ).join(
            FunctionBlockVersionV1, FunctionBlockV1.current_version_id == FunctionBlockVersionV1.id
        ).filter(
            and_(
                FunctionBlockV1.id.in_([relation.function_block_id for relation in user_relations]),
                FunctionBlockVersionV1.is_v2 == is_v2
            )
        ).all()
    
    def find_fb_version_by_user_id(self, user_id):
        user_relations: List[FunctionBlockUserRelation] = FunctionBlockUserRelation.query.filter(
            and_(
            FunctionBlockUserRelation.user_id == user_id,
            FunctionBlockUserRelation.relation == Relation.BELONG_TO.value
            )
        ).all()
        return db.session.query(
            FunctionBlockV1.id.label("function_block_id"),
            FunctionBlockVersionV1.id.label("function_block_version_id")
        ).join(
            FunctionBlockVersionV1, FunctionBlockV1.id == FunctionBlockVersionV1.function_block_id
        ).filter(
            FunctionBlockV1.id.in_([relation.function_block_id for relation in user_relations])
        )

    # TODO: remove this function on the no long future
    def find_fb_with_version_by_user_id(self, user_id):
        user_relations: List[FunctionBlockUserRelation] = FunctionBlockUserRelation.query.filter(
            FunctionBlockUserRelation.user_id == user_id
        ).all()
        fb_id_list = [user_relation.function_block_id for user_relation in user_relations]
        return db.session.query(
            FunctionBlockV1.id.label('function_block_id'),
            FunctionBlockV1.name.label('function_block_name'),
            FunctionBlockVersionV1.id.label('function_block_version_id'),
            FunctionBlockVersionV1.name.label('function_block_version_name'),
            FunctionBlockVersionV1.args.label('function_block_version_args'),
            FunctionBlockVersionV1.tag.label('function_block_version_tag'),
            FunctionBlockVersionV1.description.label('function_block_version_description'),
            FunctionBlockVersionV1.source.label('function_block_version_source')
        ).join(
            FunctionBlockVersionV1, FunctionBlockV1.current_version_id == FunctionBlockVersionV1.id
        ).filter(
            FunctionBlockV1.id.in_(fb_id_list)
        ).all()

    def find_fb_by_user_id_and_occasion(self, user_id, occasion, offset, limit, search_key):
        user_relations: List[FunctionBlockUserRelation] = FunctionBlockUserRelation.query.filter(
            FunctionBlockUserRelation.user_id == user_id
        ).all()
        fb_id_list = [user_relation.function_block_id for user_relation in user_relations]

        search_key = search_key if search_key else ''

        query = alchemy_db.session.query(
            FunctionBlockV1.id.label('id'),
            FunctionBlockV1.name.label('name'),
            FunctionBlockV1.type.label('type'),
            FunctionBlockV1.created_time.label('created_time'),
            FunctionBlockV1.current_version_id.label('current_version_id'),
            FunctionBlockV1.group_id.label('group_id'),
            FunctionBlockVersionV1.state.label('state'),
            FunctionBlockVersionV1.tag.label('tag'),
            FunctionBlockVersionV1.description.label('description'),
            FunctionBlockVersionV1.source.label('source'),
            FunctionBlockVersionV1.args.label('args')
        ).join(
            FunctionBlockVersionV1, FunctionBlockV1.current_version_id == FunctionBlockVersionV1.id
        ).filter(
                and_(
                    FunctionBlockV1.id.in_(fb_id_list),
                    FunctionBlockV1.occasion == occasion,
                    or_(
                        FunctionBlockV1.name.contains(search_key),
                        FunctionBlockV1.alt_name.contains(search_key),
                    )
                )
        )
        query = query.offset(offset).limit(limit)
        return query.all()

    def get_function_blocks_with_keyname(self, keyname, user_id):
        user_relations: List[FunctionBlockUserRelation] = FunctionBlockUserRelation.query.filter(
            FunctionBlockUserRelation.user_id.in_([user_id, SpecialUserId.PUBLIC.value])
        ).all()
        fb_id_list = [user_relation.function_block_id for user_relation in user_relations]

        # Define priority
        priority_case = case(
            (FunctionBlockV1.name.contains(keyname), 3),          # Highest priority if fb name contains keyname
            (FunctionBlockV1.alt_name.contains(keyname), 2),        # Next priority if alt_name contains keyname
            (FunctionBlockVersionV1.description.contains(keyname), 1),  # Next priority if description contains keyname
            (FunctionBlockVersionV1.source.contains(keyname), 0),       # Next priority if source contains keyname
            else_=-1  # Priority is -1 if not found
        ).label('priority')

        # Define the subquery
        subquery = db.session.query(
            FunctionBlockV1.id.label('function_block_id'),
            FunctionBlockV1.name.label('function_block_name'),
            FunctionBlockV1.alt_name.label('function_block_alt_name'),
            FunctionBlockVersionV1.description.label('current_version_description'),
            FunctionBlockVersionV1.source.label('current_version_source'),
            priority_case
        ).outerjoin(
            FunctionBlockVersionV1, FunctionBlockV1.current_version_id == FunctionBlockVersionV1.id
        ).subquery()

        # Final query with WHERE and ORDER BY
        final_query = db.session.query(subquery).filter(
        and_(
            subquery.c.priority != -1,
            subquery.c.function_block_id.in_(fb_id_list)
        )
        ).order_by(
            subquery.c.priority.desc()
        )

        return final_query.all()

    def insert_new_version(self, function_block_version: FunctionBlockVersionV1) -> FunctionBlockVersionV1:
        db.session.add(function_block_version)
        db.session.flush()
        return function_block_version
    
    def find_is_collected(self, user_id, function_block_id) -> bool:
        return FunctionBlockCollected.query.filter(
            FunctionBlockCollected.user_id == user_id,
            FunctionBlockCollected.function_block_id == function_block_id
        ).first() is not None
    
    def find_collected_minitools_by_user_id(self, user_id, offset, limit, search_key) -> List:
        return alchemy_db.session.query(
            FunctionBlockV1.id.label('id'),
            FunctionBlockV1.name.label('name'),
            FunctionBlockV1.type.label('type'),
            FunctionBlockV1.created_time.label('created_time'),
            FunctionBlockV1.current_version_id.label('current_version_id'),
            FunctionBlockV1.group_id.label('group_id'),
            FunctionBlockVersionV1.state.label('state'),
            FunctionBlockVersionV1.tag.label('tag'),
            FunctionBlockVersionV1.description.label('description'),
            FunctionBlockVersionV1.source.label('source'),
            FunctionBlockVersionV1.args.label('args'),
            FunctionBlockCollected.created_time.label('collected_time')
        ).join(
            FunctionBlockVersionV1, FunctionBlockV1.current_version_id == FunctionBlockVersionV1.id
        ).join(
            FunctionBlockCollected, and_(
                FunctionBlockV1.id == FunctionBlockCollected.function_block_id,
                FunctionBlockCollected.user_id == user_id
            )
        ).filter(
            and_(
                or_(
                    FunctionBlockV1.name.contains(search_key),
                    FunctionBlockV1.alt_name.contains(search_key),
                ),
                FunctionBlockV1.occasion == FBOccasion.MINI_TOOL.value
            )
        ).offset(offset).limit(limit).all()
    
    def find_list_collected(self, user_id, function_block_id_list) -> List[FunctionBlockCollected]:
        return FunctionBlockCollected.query.filter(
            and_(
                FunctionBlockCollected.user_id == user_id,
                FunctionBlockCollected.function_block_id.in_(function_block_id_list)
            )
        ).all()

    def insert_collected(self, function_block_collected: FunctionBlockCollected) -> FunctionBlockCollected:
        db.session.add(function_block_collected)
        db.session.flush()
        return function_block_collected
    
    def delete_collected(self, user_id, function_block_id) -> None:
        FunctionBlockCollected.query.filter(
            and_(
                FunctionBlockCollected.user_id == user_id,
                FunctionBlockCollected.function_block_id == function_block_id
            )
        ).delete()


function_block_v1_dao = FunctionBlockV1Dao()

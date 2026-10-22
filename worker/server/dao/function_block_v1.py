from model.function_block_v1 import FunctionBlockV1
from model.function_block_version_v1 import FunctionBlockVersionV1
from model.function_block_user_relation import FunctionBlockUserRelation
from typing import List
from db import alchemy_db
from datetime import datetime
from sqlalchemy import text

class FunctionBlockV1Dao:
    def insert(self, function_block_v1: FunctionBlockV1) -> FunctionBlockV1:
        alchemy_db.session.add(function_block_v1)
        alchemy_db.session.flush()
        return function_block_v1
    
    def find_by_user_id(self, user_id) -> List[FunctionBlockV1]:
        user_relations = FunctionBlockUserRelation.query.filter(
            FunctionBlockUserRelation.user_id == user_id
        ).all()
        fb_ids = [relation.function_block_id for relation in user_relations]
        return FunctionBlockV1.query.filter(
            FunctionBlockV1.id.in_(fb_ids)
        ).all()

    def find_versions_by_user_id_and_created_time(self, user_id, start_datetime=None, end_datetime=None) -> List[dict]:
        """
        Find function block versions of the given user within the given time range
        
        :param user_id: user ID
        :param start_datetime: start time, either a datetime object or a string
        :param end_datetime: end time, either a datetime object or a string
        :return: list of versions (as dicts)
        """
        if start_datetime is None:
            start_datetime = '1970-01-01 00:00:00'
        elif isinstance(start_datetime, datetime):
            start_datetime = start_datetime.strftime('%Y-%m-%d %H:%M:%S')
            
        if end_datetime is None:
            end_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(end_datetime, datetime):
            end_datetime = end_datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        # Query the user's function blocks
        user_relations = FunctionBlockUserRelation.query.filter(
            FunctionBlockUserRelation.user_id == user_id
        ).all()
        fb_ids = [relation.function_block_id for relation in user_relations]
        
        # If there are no function blocks, return an empty list
        if not fb_ids:
            return []
        
        # Build placeholders for the IN clause
        placeholders = ','.join([f':fb_id_{i}' for i in range(len(fb_ids))])
        
        # SQLAlchemy 2.0+ requires wrapping raw SQL in text()
        sql = text(f"""
        SELECT fbv.*, fb.name AS function_block_name
        FROM function_block_version_v1 fbv
        JOIN function_block_v1 fb ON fbv.function_block_id = fb.id
        WHERE fb.id IN ({placeholders})
        AND fbv.created_time >= :start_datetime
        AND fbv.created_time <= :end_datetime
        ORDER BY fbv.created_time ASC
        """)
        
        # Build the parameter dict
        params = {
            'start_datetime': start_datetime,
            'end_datetime': end_datetime
        }
        for i, fb_id in enumerate(fb_ids):
            params[f'fb_id_{i}'] = fb_id
        
        # Execute the query
        result = alchemy_db.session.execute(sql, params)
        return [dict(row._mapping) for row in result]

    def find_by_id(self, id) -> FunctionBlockV1:
        return FunctionBlockV1.query.filter(
            FunctionBlockV1.id == id
        ).first()

    def find_fb_version_by_id(self, id) -> FunctionBlockVersionV1:
        return FunctionBlockVersionV1.query.filter(
            FunctionBlockVersionV1.id == id
        ).first()

    def find_version_by_version_id_list(self, version_id_list) -> List[FunctionBlockVersionV1]:
        return FunctionBlockVersionV1.query.filter(
            FunctionBlockVersionV1.id.in_(version_id_list)
        ).all()

    def find_by_group_id(self, group_id) -> List[FunctionBlockV1]:
        return FunctionBlockV1.query.filter(
            FunctionBlockV1.group_id == group_id
        ).all()


function_block_v1_dao = FunctionBlockV1Dao()

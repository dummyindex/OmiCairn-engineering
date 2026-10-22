from db import alchemy_db as db
from model.param_file import ParamFile
from typing import List
from sqlalchemy import and_

class ParamFileDao:

    def insert(self, param_file: ParamFile) -> None:
        db.session.add(param_file)
        db.session.flush()

    def find_by_uuid(self, uuid) -> ParamFile:
        return ParamFile.query.filter(
            ParamFile.uuid == uuid
        ).first()
    
    def find_by_user_id(self, user_id, limit, offset, search_key: str) -> List[ParamFile]:
        if search_key == "" or search_key is None:
            return ParamFile.query.filter(
                ParamFile.user_id == user_id
            ).limit(limit).offset(offset).all()
        
        return ParamFile.query.filter(
            and_(
                ParamFile.user_id == user_id,
                ParamFile.name.like(f"%{search_key}%")
            )
        ).limit(limit).offset(offset).all()
    
    def find_by_suffixes(self, suffixes: List[str], user_id) -> List[ParamFile]:
        return ParamFile.query.filter(
            and_(
                ParamFile.user_id == user_id,
                ParamFile.suffix.in_(suffixes)
            )
        ).all()
    
    def delete_by_uuid(self, uuid) -> None:
        ParamFile.query.filter(
            ParamFile.uuid == uuid
        ).delete()

    def update_by_uuid(self, uuid, updated_attrs) -> None:
        ParamFile.query.filter(
            ParamFile.uuid == uuid
        ).update(updated_attrs)

param_file_dao = ParamFileDao()
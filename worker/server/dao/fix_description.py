from model.fix_description import FixDescription
from db import alchemy_db
from sqlalchemy import and_, or_
from typing import List


class FixDescriptionDao:
    def find_fix_descriptions_after_timestamp(self, timestamp) -> List[FixDescription]:
        return FixDescription.query.filter(FixDescription.created_at > timestamp).all()
    
fix_description_dao = FixDescriptionDao()
from db import alchemy_db
from typing import List
from model.thirty_part_data_source import ThirtyPartDataSource

class ThirtyPartDataSourceDao:
    def find_by_id(self, id):
        return ThirtyPartDataSource.query.filter(ThirtyPartDataSource.id == id).first()
    
    def find_page(self, page, page_size, search=None, sort=None, order=None) -> List[ThirtyPartDataSource]:
        query = ThirtyPartDataSource.query
        if search:
            query = query.filter(ThirtyPartDataSource.name.ilike(f'%{search}%'))
        if sort:
            query = query.order_by(getattr(ThirtyPartDataSource, sort).asc() if order == 'asc' else getattr(ThirtyPartDataSource, sort).desc())
        return query.paginate(page=page, per_page=page_size, error_out=False).items
    
    def find_total_count(self, search=None):
        query = ThirtyPartDataSource.query
        if search:
            query = query.filter(ThirtyPartDataSource.name.ilike(f'%{search}%'))
        return query.count()
    
thirty_part_data_source_dao = ThirtyPartDataSourceDao()
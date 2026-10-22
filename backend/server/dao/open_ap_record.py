from model.open_ap_record import OpenApRecord

from db import alchemy_db as db

class OpenApRecordDao:
    def insert(self, open_ap_record: OpenApRecord):
        db.session.add(open_ap_record)
        db.session.flush()
        return open_ap_record

    def find_by_user_id(self, user_id):
        return OpenApRecord.query.filter(OpenApRecord.user_id == user_id).all()
    
    def find_by_user_id_and_time(self, user_id, start_time, end_time):
        return OpenApRecord.query.filter(OpenApRecord.user_id == user_id, OpenApRecord.open_time >= start_time, OpenApRecord.open_time <= end_time).all()
    
    def find_ones_latest_record_by_user_id(self, user_id, analysis_id_list):
        '''
            select user_id, analysis_id, max(open_time) as open_time from open_ap_record 
            where user_id = user_id and analysis_id in (analysis_id_list)
            GROUP BY user_id, analysis_id
            ORDER BY open_time DESC;
        '''
        return db.session.query(OpenApRecord.user_id, OpenApRecord.analysis_id, db.func.max(OpenApRecord.open_time).label('open_time')).filter(OpenApRecord.user_id == user_id, OpenApRecord.analysis_id.in_(analysis_id_list)).group_by(OpenApRecord.user_id, OpenApRecord.analysis_id).order_by(db.desc('open_time')).all()

open_ap_record_dao = OpenApRecordDao()
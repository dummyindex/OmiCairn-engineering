from dao.open_ap_record import open_ap_record_dao
from model.open_ap_record import OpenApRecord


class BurialPointService:
    """Records when a user opens an analysis; used for the "recently opened analyses" list.

    No IP addresses, page visits or login events are recorded.
    """

    def record_open_ap(self, user_id, analysis_id, open_time):
        open_ap_record = OpenApRecord(
            user_id=user_id,
            analysis_id=analysis_id,
            open_time=open_time
        )
        open_ap_record_dao.insert(open_ap_record)
        return open_ap_record

burial_point_service = BurialPointService()

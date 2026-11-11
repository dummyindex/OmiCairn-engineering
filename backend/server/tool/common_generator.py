import uuid
from datetime import datetime, timedelta

DEFAULT_PERIOD = timedelta(days=30)

class CommonGenerator:

    @staticmethod
    def generate_uuid(double=False):
        if double:
            return uuid.uuid4().hex + uuid.uuid4().hex
        return uuid.uuid4().hex
    
    @staticmethod
    def camel_to_snake(camel_str: str):
        return ''.join(['_' + i.lower() if i.isupper() else i for i in camel_str]).lstrip('_')

    @staticmethod
    def generate_current_period(last_period_end_time: datetime, current_time: datetime, period: timedelta = DEFAULT_PERIOD):
        distance = current_time - last_period_end_time
        period_count = int(distance / period)
        start_time = last_period_end_time + period * period_count
        end_time = start_time + period
        return start_time, end_time

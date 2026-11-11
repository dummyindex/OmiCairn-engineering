from db import Base
import json


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Base):
            return obj.to_dict()
        return super().default(obj)

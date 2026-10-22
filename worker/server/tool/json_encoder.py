import json
import numpy as np
from db import alchemy_db as db
from datetime import datetime
from flask.json.provider import DefaultJSONProvider

from sqlalchemy.engine import BaseRow


class StrictJSONProvider(DefaultJSONProvider):
    """
    Custom JSON encoder set-up performing two tasks:
    1. Strict JSON conformance with non-finite floats
    (NaN, +/-Inf) via allow_nan=False
    2. Convert various Numpy types into python
    types so the encoder will correctly encode.
    """

    def _underscore_to_camelcase(self, underscore_str):
        words = underscore_str.split('_')
        camelcase_str = words[0] + \
            ''.join(word.capitalize() for word in words[1:])
        return camelcase_str

    def default(self, obj):
        """This helps us convert types not
        supported by the native JSON encoder into
        standard python types, eg, np.int64."""
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, db.Model):
            return obj.to_dict()
        elif isinstance(obj, BaseRow):
            return {
                self._underscore_to_camelcase(obj._fields[i]): obj[i]
                for i in range(len(obj._fields))
            }
        elif isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return super().default(obj)

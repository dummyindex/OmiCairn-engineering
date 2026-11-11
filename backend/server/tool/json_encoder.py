import json
import numpy as np
from db import alchemy_db as db
from dto import Dto
from datetime import datetime
from sqlalchemy.engine import BaseRow

class StrictJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder set-up performing two tasks:
    1. Strict JSON conformance with non-finite floats
    (NaN, +/-Inf) via allow_nan=False
    2. Convert various Numpy types into python
    types so the encoder will correctly encode.
    """

    def __init__(self, *args, **kwargs):
        """
        NaN/Infinities are illegal in standard JSON.
        Python extends JSON with non-standard symbols that
        most JavaScript JSON parsers do not understand.
        The `allow_nan` parameter will force Python simplejson
        to throw an ValueError if it runs into non-finite
        floating point values which are unsupported by
        standard JSON.
        """
        kwargs["allow_nan"] = False
        super().__init__(*args, **kwargs)

    def _underscore_to_camelcase(self, underscore_str):
        words = underscore_str.split('_')
        camelcase_str = words[0] + ''.join(word.capitalize() for word in words[1:])
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
        elif isinstance(obj, Dto):
            return obj.to_dict()
        elif isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return super(StrictJSONEncoder, self).default(obj)

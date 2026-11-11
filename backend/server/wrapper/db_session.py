from functools import wraps
from db import alchemy_db


def transaction_wrapper(func):
    @wraps(func)
    def wrapped_function(self):
        try:
            func_result = func(self)
            alchemy_db.session.commit()
            return func_result
        except Exception as e:
            alchemy_db.session.rollback()
            raise e
    return wrapped_function

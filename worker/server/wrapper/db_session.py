from functools import wraps
from db import alchemy_db
from sqlalchemy.exc import OperationalError
import time
from log.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger('TransactionWrapper')


def transaction_wrapper(func):
    @wraps(func)
    def wrapped_function(self):
        max_retries = 3  # maximum number of retries
        for attempt in range(max_retries):
            try:
                func_result = func(self)
                alchemy_db.session.commit()
                return func_result
            except OperationalError as e:
                alchemy_db.session.rollback()
                # Check whether this is a deadlock error (MySQL error code 1213)
                error_msg = str(e)
                is_deadlock = '1213' in error_msg or 'Deadlock' in error_msg

                if is_deadlock and attempt < max_retries - 1:
                    # Exponential backoff: wait 0.1s before the 1st retry, 0.2s before the 2nd
                    wait_time = 0.1 * (attempt + 1)
                    logger.warning(
                        f"Deadlock detected (attempt {attempt + 1}/{max_retries}), "
                        f"retrying after {wait_time}s... Error: {error_msg}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    # Not a deadlock error, or the maximum number of retries was reached
                    if is_deadlock:
                        logger.error(
                            f"Deadlock still occurs after {max_retries} retries, "
                            f"giving up. Error: {error_msg}"
                        )
                    raise e
            except Exception as e:
                alchemy_db.session.rollback()
                raise e
    return wrapped_function

import traceback
from functools import wraps
from tool.response_manager import ResponseManager
from log.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("exception")


def exception_wrapper(func):
    @wraps(func)
    def wrapped_function(self):
        try:
            return func(self)
        except Exception as e:
            logger.error(traceback.format_exc())
            return ResponseManager.new_server_error_response(str(e))
    return wrapped_function

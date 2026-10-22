import logging
import os
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper(),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class LoggerFactory:
    @staticmethod
    def get_logger(name):
        logger = logging.getLogger(name)
        return logger

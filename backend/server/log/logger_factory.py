import logging
import os
logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="[%(name)s] %(asctime)s %(process)d:%(processName)s- %(levelname)s ===> %(message)s"
)


class LoggerFactory:
    def create_logger(self, name):
        logger = logging.getLogger(name)
        return logger


logger_factory = LoggerFactory()

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(name)s] %(asctime)s %(process)d:%(processName)s- %(levelname)s ===> %(message)s"
)


class LoggerFactory:
    def create_logger(self, name):
        logger = logging.getLogger(name)
        return logger


logger_factory = LoggerFactory()

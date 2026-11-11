import logging


class LoggerFactory:
    @staticmethod
    def get_logger(name, level=logging.INFO):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        return logger


logger_factory = LoggerFactory()

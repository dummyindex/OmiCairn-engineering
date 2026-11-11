import logging
import boto3
boto3.set_stream_logger('boto3.resources', logging.INFO)
boto3.set_stream_logger('boto3', logging.INFO)
boto3.set_stream_logger('botocore', logging.INFO)
boto3.set_stream_logger('s3transfer', logging.INFO)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class LoggerFactory:
    @staticmethod
    def get_logger(name):
        logger = logging.getLogger(name)
        return logger

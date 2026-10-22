from datetime import datetime
import os
import boto3
class AWSCloudwatchLogsTaker:

    def __init__(self, group_name, log_stream_name) -> None:
        self.boto3_client = boto3.client('logs')
        self.group_name = group_name or os.environ.get("AWS_BATCH_LOG_GROUP", "/aws/batch/job")
        self.log_stream_name = log_stream_name

    def get(self):
        log_events = self.boto3_client.get_log_events(
            logGroupName=self.group_name,
            logStreamName=self.log_stream_name,
            startFromHead=True
        )

        return log_events['events'] if 'events' in log_events else []

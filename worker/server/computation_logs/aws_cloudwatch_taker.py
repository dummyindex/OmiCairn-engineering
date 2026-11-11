from datetime import datetime
import boto3
from log.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("AWSCloudwatchLogsTaker")


class AWSCloudwatchLogsTaker:

    def __init__(self, group_name, log_stream_name) -> None:
        self.boto3_client = boto3.client('logs')
        self.group_name = group_name
        self.log_stream_name = log_stream_name

    def get(self):

        kwargs = {
            'logGroupName': '/aws/batch/job',
            'logStreamName': self.log_stream_name,
            'startFromHead': True
        }

        all_events = []
        next_token = None

        while True:
            if next_token:
                kwargs['nextToken'] = next_token

            response = self.boto3_client.get_log_events(**kwargs)

            events = response.get('events', [])
            all_events.extend(events)

            # Save the previous token
            prev_token = next_token
            # Get the new token
            next_token = response.get('nextForwardToken')

            # If the old and new tokens are the same, all events have been fetched
            if prev_token == next_token:
                break

        return all_events

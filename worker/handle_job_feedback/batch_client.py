import boto3


class BatchClientFactory:

    @staticmethod
    def create_batch_client():
        return boto3.client("batch")


batch_client_factory = BatchClientFactory()

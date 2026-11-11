import boto3

class AWSBatchJob:

    @staticmethod
    def describe_job(job_id):
        batch_client = boto3.client('batch')
        response = batch_client.describe_jobs(jobs=[job_id])
        if 'jobs' in response and response['jobs']:
            return response['jobs'][0]
        return None
    
    @staticmethod
    def describe_jobs(job_ids):
        batch_client = boto3.client('batch')
        response = batch_client.describe_jobs(jobs=job_ids)
        if 'jobs' in response and response['jobs']:
            return response['jobs']
        return None
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

    @staticmethod
    def query_job_by_name(job_name, queue_name):
        batch_client = boto3.client('batch')
        response = batch_client.list_jobs(
            jobQueue=queue_name,
            filters=[{
                "name": "JOB_NAME",
                "values":[job_name]
            }]
        )
        if 'jobSummaryList' in response and response['jobSummaryList']:
            return response['jobSummaryList']
        return []

    @staticmethod
    def stop_job_by_name(job_name, queue_name):
        job_list = AWSBatchJob.query_job_by_name(job_name, queue_name)
        if not job_list or len(job_list) == 0:
            return
        job_ids = [job['jobId'] for job in job_list]
        batch_client = boto3.client('batch')
        batch_client.terminate_job(
            jobId=job_ids[0],
            reason='Job stopped by user'
        )
import os
import logging
import json
import boto3
import uuid
from botocore.config import Config

logger = logging.getLogger("aws_resource")


def get_parameter_from_parameter_store(parameter_name):
    """
    get sensitive data from AWS System Manager
    :param parameter_name:
    :return:
    """
    ssm = boto3.client("ssm")
    parameter = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    return parameter['Parameter']['Value']


def put_job_status(job, message, succeed=True):
    code_pipeline = boto3.client('codepipeline')
    logger.info(message)
    if succeed:
        logger.info('Putting job success')
        code_pipeline.put_job_success_result(jobId=job)
    else:
        logger.info('Putting job failure')
        code_pipeline.put_job_failure_result(jobId=job, failureDetails={'message': message, 'type': 'JobFailed'})


def find_artifact(artifacts, name):
    for artifact in artifacts:
        if artifact['name'] == name:
            return artifact

    raise Exception('Input artifact named "{0}" not found in event'.format(name))


def get_artifact(s3, artifact):
    bucket = artifact['location']['s3Location']['bucketName']
    key = artifact['location']['s3Location']['objectKey']
    logger.info("Artifact = " + bucket + key)
    filename = "/tmp/cx-" + str(uuid.uuid4()) + ".zip"
    s3.download_file(bucket, key, filename)
    return filename


def setup_s3_client(job_data):
    key_id = job_data['artifactCredentials']['accessKeyId']
    key_secret = job_data['artifactCredentials']['secretAccessKey']
    session_token = job_data['artifactCredentials']['sessionToken']

    session = boto3.Session(
        aws_access_key_id=key_id,
        aws_secret_access_key=key_secret,
        aws_session_token=session_token
    )
    return session.client('s3', config=Config(signature_version='s3v4'))


def get_user_params(job_data):
    try:
        # Get the user parameters which contain the stack, artifact and file settings
        user_parameters = job_data['actionConfiguration']['configuration']['UserParameters']
        decoded_parameters = json.loads(user_parameters)

    except Exception as e:
        # We're expecting the user parameters to be encoded as JSON
        # so we can pass multiple values. If the JSON can't be decoded
        # then fail the job with a helpful message.
        raise Exception('UserParameters could not be decoded as JSON')

    return decoded_parameters


def update_os_environment_variables():
    """
    update environment variable, so Checkmarx Python SDK could pick these value.
    :return:
    """
    logger.info("Start update_os_environment_variables")
    cxone_access_control_url = get_parameter_from_parameter_store("/Checkmarx/CxOneIamURL")
    cxone_server = get_parameter_from_parameter_store("/Checkmarx/CxOneServerURL")
    cxone_tenant_name = get_parameter_from_parameter_store("/Checkmarx/CxOneTenantName")
    cxone_refresh_token = get_parameter_from_parameter_store("/Checkmarx/CxOneAPIKey")
    pivotal_tracker_token = get_parameter_from_parameter_store("/PivotalTracker/Token")

    os.environ["cxone_access_control_url"] = cxone_access_control_url
    os.environ["cxone_server"] = cxone_server
    os.environ["cxone_tenant_name"] = cxone_tenant_name
    os.environ["cxone_grant_type"] = "refresh_token"
    os.environ["cxone_refresh_token"] = cxone_refresh_token
    os.environ["pivotal_tracker_token"] = pivotal_tracker_token
    logger.info("Finish update_os_environment_variables")


def get_code_pipeline_project_and_zip_file_path(job_data):
    logger.info("start get_code_pipeline_project_and_zip_file_path")
    source_artifact = "SourceArtifact"
    build_artifact = "BuildArtifact"
    params = get_user_params(job_data)
    input_type = source_artifact
    project_name = None
    if 'project' in params:
        project_name = params['project']
    else:
        raise Exception("project must be provided")
    if 'source' in params and params['source'] == "build":
        input_type = build_artifact

    artifacts = job_data['inputArtifacts']
    artifact_data = find_artifact(artifacts, input_type)
    s3 = setup_s3_client(job_data)
    zip_file_path = get_artifact(s3, artifact_data)
    logger.info("finish get_code_pipeline_project_and_zip_file_path")
    return project_name, zip_file_path

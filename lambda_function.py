"""

This script will be run in AWS Lambda.

"""

import logging
import traceback
from utilities.aws_resources import (
    update_os_environment_variables,
    get_code_pipeline_project_and_zip_file_path,
    put_job_status,
)
from utilities.pivotal_tracker import (
    create_pivotal_stories
)
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning


root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)
logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

disable_warnings(InsecureRequestWarning)


def execute_job(project_name, zip_file_path):
    update_os_environment_variables()
    logger.info(f"project_name: {project_name}")
    logger.info(f"zip_file_path: {zip_file_path}")
    from utilities.cxone import execute_cx_one_scan
    scan_results = execute_cx_one_scan(project_name=project_name, zip_file_path=zip_file_path)
    stories = create_pivotal_stories(scan_results, project_name)
    for story in stories:
        story_name = story.get("name")
        logger.info(f"story name: {story_name}")


def lambda_handler(event, context):
    logger.info("Lambda function start")
    job_id = event['CodePipeline.job']['id']
    job_data = event['CodePipeline.job']['data']
    try:
        project_name, zip_file_path = get_code_pipeline_project_and_zip_file_path(job_data)
        execute_job(project_name, zip_file_path)
        put_job_status(job_id, "done")
    except Exception as e:
        logger.info('Function failed due to exception.')
        logger.info(f"Exception: {e}")
        traceback.print_exc()
        put_job_status(job_id, 'Function exception: ' + str(e), succeed=False)

    logger.info('Lambda function complete.')
    return "Complete."


if __name__ == '__main__':
    project_name = "bodgeit"
    zip_file_path = "/home/happy/Downloads/bodgeit-master.zip"
    execute_job(project_name, zip_file_path)

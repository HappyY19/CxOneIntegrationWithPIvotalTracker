import os
import logging
import time
from CheckmarxPythonSDK.CxOne import (
    get_a_list_of_projects,
    create_a_project,
    create_a_pre_signed_url_to_upload_files,
    upload_zip_content_for_scanning,
)
from CheckmarxPythonSDK.CxOne.scansAPI import (
    create_scan,
    ScanInput,
    get_a_scan_by_id,
)
from CheckmarxPythonSDK.CxOne.dto import (
    ProjectInput,
    Project,
    Upload,
    ScanConfig,
)

from CheckmarxPythonSDK.CxOne.sastResultsAPI import (
    get_sast_results_by_scan_id,
)

logger = logging.getLogger("CxOne")


def create_project_if_not_exist(p_input: ProjectInput):
    logger.info("Start create_project_if_not_exist")
    project_name = p_input.name
    project_collection = get_a_list_of_projects(name=project_name)
    if project_collection.totalCount == 0:
        logger.info(f"CxOne project with name: {project_name} does not exist, start creating this project")
        result = create_a_project(project_input=p_input)
        logger.info(f"Finish create CxOne project with name {project_name}")
    else:
        logger.info(f"The project with name {project_name} exists in the system")
        result = project_collection.projects[0]
    logger.info("Finish create_project_if_not_exist")
    return result


def execute_cx_one_scan(project_name, zip_file_path):
    """

    Create a CxOne project (same name as the AWS CodePipeline) if the project not exist, otherwise use the existing one.
    Create a scan under the CxOne project.
    Wait for the scan to be finished.

    return scan results
    :param project_name:
    :param zip_file_path:
    :return:
    """
    logger.info("Start execute_cx_one_scan")
    tags = {
        "test": "test",
        "demo": "true"
    }
    project_input = ProjectInput(
        name=project_name,  origin="API", tags=tags, criticality=3
    )
    project = create_project_if_not_exist(p_input=project_input)

    upload_url = create_a_pre_signed_url_to_upload_files()
    logger.info("create the upload link in order to upload files to CxOne")
    is_successful = upload_zip_content_for_scanning(
        upload_link=upload_url,
        zip_file_path=zip_file_path
    )
    if not is_successful:
        logger.info("Failed to upload source code zip file to CxOne")
        return None
    logger.info("Successfully upload source code zip file to CxOne")
    scan_input = ScanInput(
        scan_type="upload",
        handler=Upload(upload_url=upload_url),
        project=Project(project_id=project.id, tags={"test": "", "priority": "high"}),
        configs=[
            ScanConfig("sast", {"incremental": "false", "presetName": "ASA Premium"}),
            ScanConfig("sca"),
            ScanConfig("kics"),
        ],
        tags={
            "test": "",
            "scan_tag": "toyota motor"
        }
    )
    logger.info("Start to scan")
    scan = create_scan(scan_input=scan_input)
    scan_id = scan.id

    logger.info(f"CxOne scan id: {scan_id}")
    scan = get_a_scan_by_id(scan_id)
    scan_status = scan.status
    logger.info(f"scan status: {scan_status}")
    while scan_status not in ("Completed", "Failed", "Canceled"):
        time.sleep(5)
        scan = get_a_scan_by_id(scan_id)
        scan_status = scan.status
        logger.info(f"scan status: {scan_status}")
    logger.info("Start get sast scan results")
    sast_scan_results = get_sast_results_by_scan_id(scan_id)
    logger.info("Finish get sast scan results")
    logger.info("Finish execute_cx_one_scan")
    return {"sast_scan_results": sast_scan_results}

# encoding: utf-8
"""
Create a Pivotal Tracker project if not exist, otherwise use the existing one.
Create a story under the Pivotal Tracker project.
"""
import os
import requests
import json
import logging

logger = logging.getLogger("pivotal_tracker")

base_url = "https://www.pivotaltracker.com/services/v5/"


def get_header():
    return {
        "X-TrackerToken": os.getenv("pivotal_tracker_token"),
        "Content-Type": "application/json"
    }


def get_projects():
    result = []
    url = base_url + "projects/"
    response = requests.get(url, headers=get_header())
    if response.status_code == requests.codes.OK:
        result = response.json()
    return result


def get_project_by_name(name):
    result = None
    project_list = get_projects()
    if project_list:
        for p in project_list:
            if p.get('name') == name:
                result = p
                break
    return result


def create_project(project_name):
    result = None
    url = base_url + "projects/"
    response = requests.post(url, data=json.dumps({"name": project_name}), headers=get_header())
    if response.status_code == requests.codes.OK:
        result = response.json()
    return result


def get_stories(project_id):
    result = []
    url = base_url + f"/projects/{project_id}/stories"
    response = requests.get(url, headers=get_header())
    if response.status_code == requests.codes.OK:
        result = response.json()
    return result


def create_story(project_id, story_content):
    """

    :param project_id:
    :type (int)
    :param story_content:
    :type (str)
    :return:
    """
    result = None
    url = base_url + f"/projects/{project_id}/stories"
    response = requests.post(url, data=json.dumps(story_content), headers=get_header())
    if response.status_code == requests.codes.OK:
        result = response.json()
    return result


def create_project_if_not_exist(project_name):
    project = get_project_by_name(project_name)
    if not project:
        project = create_project(project_name)
    return project


def create_pivotal_stories(scan_results, project_name):
    pivotal_tracker_project = create_project_if_not_exist(project_name)
    pivotal_tracker_project_id = pivotal_tracker_project.get("id")
    existing_stories = get_stories(pivotal_tracker_project_id)
    existing_story_name_similarity_ids = [item.get("name").split(" ")[-1] for item in existing_stories]
    sast_results_response = scan_results.get("sast_scan_results")
    sast_results_total_count = sast_results_response.get('totalCount')
    if sast_results_total_count == 0:
        return []
    new_stories = []
    scan_results = sast_results_response.get('results')
    for result in scan_results:
        if str(result.similarityID) in existing_story_name_similarity_ids:
            logger.info(f"story with similarity ID {result.similarityID} already exist")
            continue
        name = f"{result.group} {result.queryName} {result.similarityID}"
        start_node = result.nodes[0]
        end_node = result.nodes[-1]
        description = (f"severity: {result.severity}\n"
                       f"state: {result.state}\n"
                       f"status: {result.status}\n"
                       f"cweID: {result.cweID}\n"
                       f"firstFoundAt: {result.firstFoundAt}\n"
                       f"firstScanID: {result.firstScanID}\n"
                       f"foundAt: {result.foundAt}\n"
                       f"start node: fileName: {start_node.fileName}, line: {start_node.line} "
                       f"column: {start_node.column} name: {start_node.name}, "
                       f"fullName: {start_node.fullName}, domType: {start_node.domType}, "
                       f"method: {start_node.method}, methodLine: {start_node.methodLine},"
                       f"length: {start_node.length}\n"
                       f"end node: fileName: {end_node.fileName}, line: {end_node.line} "
                       f"column: {end_node.column} name: {end_node.name}, "
                       f"fullName: {end_node.fullName}, domType: {end_node.domType}, "
                       f"method: {end_node.method}, methodLine: {end_node.methodLine},"
                       f"length: {end_node.length}")
        content = {
            "name": name,
            "current_state": "started",
            "story_type": "bug",
            "description": description

        }
        story = create_story(project_id=pivotal_tracker_project_id, story_content=content)
        new_stories.append(story)
    return new_stories

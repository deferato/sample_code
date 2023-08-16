import json
import os

import requests


OCTOPUS_API_URL = "https://octopus.com"
session = requests.Session()
session.headers.update({
    'X-Octopus-ApiKey': os.environ['OCTOPUS_API_KEY'],
    'Accept': 'application/json'
})

PROJECT_GROUPS = {
    '63': 'Self Service Projects',
    '241': 'Project - API',
    '106': 'Project - SQL',
    '21': 'Sandbox Projects'
}

def get_step_template_list():

    get_url = OCTOPUS_API_URL + "/api/Spaces-1/actiontemplates/All"
    get_return = session.get(get_url).content
    return json.loads(get_return)


def get_template_usage(usage_url):

    get_url = OCTOPUS_API_URL + usage_url
    get_return = session.get(get_url).content
    return json.loads(get_return)


def get_projects(project_groups_list=PROJECT_GROUPS):
    """Retrieves a JSON collection of projects for a given set of project groups."""

    result = { "Items": [] }
    for key, value in project_groups_list.items():
        print("Key: {} Value: {}".format(key,value))
        project_group = {
            "project_group_id": key,
            "project_group_name": value,
            "projects": []
        }

        full_project_url = (
            OCTOPUS_API_URL
            + "/api/projectgroups"
            + "/ProjectGroups-"
            + key
            + "/projects"
        )
        print("Full Project Url: {}".format(full_project_url))

        response = session.get(url=full_project_url)

        if not response.ok:
            response.raise_for_status()

        data = json.loads(response.content)
        items = data["Items"]
        print("Item Count: {}".format(len(items)))

        if len(items) == 0:
            continue

        for item in items:
            print("Project Info: {} - {}".format(item['Id'], item['Name']))
            project_group['projects'].append({
                "project_id": item["Id"],
                "project_name": item["Name"],
                "project_slug": item["Slug"],
                "project_api_url": full_project_url,
                "project_url": "https://octopus.com/app#/Spaces-1/projects/{}/overview".format(item["Slug"])
            })

        result['Items'].append(project_group)

    return result


def get_latest_release(project_id, project_slug):
    """Retrieves the latest release for a given project"""

    full_release_url = (
        OCTOPUS_API_URL
        + "/api/projects"
        + "/{}".format(project_id)
        + "/releases"
    )
    print("Full Release Url: {}".format(full_release_url))

    release_response = session.get(url=full_release_url)

    if not release_response.ok:
        release_response.raise_for_status()

    data = json.loads(release_response.content)
    items = data["Items"]

    if len(items) == 0:
        return {}

    return {
        "release_id": items[0]["Id"],
        "assembled": items[0]["Assembled"],
        "version": items[0]["Version"],
        "release_api_url": full_release_url,
        "release_url": "https://octopus.com/app#/Spaces-1/projects/{}/releases/{}".format(project_slug, items[0]["Version"])
    }


def get_release_progression(release):
    """Retrieves release progression status for a given release"""

    full_progression_url = (
        OCTOPUS_API_URL
        + "/api/releases"
        + "/{}".format(release["release_id"])
        + "/progression"
    )

    progression_response = session.get(url=full_progression_url)

    if not progression_response.ok:
        progression_response.raise_for_status()

    data = json.loads(progression_response.content)
    phases = data["Phases"]

    if len(phases) == 0:
        return []

    release_progression = []
    for phase in phases:
        release_progression.append({
            "phase_name": phase["Name"],
            "progress": phase["Progress"]
        })

    return release_progression


def get_project_slug(project_id):
    """Retrieves the Slug for the given project id"""

    url = "https://octopus.com/api/projects/{}".format(project_id)

    response = session.get(url=url)

    if not response.ok:
        response.raise_for_status()

    data = json.loads(response.content)

    return data["Slug"]


def get_project_id(project_slug):
    """Retrieves the ID for the given project slug"""

    url = "https://octopus.com/api/projects/{}".format(project_slug)

    response = session.get(url=url)

    if not response.ok:
        response.raise_for_status()

    data = json.loads(response.content)

    return data["Id"]

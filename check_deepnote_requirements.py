# Uses the deepnote API to update notebooks and Dockerfiles on deepnote, based
# on the contexts of Deepnote.json.
# https://community.deepnote.com/c/beta-testers/notebooks-api-early-access

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests

if len(sys.argv) != 1:
    print("Usage: python3 check_deepnote_requirements.py")
    exit(-1)

# root should be textbook repo root
htmlbook = os.path.dirname(os.path.realpath(__file__))
book = os.path.dirname(htmlbook)
root = os.path.dirname(book)


def get_formatted_version():
    with open(Path(root) / "pyproject.toml") as file:
        for line in file:
            # Look for the line that starts with "version ="
            if line.strip().startswith("version ="):
                # Extract the version number (everything after the "=" and within quotes)
                version = line.split("=", 1)[1].strip().strip('"')
                return version
    return None


deepnote = json.load(open(Path(book) / "Deepnote.json"))
version_from_poetry = get_formatted_version()


def check_manip_sha(chapter, project_id):
    # Note: I (finally) figured this out by opening the deepnote project in a browser,
    # and then turning off wifi before clicking on the download button.
    url = f"https://deepnote.com/api/project/{project_id}/download-file?path=requirements.txt"
    for i in range(3):  # number of retries
        r = requests.get(url)
        if r.status_code == 200:
            break
    if r.status_code != 200:
        print("failed to get requirements.txt")
        print(r.status_code, r.reason, r.text)

    # Regular expression to find the version number after manipulation==
    match = re.search(r"manipulation==(.+)$", r.text)
    if match:
        version = match.group(1)
        if version != version_from_poetry:
            print(
                f"deepnote chapter {chapter} notebook has version {version} in the requirements.txt, but poetry has {version_from_poetry}. Please run the publish_to_deepnote script."
            )
            exit(-1)
    else:
        print("failed to extract manipulation version from requirements.txt")


with open(Path(book) / "Deepnote_workspace.txt") as workspace_file:
    workspace = workspace_file.read()

for chapter, project_id in deepnote.items():
    check_manip_sha(chapter, project_id)

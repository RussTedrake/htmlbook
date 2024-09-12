# Uses the deepnote API to update notebooks and Dockerfiles on deepnote, based
# on the contexts of Deepnote.json.
# https://community.deepnote.com/c/beta-testers/notebooks-api-early-access

import json
import os
import subprocess
import sys
from pathlib import Path

import requests

testing = False
check_deepnote_files = True

if len(sys.argv) < 2:
    print("Usage: python3 htmlbook/publish_to_deepnote.py dockerhub_sha")
    exit(-1)


# root should be textbook repo root
htmlbook = os.path.dirname(os.path.realpath(__file__))
root = os.path.dirname(htmlbook)
repository = os.path.basename(os.path.dirname(root))
os.chdir(root)

dockerhub_sha = sys.argv[1]
Dockerfile = f"FROM russtedrake/{repository}:{dockerhub_sha}"
with open(htmlbook + "/Init.ipynb") as f:
    Init = json.load(f)

def get_formatted_version():
    # Run the 'poetry version' command
    result = subprocess.run(['poetry', 'version'], stdout=subprocess.PIPE, text=True)

    # Extract the output and strip any leading/trailing whitespace
    output = result.stdout.strip()

    # Replace the space with '==' to get the desired format
    formatted_version = output.replace(' ', '==')

    return formatted_version


Requirements = f"""
--extra-index-url https://drake-packages.csail.mit.edu/whl/nightly
{get_formatted_version()}
"""

deepnote = json.load(open("Deepnote.json"))

api_key = os.environ["DEEPNOTE_API_KEY_" + repository.upper()]
headers = {"Authorization": f"Bearer {api_key}"}

# We might push multiple notebooks to the same project, but only need to send
# the dockerfile once.
updated_dockerfiles = []


def update(notebook, project_id, path=""):
    expected_files = set(["Dockerfile", "requirements.txt"])
    expected_notebooks = dict({'Init':0})
    notebook_path = Path(path) / notebook
    notebook = Path(notebook).stem

    # If notebook is a directory, publish all notebooks in that directory
    if notebook_path.is_dir():
        for p in notebook_path.rglob("*.ipynb"):
            f, n = update(p.relative_to(notebook_path), project_id, notebook_path)
            expected_files.update(f)
            expected_notebooks.update(n)
        return expected_files, expected_notebooks
    
    print(f"Updating {notebook_path}...")
    # Update the Dockerfile
    if project_id not in updated_dockerfiles:
        url = f"https://api.deepnote.com/v1/projects/{project_id}/files?path=Dockerfile"
        if testing:
            print(f"would be pushing to {url}")
        else:
            for i in range(3):  # number of retries
                r = requests.put(url, headers=headers, data=Dockerfile)
                if r.status_code == 200:
                    break
            if r.status_code != 200:
                print("failed to update Dockerfile")
                print(r.status_code, r.reason, r.text)

        url = f"https://api.deepnote.com/v1/projects/{project_id}/files?path=requirements.txt"
        if testing:
            print(f"would be pushing to {url}")
        else:
            for i in range(3):  # number of retries
                r = requests.put(url, headers=headers, data=Requirements)
                if r.status_code == 200:
                    break
            if r.status_code != 200:
                print("failed to update requirements.txt")
                print(r.status_code, r.reason, r.text)

        url = (
            f"https://api.deepnote.com/v1/projects/{project_id}/notebooks/import-from-ipynb"
        )
        payload = {"name": "Init", "ipynb": Init}
        if testing:
            print(f"would be pushing to {url}")
        else:
            for i in range(3):  # number of retries
                r = requests.put(url, headers=headers, json=payload)
                if r.status_code == 200:
                    break
            if r.status_code != 200:
                print("failed to update Init notebook")
                print(r.status_code, r.reason, r.text)

        updated_dockerfiles.append(project_id)


    # Update the notebook file(s)
    url = (
        f"https://api.deepnote.com/v1/projects/{project_id}/notebooks/import-from-ipynb"
    )
    with open(notebook_path.with_suffix(".ipynb")) as f:
        contents = json.load(f)
    payload = {"name": notebook, "ipynb": contents}
    if testing:
        print(f"would be pushing to {url}")
    else:
        for i in range(3):  # number of retries
            r = requests.put(url, headers=headers, json=payload)
            if r.status_code == 200:
                break
        if r.status_code != 200:
            print("failed to update notebook")
            r = requests.put(url, headers=headers, json=payload)
            print(r.status_code, r.reason, r.text)
        expected_notebooks[notebook] = json.loads(r.text)["id"]
    return expected_files, expected_notebooks


def check_files(expected_files, expected_notebooks, project_id):
    global check_deepnote_files
    if not check_deepnote_files:
        return
    if testing:
        return

    url = f"https://deepnote.com/workspace/{workspace}/project/{project_id}/"
    try:
        output = subprocess.run(
            ["node", "htmlbook/deepnote_check_notebooks.js", url],
            capture_output=True,
            text=True,
            timeout=60,
        ).stdout.splitlines()
    except:
        print("Failed to run node.js notebook check. Disabling these checks.")
        print("See deepnote_check_notebooks.js for installation instructions.")
        check_deepnote_files = False
        return

    separator = output.index("---")
    notebooks = set(output[:separator])
    expected_notebooks = set(expected_notebooks)
    files = set(output[separator + 1 :])
    expected_files = set(expected_files)

    if not expected_notebooks == notebooks:
        if expected_notebooks - notebooks:
            print(f"Missing notebooks: {expected_notebooks - notebooks}")
        if notebooks - expected_notebooks:
            print(f"Extra notebooks: {notebooks - expected_notebooks}")

    if not expected_files == files:
        if expected_files - files:
            print(f"Missing files: {expected_files - files}")
        if files - expected_files:
            print(f"Extra files: {files - expected_files}")


with open(Path(root) / "Deepnote_workspace.txt") as workspace_file:
    workspace = workspace_file.read()

notebooks = dict()

for chapter, project_id in deepnote.items():
    expected_files, chapter_notebooks = update(chapter, project_id, "")
    check_files(expected_files, chapter_notebooks.keys(), project_id)
    notebooks[chapter] = chapter_notebooks

with open(Path(root) / "chapters.js", "w") as f:
    f.write("chapter_project_ids = ")
    json.dump(deepnote, f, sort_keys=True)
    f.write("\n")
    f.write("notebook_ids = ")
    json.dump(notebooks, f, sort_keys=True)
    f.write("\n")
    f.write(f'deepnote_workspace_id = "{workspace}"')

# Uses the deepnote API to update notebooks and Dockerfiles on deepnote, based
# on the contexts of Deepnote.json.
# https://community.deepnote.com/c/beta-testers/notebooks-api-early-access

import json
import requests
import os
from pathlib import Path
import subprocess
import sys

testing = False
check_deepnote_files = True

if len(sys.argv) < 2:
    print('Usage: python3 htmlbook/publish_to_deepnote.py dockerhub_sha')
    exit(-1)

dockerhub_sha = sys.argv[1]

# root should be textbook repo root
htmlbook = os.path.dirname(os.path.realpath(__file__))
root = os.path.dirname(htmlbook)
repository = os.path.basename(root)

notebooks = json.load(open("Deepnote.json"))

for path in Path(root).rglob('*/Deepnote.json'):
    # Ignore some directories.
    if 'bazel' in str(path):
        continue
    d = path.parent.relative_to(Path(root))
    notebooks[str(d)] = json.load(open(path))

api_key = os.environ['DEEPNOTE_API_KEY_' + repository.upper()]
headers = {'Authorization': f'Bearer {api_key}'}

# We might push multiple notebooks to the same project, but only need to send
# the dockerfile once.
updated_dockerfiles = []

def update(notebook, project_id, path=''):
    expected_files = set(['Dockerfile'])
    notebook = Path(notebook).stem
    notebook_path = Path(path)/notebook
    # If notebook is a directory, publish all notebooks in that directory
    if notebook_path.is_dir():
        for p in notebook_path.rglob('*.ipynb'):
            expected_files.update(
                update(p.relative_to(notebook_path), project_id, notebook_path))
        return expected_files

    print(f'Updating {notebook_path}...')
    # Update the Dockerfile
    if project_id not in updated_dockerfiles:
        url = f"https://api.deepnote.com/v1/projects/{project_id}/files?path=Dockerfile"
        Dockerfile = f"FROM russtedrake/{repository}:{dockerhub_sha}"
        if testing:
            print(f"would be pushing to {url}")
        else:
            r = requests.put(url, headers=headers, data=Dockerfile)
            if r.status_code != 200:
                print(r.status_code, r.reason, r.text)
        updated_dockerfiles.append(project_id)

    # Update the notebook file(s)
    url = f"https://api.deepnote.com/v1/projects/{project_id}/files?path={notebook}.ipynb"
    with open(notebook_path.with_suffix('.ipynb')) as f:
        contents = f.read()
    if testing:
        print(f"would be pushing to {url}")
    else:
        r = requests.put(url, headers=headers, data=contents.encode('utf-8'))
        if r.status_code != 200:
            print(r.status_code, r.reason, r.text)
    expected_files.update([f"{notebook}.ipynb"])
    return expected_files

def check_files(expected_files, project_id):
    global check_deepnote_files
    if not check_deepnote_files:
        return

    url = f"https://deepnote.com/workspace/{workspace}/project/{project_id}/"
    try:
        files = set(subprocess.run(
            ["node", "htmlbook/deepnote_check_notebooks.js", url],
            capture_output=True, text=True, timeout=60).stdout.splitlines())
    except:
        print("Failed to run node.js notebook check. Disabling these checks.")
        print("See deepnote_check_notebooks.js for installation instructions.")
        check_deepnote_files = False
        return

    if not expected_files == files:
        print(f"Expected files: {expected_files}")
        print(f"Files on Deepnote: {files}")

with open(Path(root)/'Deepnote_workspace.txt') as workspace_file:
    workspace = workspace_file.read()

for notebook, project_id in notebooks.items():
    if isinstance(project_id, dict):
        for n, p in project_id.items():
            expected_files = update(n, p, notebook)
            check_files(expected_files, p)
    else:
        expected_files = update(notebook, project_id, '')
        check_files(expected_files, project_id)

with open(Path(root)/'chapters.js', 'w') as f:
    f.write("deepnote = ");
    json.dump(notebooks, f, sort_keys=True)
    f.write("\n")
    f.write(f'deepnote_workspace_id = "{workspace}"')
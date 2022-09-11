# Uses the deepnote API to update notebooks and Dockerfiles on deepnote, based
# on the contexts of Deepnote.json.
# https://community.deepnote.com/c/beta-testers/notebooks-api-early-access

import json
import requests
import os
from pathlib import Path
import sys

testing = False

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
    notebook_path = Path(path)/notebook
    # If notebook is a directory, publish all notebooks in that directory
    if notebook_path.is_dir():
        for p in notebook_path.rglob('*.ipynb'):
            update(p.relative_to(notebook_path), project_id, notebook_path)
        return

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

for notebook, project_id in notebooks.items():
    if isinstance(project_id, dict):
        for n, p in project_id.items():
            update(n, p, notebook)
    else:
        update(notebook, project_id, '')

with open(Path(root)/'chapters.js', 'w') as f:
    f.write("deepnote = ");
    json.dump(notebooks, f)
    f.write("\n")
    with open(Path(root)/'Deepnote_workspace.txt') as workspace_file:
        f.write(f'deepnote_workspace_id = "{workspace_file.read()}"')
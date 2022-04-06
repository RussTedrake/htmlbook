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
    print('Usage: ptyhon3 htmlbook/publish_to_deepnote.py dockerhub_sha')
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

def update(notebook, project_id, path=''):
    print(f'Updating {Path(path)/notebook}...')
    # Update the Dockerfile
    url = f"https://api.deepnote.com/v1/projects/{project_id}/files?path=Dockerfile"
    Dockerfile = f"FROM russtedrake/underactuated:{dockerhub_sha}"
    if testing:
        print(f"pushing to {url}")
    else:
        r = requests.put(url, headers=headers, data=Dockerfile)
        if r.status_code != 200:
            print(r.status_code, r.reason, r.text)

    # Update the notebook file
    url = f"https://api.deepnote.com/v1/projects/{project_id}/files?path={notebook}.ipynb"
    with open((Path(path)/notebook).with_suffix('.ipynb')) as f:
        contents = f.read()
    if testing:
        print(f"pushing to {url}")
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

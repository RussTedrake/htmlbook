# Uses the deepnote API to update notebooks and Dockerfiles on deepnote, based
# on the contexts of Deepnote.json.
# https://community.deepnote.com/c/beta-testers/notebooks-api-early-access

import json
import requests
import os
import sys

if len(sys.argv) < 2:
    print('Usage: ptyhon3 htmlbook/publish_to_deepnote.py dockerhub_sha')
    exit(-1)

chapters = json.load(open("Deepnote.json"))
dockerhub_sha = sys.argv[1]

# root should be textbook repo root
htmlbook = os.path.dirname(os.path.realpath(__file__))
root = os.path.dirname(htmlbook)
repository = os.path.basename(root) 

api_key = os.environ['DEEPNOTE_API_KEY_' + repository.upper()]
headers = {'Authorization': f'Bearer {api_key}'}

for notebook, project_id in chapters.items():
    print(f'Updating {notebook}...')
    # Update the Dockerfile
    url = f"https://api.deepnote.com/v1/projects/{project_id}/files?path=Dockerfile"
    Dockerfile = f"FROM russtedrake/underactuated:{dockerhub_sha}"
    r = requests.put(url, headers=headers, data=Dockerfile)
    if r.status_code != 200:
        print(r.status_code, r.reason, r.text)

    # Update the notebook file
    url = f"https://api.deepnote.com/v1/projects/{project_id}/files?path={notebook}.ipynb"
    with open(notebook + '.ipynb') as f:
        contents = f.read()
    r = requests.put(url, headers=headers, data=contents.encode('utf-8'))
    if r.status_code != 200:
        print(r.status_code, r.reason, r.text)

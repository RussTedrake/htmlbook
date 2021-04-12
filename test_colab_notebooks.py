
# Usage python3 test_colab_notebooks.py [notebooks]
# e.g. 
# python3 htmlbook/test_colab_notebooks.py *.ipynb
# python3 htmlbook/test_colab_notebooks.py examples/*.ipynb
# find exercises -iname "*.ipynb" -print0 | xargs -0 python3 htmlbook/test_colab_notebooks.py 

import concurrent.futures
import os
import subprocess
import sys
from time import sleep

# root should be textbook repo root
htmlbook = os.path.dirname(os.path.realpath(__file__))
root = os.path.dirname(htmlbook)
repository = os.path.basename(root) 

def test_notebook(notebook):
  return subprocess.run(
    [
      'node',
      os.path.join(htmlbook,'test_colab_notebook.js'),
      notebook,
      '--terminate_session'
    ], 
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    universal_newlines=True)

def check_output(notebook, data):
  if data.stderr:
    print(f'[\u001b[0;31mFAILED\u001b[0m]: {notebook}')
    print(data.stderr)
  else: 
    print(f'[PASSED]: {notebook}')
  assert data.returncode == 0, data

notebooks = sys.argv[1:]
if not notebooks:
  # Run all notebooks that are a source file for an active bazel rule.
  # (This is more robust than trying all .ipynb files)
  query = subprocess.run(['bazel','query',"kind('source file', deps(//...))"],
    stdout=subprocess.PIPE, universal_newlines=True)
  for path in query.stdout.splitlines():
    if path.startswith('@') or not path.endswith('.ipynb'):
      continue
    path = path.replace('//:','').replace('//','').replace(':','/')   
    if path.startswith('solutions') or path.startswith('figures'):
      continue
    notebooks.append(path)

if False:
  jobs = {}

  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    for p in notebooks:
      jobs[executor.submit(test_notebook, p)] = p 
      
    for f in concurrent.futures.as_completed(jobs):
      data = f.result()
      check_output(jobs[f], data)

else:
  for p in notebooks:
    data = test_notebook(p)
    check_output(p, data)
    sleep(60)  # Add a pause to avoid colab rate limits


# TODO: pause for an hour or so after each batch, to avoid hitting timeouts?
# TODO: run nightly and send me an email on failure?



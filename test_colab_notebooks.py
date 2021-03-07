
# Usage python3 test_colab_notebooks.py

import concurrent.futures
import os
import pathlib
import subprocess
import sys

# root should be textbook repo root
htmlbook = os.path.dirname(os.path.realpath(__file__))
root = os.path.dirname(htmlbook)
repository = os.path.basename(root) 

def test_notebook(notebook):
    print(f'Running {notebook}')
    return subprocess.run(
      [
        'node',
        os.path.join(htmlbook,'test_colab_notebook.js'),
        notebook,
        '--terminate_session'
      ], 
      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
      universal_newlines=True)
    

jobs = {}

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
  for path in pathlib.Path(root).rglob('*.ipynb'):
    p = str(path.relative_to(root))
    if any(s in p for s in ['.history','bazel','.ipynb_checkpoints']):
      continue

    jobs[executor.submit(test_notebook, p)] = p 
    
  for f in concurrent.futures.as_completed(jobs):
    data = f.result()
    if data.stderr:
      print(f'[\u001b[0;31mFAILED\u001b[0m]: {jobs[f]}')
      print(data.stderr)
    else: 
      print(f'[PASSED]: {jobs[f]}')
    assert data.returncode == 0, data






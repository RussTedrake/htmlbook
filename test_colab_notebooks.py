
# Usage python3 test_colab_notebooks.py [notebook to start from] ["--skip"]

import os
import pathlib
import subprocess
import sys

# root should be textbook repo root
htmlbook = os.path.dirname(os.path.realpath(__file__))
root = os.path.dirname(htmlbook)
repository = os.path.basename(root) 

def run(cmd, **kwargs):
    cp = subprocess.run(cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True, **kwargs)
    if cp.stderr:
        print(cp.stderr)
    assert cp.returncode == 0, cp

if len(sys.argv) > 1:
  state = 'waiting'
else:
  state = 'run'

for path in pathlib.Path(root).rglob('*.ipynb'):
  p = str(path.relative_to(root))
  if any(s in p for s in ['.history','bazel','.ipynb_checkpoints']):
    continue
  # Allow fast-forwarding to the a particular notebook: 
  if state == 'waiting':
    if p == sys.argv[1]:
      state = 'skip' if len(sys.argv)>2 and sys.argv[2] == '--skip' else 'run'
  elif state == 'skip':
    state = 'run'
  if state != 'run':
    continue

  print(f'testing {p}')
  run(['node', os.path.join(htmlbook,'test_colab_notebook.js'), p, '--terminate'])

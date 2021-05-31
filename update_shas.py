
# Usage python3 htmlbook/update_shas.py [notebooks]

import os
import pathlib
import subprocess
import sys

# root should be textbook repo root
htmlbook = os.path.dirname(os.path.realpath(__file__))
root = os.path.dirname(htmlbook)
repository = os.path.basename(root)

os.chdir(root)

out = subprocess.run(
  ['git', 'rev-parse', 'HEAD'],
  stdout=subprocess.PIPE,
  universal_newlines=True)
sha = out.stdout.strip()

notebooks = sys.argv[1:]
if not notebooks:
  for path in pathlib.Path(root).rglob('*.ipynb'):
    p = str(path.relative_to(root))
    if any(s in p for s in [
      '.history','bazel','figures','.ipynb_checkpoints'
      ]):
      continue
    notebooks.append(p)

for p in notebooks:
  s = subprocess.run([
    'sed', "-i",
    f"s/{repository}_sha='[0-9a-z]*'/{repository}_sha='{sha}'/g",
    p
  ])


## Requirements management with Poetry

```
pip install poetry poetry-plugin-export
poetry install --all-extras --with=dev,docs
```
(in a virtual environment) to install the requirements.

## Please install the pre-commit hooks

```
pip install pre-commit
pre-commit install
```

## Autoflake for notebooks

`autoflake`` is not officially supported by nbqa because it has some risks:
https://github.com/nbQA-dev/nbQA/issues/755 But it can be valuable to run it
manually and check the results.

```
nbqa autoflake --remove-all-unused-imports --in-place .
```

## To Run the Unit Tests

Install the prerequisites:
```bash
bash setup/.../install_prereqs.sh
```

Make sure that you have done a recursive checkout in this repository, or have run

```bash
git submodule update --init --recursive
```
Then run
```bash
bazel test //...
```

## Updating dependencies

Bazel currently uses requirements-bazel.txt, which we generate from poetry

To generate it, run
```
poetry lock && ./book/htmlbook/PoetryExport.sh
```

## To update the pip wheels

If you make a change to the dependencies or library directory, you
will need to update the pip wheels.
- First PR the code changes, and mark the PR with the `requires new pip wheels` label.
- Once the PR is merged update the version number in `pyproject.toml`, then
`git commit` that small change, then from the root directory, run:
```
rm -rf dist/*
poetry publish --build && cd book && ./Deepnote.sh
```
- Finally, PR the updated pyproject.toml (*without* the `requires new pip wheels` label).

Note: use `poetry config pypi-token.pypi <token>` once to set up your pypi token.

# To update the Docker image (and pip wheels)

It's good form to update the pip wheels first (so that the Docker contains the
latest pip dependencies):
```
rm -rf dist/*
poetry publish --build
./book/Deepnote_docker.sh
cd book && ./Deepnote.sh
```
And make sure to follow the printed instructions to build the image once on
deepnote. The run a few notebooks on deepnote to convince yourself you haven't
broken anything.

## Building the documentation

You will need to install `sphinx`:
```
poetry install --with docs
pip install sphinx myst-parser sphinx_rtd_theme
```

From the root directory, run
```
rm -rf book/python && sphinx-build -M html $(book/htmlbook/book_name.py) /tmp/my_doc && cp -r /tmp/my_doc/html book/python
```
Note that the website will only install the dependencies in the `docs` group, so
`poetry install --only docs` must obtain all of the relevant dependencies.



## To debug a notebook with a local build of Drake

There are several approaches, but perhaps easiest is to just add a few lines at the top of the notebook:
```
import sys
import os

python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
drake_path = os.path.expanduser(f"~/drake-install/lib/{python_version}/site-packages")
if drake_path not in sys.path:
    sys.path.insert(0, drake_path)

import pydrake
print(f"Using pydrake from: {pydrake.__file__}")
```

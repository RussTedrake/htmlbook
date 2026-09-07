## Requirements management with Poetry

```
pip install "poetry>=2.0"
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

If you have access to the solutions repository (e.g. manipulation-solutions or underactuated-solutions), run e.g.
```
git clone git@github.com:RobotLocomotion/manipulation-solutions.git solutions
cd solutions && git checkout $(cat ../solutions_sha.txt) && cd ..
```

Make sure that you have done a recursive checkout in this repository, or have run
```bash
git submodule update --init --recursive
```
Then run
```bash
pytest
```


## Updating dependencies

First update the dependency in `pyproject.toml`.

```
poetry lock
```
Then run 
```
poetry install --all-extras --with=dev,docs
```
to update your virtual environment.

## To update the pip wheels

Library and dependency changes require a new package release. Keep the source
release and its published artifacts in this order:

1. Include a new version in `pyproject.toml` in the code PR, and apply the
   `requires new pip wheels` label. Run local lint and source tests, including
   changed files in this submodule, before pushing.
2. Merge the PR after the relevant CI checks pass. A job testing the installed
   PyPI package may need the release before it can pass; check that its failure
   is caused by the unpublished version rather than a source regression.
3. Check out the merged commit with a clean working tree and initialized
   submodules. Build from that commit, so the published version has an exact
   source revision. From the repository root, use a fresh output directory:

   ```bash
   .venv/bin/python -m poetry build --output /tmp/book-release-VERSION
   ```

4. Inspect the artifacts and test the wheel in a separate environment outside
   the checkout. Publish the same artifacts:

   ```bash
   .venv/bin/python -m poetry publish --dist-dir /tmp/book-release-VERSION
   ```

5. Verify that PyPI serves the expected version and artifacts, and test a fresh
   installation. Rerun any CI jobs that were waiting for the package release.
6. Update public notebook links and instructions that depend on the release
   only after the package is available. Smoke-test the notebooks in Colab,
   including their Meshcat links.

Replace `VERSION` with the release version. Configure the PyPI token once with
`poetry config pypi-token.pypi <token>`; do not commit the token.

## To update the Docker image

Publish the pip wheels first so the image installs the released library. In
repositories providing it, run `./setup/docker/publish.sh` from the repository
root, then smoke-test the resulting image. This is a separate publication step
from the Python package release.

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

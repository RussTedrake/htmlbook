# Copyright 2020 Massachusetts Institute of Technology.
# Licensed under the BSD 3-Clause License. See LICENSE.TXT for details.

import os
import re
import sys
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)

from nbconvert.exporters import PythonExporter  # noqa: E402
from nbconvert.writers import StdoutWriter  # noqa: E402


def find_workspace_root(root=None):
    if root is None:
        root = os.getcwd()
    if os.path.exists(os.path.join(root, "WORKSPACE")):
        return root
    if os.path.exists(os.path.join(root, "WORKSPACE.bazel")):
        return root
    new_root = os.path.dirname(root)
    assert new_root != root, "Could not find workspace root"
    return find_workspace_root(new_root)


def find_workspace_name():
    workspace_file = find_workspace_root() + "/WORKSPACE.bazel"
    with open(workspace_file, "r") as file:
        for line in file:
            if line.startswith("workspace(name ="):
                # Extracting the workspace name
                name_part = line.split("=")[1].strip()
                # Removing any potential leading or trailing characters like quotes or parentheses
                workspace_name = name_part.strip(" '\"()")
                return workspace_name
    assert "Could not find workspace name in WORKSPACE.bazel file"


def main(notebook_filename, grader_throws=False):
    resources = {}
    basename = os.path.basename(notebook_filename)
    resources["unique_key"] = basename[: basename.rfind(".")]
    exporter = PythonExporter()
    output, resources = exporter.from_filename(notebook_filename, resources=resources)
    repo = find_workspace_name()
    # load startup.py from same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    startup_path = os.path.join(script_dir, "startup.py")
    with open(startup_path, "r") as file:
        startup_code = file.read()
    # Raise deprecations to errors and set 'running_as_test'
    output = (
        startup_code
        + (
            f"try:\n"
            f"    from {repo}.utils import _set_running_as_test\n"
            f"    _set_running_as_test(True)\n\n"
            f"except ModuleNotFoundError:\n"
            f"    pass\n"
        )
        + output
    )

    if grader_throws:
        output = (
            f"from {repo}.exercises.grader import set_grader_throws\n"
            f"set_grader_throws(True)\n\n"
        ) + output

    writer = StdoutWriter()
    writer.write(output, resources)


if __name__ == "__main__":
    sys.argv[0] = re.sub(r"_script\.py$", "", sys.argv[0])
    if len(sys.argv) < 2:
        print("Notebook filename is missing", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) >= 3 else False)

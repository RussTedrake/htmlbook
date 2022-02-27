# Copyright 2020 Massachusetts Institute of Technology.
# Licensed under the BSD 3-Clause License. See LICENSE.TXT for details.

from pathlib import Path
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)

from nbconvert.exporters import PythonExporter  # noqa: E402
from nbconvert.writers import StdoutWriter  # noqa: E402


def main(notebook_filename, grader_throws=False):
    resources = {}
    basename = os.path.basename(notebook_filename)
    resources["unique_key"] = basename[:basename.rfind(".")]
    exporter = PythonExporter()
    output, resources = exporter.from_filename(notebook_filename,
                                               resources=resources)
    # TODO(russt): make this more robust (e.g. use bazel workspace name?)
    repo = Path(__file__).parent.parent.parent.parent.name
    # Raise deprecations to errors and set 'running_as_test'
    output = (
        f'from pydrake.common.deprecation import DrakeDeprecationWarning\n'
        f'import warnings\n'
        f'warnings.simplefilter("error", DrakeDeprecationWarning)\n\n'
        f'try:\n'
        f'    from {repo}.utils import set_running_as_test\n'
        f'    set_running_as_test(True)\n\n'
        f'except ModuleNotFoundError:\n'
        f'    pass\n'
    ) + output

    if grader_throws:
        output = (
            f'from {repo}.exercises.grader import set_grader_throws\n'
            f'set_grader_throws(True)\n\n'
        ) + output

    writer = StdoutWriter()
    write_results = writer.write(output, resources)


if __name__ == "__main__":
    sys.argv[0] = re.sub(r"_script\.py$", "", sys.argv[0])
    if len(sys.argv) < 2:
        print("Notebook filename is missing", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) >= 3 else False)

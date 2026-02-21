"""Pytest wrapper: run check_deepnote_requirements.py (Bazel rt_py_test, needs network)."""
import os
import subprocess
import sys


def test_check_deepnote_requirements():
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    script = os.path.join(repo_root, "book", "htmlbook", "check_deepnote_requirements.py")
    result = subprocess.run(
        [sys.executable, script],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (result.stdout or "") + (result.stderr or "")

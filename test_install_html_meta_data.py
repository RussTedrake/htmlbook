"""Pytest wrapper: run install_html_meta_data.py --read_only (Bazel rt_py_test)."""
import os
import subprocess
import sys


def test_install_html_meta_data_read_only():
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    script = os.path.join(repo_root, "book", "htmlbook", "install_html_meta_data.py")
    result = subprocess.run(
        [sys.executable, script, "--read_only"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (result.stdout or "") + (result.stderr or "")

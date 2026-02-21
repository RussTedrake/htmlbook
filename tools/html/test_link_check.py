"""Pytest wrapper: run check_html_links_exist on all book HTML (Bazel rt_html_test)."""
import os
import subprocess
import sys


def test_link_check_all_html():
    # Pants runs tests with cwd = build root (sandbox root).
    repo_root = os.getcwd()
    book_dir = os.path.join(repo_root, "book")
    html_files = [
        os.path.join("book", f)
        for f in os.listdir(book_dir)
        if f.endswith(".html") and not f.endswith(".html.in")
    ]
    html_files.sort()
    script = os.path.join(
        repo_root,
        "book",
        "htmlbook",
        "tools",
        "html",
        "check_html_links_exist.py",
    )
    result = subprocess.run(
        [sys.executable, script, "--cwd", repo_root] + html_files,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (result.stdout or "") + (result.stderr or "")

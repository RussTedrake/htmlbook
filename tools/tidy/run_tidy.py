#!/usr/bin/env python3
"""
Run tidy on HTML/XML files. Used by Pants as a test; exits 0 if all pass.
Replaces the Bazel html_tidy_test rule.
"""
import os
import shutil
import subprocess
import sys


def _find_tidy():
    tidy = shutil.which("tidy")
    if tidy:
        return tidy
    for path in ("/usr/bin/tidy", "/usr/local/bin/tidy", "/opt/homebrew/bin/tidy"):
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def main():
    # Repo root: from this file go up to find pants.toml or pyproject.toml
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
    book_dir = os.path.join(root, "book")
    config = os.path.join(book_dir, ".tidy.config")
    if not os.path.isfile(config):
        print("Missing book/.tidy.config", file=sys.stderr)
        sys.exit(1)
    tidy_bin = _find_tidy()
    if not tidy_bin:
        print("tidy not found; install via e.g. brew install tidy-html5", file=sys.stderr)
        sys.exit(1)
    html_files = [
        os.path.join(book_dir, f)
        for f in os.listdir(book_dir)
        if f.endswith(".html") and not f.endswith(".html.in")
    ]
    html_files.sort()
    failed = 0
    for path in html_files:
        result = subprocess.run(
            [tidy_bin, "-config", config, "-output", "/dev/null", path],
            capture_output=True,
            text=True,
            cwd=root,
        )
        if result.returncode not in (0, 1):
            print(f"{path}: tidy failed with code {result.returncode}", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            failed += 1
        elif "error" in result.stderr.lower() and "0 errors" not in result.stderr:
            print(f"{path}: tidy reported errors", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            failed += 1
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

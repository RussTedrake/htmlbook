"""Check that every notebook in a book is executed by some test.

A notebook is covered when an `ipynb_test(...)` call in a `test_*.py` file in
the notebook's directory registers it. Exercise notebooks
(`book/<chapter>/exercises/*.ipynb`) are generated from the private solutions
checkout, so a registration in `solutions/notebooks/<chapter>/` covers them.

Notebooks that cannot run in CI belong in the book's `UNTESTED` mapping, from
path relative to `book/` to the reason, so that disabling a test leaves a
visible record. Each book calls these helpers from its own
`book/test_notebook_coverage.py`.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path


def book_notebooks(book: Path) -> list[Path]:
    """Notebooks tracked by git in `book`, excluding submodules."""
    output = subprocess.check_output(
        ["git", "ls-files", "--", "*.ipynb"], cwd=book, text=True
    )
    return sorted(book / line for line in output.splitlines())


def registered_notebooks(directory: Path) -> set[str]:
    """Notebook names registered via ipynb_test() in directory/test_*.py."""
    names = set()
    for test_file in directory.glob("test_*.py"):
        tree = ast.parse(test_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "ipynb_test"
                and node.args
                and isinstance(node.args[0], ast.Constant)
            ):
                names.add(node.args[0].value)
    return names


def _is_exercise(notebook: Path) -> bool:
    return notebook.parent.name == "exercises"


def _publicly_covered(notebook: Path) -> bool:
    return notebook.name in registered_notebooks(notebook.parent)


def untested_notebooks(book: Path, untested: dict[str, str]) -> list[str]:
    """Non-exercise notebooks that no test runs and `untested` does not list."""
    missing = []
    for notebook in book_notebooks(book):
        relative = notebook.relative_to(book).as_posix()
        if (
            not _is_exercise(notebook)
            and not _publicly_covered(notebook)
            and relative not in untested
        ):
            missing.append(relative)
    return missing


def stale_untested_entries(book: Path, untested: dict[str, str]) -> list[str]:
    """Entries of `untested` that name a missing or already-tested notebook."""
    notebooks = {nb.relative_to(book).as_posix(): nb for nb in book_notebooks(book)}
    stale = []
    for path in untested:
        if path not in notebooks:
            stale.append(f"{path}: no such tracked notebook")
        elif _publicly_covered(notebooks[path]):
            stale.append(f"{path}: now registered with ipynb_test()")
    return stale


def untested_exercises(book: Path, solutions_notebooks: Path) -> list[str]:
    """Exercise notebooks run by neither a public nor a solutions test."""
    missing = []
    for notebook in book_notebooks(book):
        if not _is_exercise(notebook) or _publicly_covered(notebook):
            continue
        chapter = notebook.parent.parent.name
        if notebook.name not in registered_notebooks(solutions_notebooks / chapter):
            missing.append(notebook.relative_to(book).as_posix())
    return missing


def assert_book_notebooks_are_tested(book: Path, untested: dict[str, str]) -> None:
    missing = untested_notebooks(book, untested)
    assert not missing, (
        "These notebooks are not run by any test. Register each one with "
        "ipynb_test() in a test_*.py file in its directory, or add it to "
        "UNTESTED in book/test_notebook_coverage.py with the reason it cannot "
        "run:\n  " + "\n  ".join(missing)
    )


def assert_untested_list_is_current(book: Path, untested: dict[str, str]) -> None:
    stale = stale_untested_entries(book, untested)
    assert not stale, "Remove these entries from UNTESTED:\n  " + "\n  ".join(stale)


def assert_exercise_notebooks_are_tested(book: Path, solutions_notebooks: Path) -> None:
    missing = untested_exercises(book, solutions_notebooks)
    assert not missing, (
        "These exercise notebooks are not run by any public or solutions test. "
        "Register each one with ipynb_test() in "
        "solutions/notebooks/<chapter>/test_*.py:\n  " + "\n  ".join(missing)
    )

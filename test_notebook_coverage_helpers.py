"""Tests for the notebook coverage helpers in htmlbook.notebook_coverage."""

import subprocess

import pytest
from htmlbook.notebook_coverage import (
    assert_book_notebooks_are_tested,
    assert_exercise_notebooks_are_tested,
    assert_untested_list_is_current,
    stale_untested_entries,
    untested_exercises,
    untested_notebooks,
)


@pytest.fixture
def book(tmp_path):
    book = tmp_path / "book"
    for path, text in {
        "pend/pend.ipynb": "{}",
        "pend/untested.ipynb": "{}",
        "pend/skipped.ipynb": "{}",
        "pend/test_notebooks_pend.py": 'ipynb_test("pend.ipynb")\n',
        "pend/exercises/public.ipynb": "{}",
        "pend/exercises/private.ipynb": "{}",
        "pend/exercises/test_notebooks_exercises.py": (
            "from htmlbook.ipynb_test import ipynb_test\n"
            'ipynb_test("public.ipynb")\n'
        ),
    }.items():
        (book / path).parent.mkdir(parents=True, exist_ok=True)
        (book / path).write_text(text)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    # An untracked notebook (e.g. generated output) is not part of the book.
    (book / "pend" / "scratch.ipynb").write_text("{}")
    return book


def test_untested_notebooks(book):
    untested = {"pend/skipped.ipynb": "Needs a GPU."}
    assert untested_notebooks(book, untested) == ["pend/untested.ipynb"]
    with pytest.raises(AssertionError, match="pend/untested.ipynb"):
        assert_book_notebooks_are_tested(book, untested)
    untested["pend/untested.ipynb"] = "Downloads large assets."
    assert_book_notebooks_are_tested(book, untested)


def test_stale_untested_entries(book):
    untested = {
        "pend/skipped.ipynb": "Needs a GPU.",
        "pend/pend.ipynb": "Was flaky.",
        "pend/gone.ipynb": "Removed.",
    }
    assert stale_untested_entries(book, untested) == [
        "pend/pend.ipynb: now registered with ipynb_test()",
        "pend/gone.ipynb: no such tracked notebook",
    ]
    with pytest.raises(AssertionError, match="gone.ipynb"):
        assert_untested_list_is_current(book, untested)
    assert_untested_list_is_current(book, {"pend/skipped.ipynb": "Needs a GPU."})


def test_untested_exercises(book, tmp_path):
    solutions = tmp_path / "solutions" / "notebooks"
    (solutions / "pend").mkdir(parents=True)
    assert untested_exercises(book, solutions) == ["pend/exercises/private.ipynb"]
    with pytest.raises(AssertionError, match="private.ipynb"):
        assert_exercise_notebooks_are_tested(book, solutions)
    (solutions / "pend" / "test_notebooks_solutions_pend.py").write_text(
        'ipynb_test("private.ipynb", grader_throws=True)\n'
    )
    assert_exercise_notebooks_are_tested(book, solutions)

import json

import nbformat
import pytest
from htmlbook import ipynb_test as runner


def test_registered_notebook_forwards_grading_option(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        runner, "_run_notebook", lambda path, **kwargs: calls.append((path, kwargs))
    )
    namespace = {
        "__file__": str(tmp_path / "test_notebooks.py"),
        "ipynb_test": runner.ipynb_test,
    }
    exec('ipynb_test("solution.ipynb", grader_throws=True)', namespace)
    namespace["test_solution"]()
    assert calls == [(tmp_path / "solution.ipynb", {"grader_throws": True})]


@pytest.mark.parametrize(
    "grader_throws,score,should_fail",
    [(True, 0, True), (True, 1, False), (False, 0, False)],
)
def test_notebook_grading(tmp_path, monkeypatch, grader_throws, score, should_fail):
    monkeypatch.setattr(runner, "_startup_prelude", lambda: "")
    monkeypatch.setattr(runner, "get_project_name", lambda: "manipulation")
    result = {
        "score": score,
        "tests": [{"name": "example", "score": score, "max_score": 1}],
    }
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell(
                "from pathlib import Path\n"
                "from manipulation.exercises.grader import Grader\n"
                f"Path('results.json').write_text({json.dumps(result)!r})\n"
                "Grader.print_test_results('results.json')\n"
            )
        ]
    )
    path = tmp_path / "grading.ipynb"
    nbformat.write(notebook, path)
    if should_fail:
        with pytest.raises(
            pytest.fail.Exception, match="Grader did not award full points"
        ):
            runner._run_notebook(path, grader_throws=grader_throws)
    else:
        runner._run_notebook(path, grader_throws=grader_throws)

import nbformat
import pytest
from htmlbook import ipynb_test


@pytest.mark.parametrize(
    "strict,full_credit", [(False, False), (True, False), (True, True)]
)
def test_registered_notebook_grading(tmp_path, monkeypatch, strict, full_credit):
    # Exercise the registered test and the child process, with a small grader
    # fixture so htmlbook's tests do not depend on a particular book's package.
    package = tmp_path / "grading_fixture"
    exercises = package / "exercises"
    exercises.mkdir(parents=True)
    (package / "__init__.py").touch()
    (exercises / "__init__.py").touch()
    (exercises / "grader.py").write_text(
        "strict = False\n"
        "def set_grader_throws(value):\n"
        "    global strict\n"
        "    strict = value\n"
        "def grade(full_credit):\n"
        "    if strict and not full_credit:\n"
        "        raise RuntimeError('Grader did not award full points.')\n"
    )
    monkeypatch.setattr(ipynb_test, "get_project_name", lambda: "grading-fixture")
    monkeypatch.setattr(ipynb_test, "_startup_prelude", lambda: "")
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell(
                "from grading_fixture.exercises.grader import grade\n"
                f"grade({full_credit!r})\n"
            )
        ]
    )
    nbformat.write(notebook, tmp_path / "example.ipynb")
    namespace = {"__file__": str(tmp_path / "test_example.py")}
    # Omit the option in the default case to cover existing public callers.
    option = ", grader_throws=True" if strict else ""
    exec(
        "from htmlbook.ipynb_test import ipynb_test\n"
        f"ipynb_test('example.ipynb'{option})\n",
        namespace,
    )
    if strict and not full_credit:
        with pytest.raises(
            pytest.fail.Exception, match="Grader did not award full points"
        ):
            namespace["test_example"]()
    else:
        namespace["test_example"]()

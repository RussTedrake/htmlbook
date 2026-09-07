import sys
from pathlib import Path
from unittest.mock import Mock

import nbformat

from htmlbook import ipynb_test


def test_export_conditional_magic_and_refresh_cached_template(tmp_path, monkeypatch):
    template_file = tmp_path / "nbconvert/templates/python/index.py.j2"
    template_file.parent.mkdir(parents=True)
    template_file.write_text("stale template", encoding="utf-8")
    monkeypatch.setattr(
        ipynb_test,
        "Path",
        lambda value: tmp_path if value == "/tmp/jupyter_templates" else Path(value),
    )
    monkeypatch.setattr(ipynb_test, "_startup_prelude", lambda: "")
    # Explicit template selection must work even with a different Jupyter home.
    monkeypatch.setenv("JUPYTER_DATA_DIR", str(tmp_path / "other-jupyter-home"))
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell(
                'import sys\nif "google.colab" in sys.modules:\n'
                "    %pip install -q manipulation\n"
            ),
            nbformat.v4.new_markdown_cell("This should not become Python."),
            nbformat.v4.new_code_cell("result = 42"),
        ]
    )
    notebook_path = tmp_path / "example.ipynb"
    nbformat.write(notebook, notebook_path)
    source = ipynb_test._notebook_source(notebook_path)
    assert "ipython2python" in template_file.read_text(encoding="utf-8")
    code = compile(source, str(notebook_path), "exec")

    shell = Mock()
    monkeypatch.delitem(sys.modules, "google.colab", raising=False)
    namespace = {"get_ipython": lambda: shell}
    exec(code, namespace)
    shell.run_line_magic.assert_not_called()
    assert namespace["result"] == 42

    monkeypatch.setitem(sys.modules, "google.colab", Mock())
    exec(code, namespace)
    shell.run_line_magic.assert_called_once_with("pip", "install -q manipulation")

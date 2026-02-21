from __future__ import annotations

import contextlib
import inspect
import os
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

import nbformat
import pytest
from nbconvert.exporters import PythonExporter

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _prepare_nbconvert_template() -> None:
    temp_jupyter_dir = Path("/tmp/jupyter_templates")
    template_dir = temp_jupyter_dir / "nbconvert" / "templates" / "python"
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / "index.py.j2"
    if not template_file.exists():
        template_file.write_text(
            """# coding: utf-8
{%- for cell in nb.cells -%}
{%- if cell.cell_type == 'code' -%}
{% for line in cell.source.splitlines() %}
{{ line }}
{% endfor %}
{% if not loop.last %}

{% endif %}
{%- endif -%}
{%- endfor -%}
""",
            encoding="utf-8",
        )
    os.environ.setdefault("JUPYTER_DATA_DIR", str(temp_jupyter_dir))
    os.environ.setdefault("JUPYTER_CONFIG_DIR", "/tmp")


def _startup_prelude() -> str:
    startup = _REPO_ROOT / "book/htmlbook/tools/jupyter/startup.py"
    startup_code = startup.read_text(encoding="utf-8")
    startup_code = startup_code.replace(
        'if "/usr/lib/python" in sys.modules["mpl_toolkits"].__file__:',
        'mpl_toolkits_file = getattr(sys.modules["mpl_toolkits"], "__file__", "") or ""\n'
        '    if "/usr/lib/python" in mpl_toolkits_file:',
    )

    return (
        startup_code
        + "\n\n"
        + "try:\n"
        + "    from underactuated.utils import _set_running_as_test\n"
        + "    _set_running_as_test(True)\n"
        + "except ModuleNotFoundError:\n"
        + "    pass\n\n"
    )


@contextlib.contextmanager
def _chdir(path: Path):
    old = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _notebook_source(notebook_path: Path) -> str:
    warnings.filterwarnings("ignore", category=SyntaxWarning)
    with contextlib.suppress(Exception):
        from pydrake.common.deprecation import DrakeDeprecationWarning

        warnings.simplefilter("error", DrakeDeprecationWarning)

    _prepare_nbconvert_template()
    notebook = nbformat.read(notebook_path, as_version=4)
    exporter = PythonExporter()
    source, _ = exporter.from_notebook_node(notebook)
    source = source.replace("plot_system_graphviz", "#plot_system_graphviz")
    return _startup_prelude() + source


def _run_notebook(notebook_path: Path) -> None:
    source = _notebook_source(notebook_path)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        prefix=f"ipynb_{notebook_path.stem}_",
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(source)
        source_path = Path(f.name)

    env = os.environ.copy()
    env["PYTHONFAULTHANDLER"] = "1"
    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    env.setdefault("NUMEXPR_NUM_THREADS", "1")

    pythonpath = [str(_REPO_ROOT), str(_REPO_ROOT / "book"), str(notebook_path.parent)]
    if env.get("PYTHONPATH"):
        pythonpath.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath)

    cmd = [sys.executable, str(source_path)]
    workdir_cm = tempfile.TemporaryDirectory(prefix=f"ipynb_cwd_{notebook_path.stem}_")
    try:
        with workdir_cm as run_cwd:
            result = subprocess.run(
                cmd,
                cwd=run_cwd,
                env=env,
                capture_output=True,
                text=True,
            )
    finally:
        source_path.unlink(missing_ok=True)

    if result.returncode != 0:
        details = [
            f"Notebook execution failed: {notebook_path}",
            f"Exit code: {result.returncode}",
        ]
        if result.stdout:
            details.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            details.append(f"STDERR:\n{result.stderr}")
        pytest.fail("\n\n".join(details))


def ipynb_test(path: str, *, name: str | None = None) -> None:
    frame = inspect.currentframe()
    assert frame is not None
    caller = frame.f_back
    assert caller is not None

    module_globals = caller.f_globals
    caller_file = Path(module_globals["__file__"]).resolve()
    notebook_path = (caller_file.parent / path).resolve()

    test_name = name or f"test_{notebook_path.stem}"

    @pytest.mark.notebook
    def _test() -> None:
        _run_notebook(notebook_path)

    _test.__name__ = test_name
    _test.__qualname__ = test_name
    module_globals[test_name] = _test

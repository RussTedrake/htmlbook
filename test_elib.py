import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

loader = importlib.machinery.SourceFileLoader(
    "elib_cgi", str(Path(__file__).with_name("elib.cgi"))
)
spec = importlib.util.spec_from_loader(loader.name, loader)
elib = importlib.util.module_from_spec(spec)
loader.exec_module(elib)


def request(body):
    data = json.dumps(body).encode()
    return (
        {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": "application/json; charset=utf-8",
            "CONTENT_LENGTH": str(len(data)),
        },
        io.BytesIO(data),
    )


def test_tags_preserve_order_and_allow_sql_metacharacters():
    assert elib.read_tags(*request(["B", "A", "B", "O'Brien"])) == ["B", "A", "O'Brien"]


@pytest.mark.parametrize(
    "body", [{"tags": []}, [3], [""], [" A"], ["A\nB"], ["A"] * 1001]
)
def test_invalid_tags(body):
    with pytest.raises(elib.RequestError):
        elib.read_tags(*request(body))


@pytest.mark.parametrize(
    "updates,status",
    [
        ({"REQUEST_METHOD": "GET"}, "405"),
        ({"CONTENT_TYPE": "text/plain"}, "415"),
        ({"CONTENT_LENGTH": "bad"}, "400"),
        ({"CONTENT_LENGTH": "131073"}, "413"),
        ({"CONTENT_LENGTH": "100"}, "400"),
    ],
)
def test_invalid_http_request(updates, status):
    environ, stream = request(["A"])
    environ.update(updates)
    with pytest.raises(elib.RequestError) as error:
        elib.read_tags(environ, stream)
    assert error.value.status.startswith(status)


def test_lookup_parameters_projection_and_cleanup(monkeypatch, tmp_path):
    import mysql.connector

    config = tmp_path / "elib.json"
    config.write_text("{}")
    monkeypatch.setattr(elib, "CONFIG_PATH", config)
    connection = MagicMock()
    cursor = connection.cursor.return_value
    cursor.fetchall.return_value = [{"bibtag": "O'Brien"}]
    monkeypatch.setattr(mysql.connector, "connect", lambda **kwargs: connection)
    assert elib.lookup(["O'Brien", "missing"]) == {
        "entries": {"O'Brien": {"bibtag": "O'Brien"}},
        "missing": ["missing"],
    }
    sql, parameters = cursor.execute.call_args.args
    assert "O'Brien" not in sql
    assert parameters == ("O'Brien", "missing")
    assert "CASE WHEN isPublic THEN url ELSE NULL END" in sql
    assert "SELECT *" not in sql
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_database_failure_is_http_error_without_details(monkeypatch, capsys):
    environ, stream = request(["A"])
    monkeypatch.setattr(elib.os, "environ", environ)
    monkeypatch.setattr(elib.sys, "stdin", io.TextIOWrapper(stream))

    def fail(tags):
        raise RuntimeError("sensitive connection detail")

    monkeypatch.setattr(elib, "lookup", fail)
    elib.main()
    output = capsys.readouterr()
    assert "503 Service Unavailable" in output.out
    assert "sensitive connection detail" not in output.out
    assert "sensitive connection detail" in output.err

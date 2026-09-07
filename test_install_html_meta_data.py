import io
import json
from unittest.mock import Mock
from urllib.error import URLError

import pytest
from htmlbook import install_html_meta_data as metadata
from htmlbook.install_html_meta_data import install_html_meta_data


def test_install_html_meta_data_check() -> None:
    assert not install_html_meta_data(check=True)


def test_batched_bibliography_and_repeated_rendering(monkeypatch):
    entry = {
        "bibtag": "A",
        "bibtype": "article",
        "title": "Title",
        "year": "2025",
        "url": "paper.pdf",
        "isPublic": 1,
    }
    response = io.BytesIO(json.dumps({"entries": {"A": entry}, "missing": []}).encode())
    fetch = Mock(return_value=response)
    monkeypatch.setattr(metadata, "urlopen", fetch)
    entries = metadata.fetch_bibliography("https://example.org/elib.cgi", ["A", "A"])
    assert json.loads(fetch.call_args.args[0].data) == ["A"]
    html = '<html><elib>A+A</elib><div id="references"></div></html>'
    first = metadata.write_references(entries, html, "chapter.html")
    assert first == metadata.write_references(entries, html, "another.html")
    assert entries["A"] == entry
    assert first.count("<li id=A>") == 1


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"entries": {}, "missing": []},
        {"entries": {}, "missing": ["A"]},
        {"entries": {"A": {"bibtag": "B"}}, "missing": []},
        {"entries": {"A": {}}, "missing": ["A"]},
    ],
)
def test_invalid_or_missing_bibliography(monkeypatch, payload):
    monkeypatch.setattr(
        metadata,
        "urlopen",
        lambda *args, **kwargs: io.BytesIO(json.dumps(payload).encode()),
    )
    with pytest.raises(RuntimeError):
        metadata.fetch_bibliography("https://example.org/elib.cgi", ["A"])


def test_network_failure_precedes_any_writes(monkeypatch):
    def fail(*args, **kwargs):
        raise URLError("unavailable")

    monkeypatch.setattr(metadata, "urlopen", fail)
    write = Mock()
    monkeypatch.setattr(metadata, "write_file_as_string", write)
    with pytest.raises(RuntimeError, match="Failed to fetch"):
        install_html_meta_data()
    write.assert_not_called()

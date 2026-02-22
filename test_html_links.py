from __future__ import annotations

import os
import re
import time
from pathlib import Path
from urllib.parse import unquote

import pytest
from bs4 import BeautifulSoup

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover
    requests = None

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_URL = f"https://{ROOT.name}.csail.mit.edu/"
IGNORE_LINK_DOMAINS = (
    "sr.stanford.edu",
    "www.robotics.tu-berlin.de",
    "colab.research.google.com",
    "accessibility.mit.edu",
    "kuffner.org",
)

BOOK_DIR = ROOT / "book"
CHECK_EXTERNAL_LINKS = os.environ.get("CHECK_EXTERNAL_LINKS", "").lower() in {
    "1",
    "true",
    "yes",
}

_EXTERNAL_LINK_CACHE: dict[tuple[str, str], bool] = {}


def _book_html_sources() -> list[Path]:
    files = list(BOOK_DIR.glob("*.html"))
    files.extend(BOOK_DIR.glob("*.html.in"))
    return sorted(files)


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _get_links_from_string(contents: str, extension: str) -> list[str]:
    if extension.lower() == ".ipynb":
        return re.findall(r"\((\s*http.*?)\)", contents)
    return [
        el["href"]
        for el in BeautifulSoup(contents, features="html.parser").select("a[href]")
    ]


def _html_has_id(html: str, element_id: str) -> bool:
    if "github.com" in html:
        # We won't find anchors like #L55 in raw GitHub HTML.
        return True
    decoded_id = unquote(element_id)
    return BeautifulSoup(html, features="html.parser").find(id=decoded_id) is not None


def _is_transient_http_status(status_code: int) -> bool:
    return status_code in {403, 406, 418, 429, 503}


def _request_with_retries(link: str, anchor_id: str, attempts: int = 2):
    if requests is None:
        return None
    method = requests.get if anchor_id else requests.head
    timeout_s = 8
    last_response = None
    for attempt in range(attempts):
        try:
            response = method(link, timeout=timeout_s)
            last_response = response
            if response.ok:
                return response
            if not _is_transient_http_status(response.status_code):
                return response
        except Exception:
            if attempt == attempts - 1:
                raise
            # Retry once for network blips, but keep the test fast.
        if attempt < attempts - 1:
            time.sleep(0.1)
    return last_response


def _external_link_ok(link: str, anchor_id: str) -> bool:
    cache_key = (link, anchor_id)
    if cache_key in _EXTERNAL_LINK_CACHE:
        return _EXTERNAL_LINK_CACHE[cache_key]

    try:
        response = _request_with_retries(link, anchor_id, attempts=2)
        if response is None:
            ok = True
        elif _is_transient_http_status(response.status_code):
            ok = True
        elif not response.ok:
            ok = False
        elif anchor_id and not _html_has_id(response.text, anchor_id):
            ok = False
        else:
            ok = True
    except Exception:
        ok = False

    _EXTERNAL_LINK_CACHE[cache_key] = ok
    return ok


def _check_html_links(filename: Path) -> list[str]:
    extension = filename.suffix
    contents = _read_file(filename)
    broken_links: list[str] = []

    for raw_link in _get_links_from_string(contents, extension):
        link = raw_link.strip()
        if link.startswith(REPOSITORY_URL):
            link = link.removeprefix(REPOSITORY_URL)
        if "#" in link:
            url, anchor_id = link.split("#", maxsplit=1)
        else:
            url, anchor_id = link, ""

        if not url:
            if not _html_has_id(contents, anchor_id):
                broken_links.append(link)
        elif not url[:4].lower() == "http":
            if url[:4].lower() == "data" and os.environ.get("GITHUB_ACTIONS"):
                # Don't require the data directory on CI.
                continue
            if (
                url.startswith("Spring")
                or url.startswith("Fall")
                or url.startswith("python")
            ):
                # Ignore versioned term URLs.
                continue
            local_path = ROOT / "book" / url
            if not local_path.exists():
                broken_links.append(link)
                continue
            if filename.name == "index.html" and anchor_id.startswith("section"):
                continue
            if anchor_id and not _html_has_id(_read_file(local_path), anchor_id):
                broken_links.append(link)
        elif any(domain in url for domain in IGNORE_LINK_DOMAINS):
            continue
        elif requests is not None and CHECK_EXTERNAL_LINKS:
            if not _external_link_ok(link, anchor_id):
                broken_links.append(link)

    for tag in ("jupyter", "pysrcinclude", "pysrc"):
        index = 0
        while contents.find(f"<{tag}>", index) > 0:
            start = contents.find(f"<{tag}>", index) + len(tag) + 2
            end = contents.find(f"</{tag}>", start)
            index = end + len(tag) + 3
            source_file = ROOT / "book" / contents[start:end]
            if not source_file.exists():
                broken_links.append(f"<{tag}>{contents[start:end]}</{tag}>")

    for ref in re.finditer(r"\\ref{(.*?)}", contents):
        label = ref[1]
        if f"\\label{{{label}}}" not in contents:
            broken_links.append(ref[0])

    return broken_links


def test_html_links_exist() -> None:
    failures: list[str] = []
    for html_path in _book_html_sources():
        broken_links = _check_html_links(html_path)
        if broken_links:
            details = "\n".join(f"- {link}" for link in broken_links)
            failures.append(f"HTML link check failed for {html_path.name}\n{details}")
    if failures:
        pytest.fail("\n\n".join(failures))

import json
import re
import time
from pathlib import Path

import pytest
import requests
from htmlbook.book_name import get_project_name

# root should be textbook repo root.
HTMLBOOK = Path(__file__).resolve().parent
BOOK = HTMLBOOK.parent
ROOT = BOOK.parent


def _get_formatted_version() -> str | None:
    with open(ROOT / "pyproject.toml") as file:
        for line in file:
            if line.strip().startswith("version ="):
                version = line.split("=", 1)[1].strip().strip('"')
                return version
    return None


with open(BOOK / "Deepnote.json") as f:
    DEEPNOTE = json.load(f)

VERSION_FROM_POETRY = _get_formatted_version()
PROJECT_NAME = get_project_name()

if VERSION_FROM_POETRY is None:
    raise RuntimeError("Could not find version in pyproject.toml")


def _check_project_version(chapter: str, project_id: str) -> None:
    url = (
        f"https://deepnote.com/api/project/{project_id}"
        "/download-file?path=requirements.txt"
    )
    response = None
    last_error = None
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                break
            if response.status_code == 401:
                break
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1.0)
            continue
    assert response is not None, (
        "failed to get requirements.txt "
        f"for chapter {chapter}. last error: {last_error!r}"
    )
    if response.status_code == 401:
        pytest.fail(
            f"deepnote chapter {chapter} returned 401 (unauthorized). "
            "Also check Deepnote project sharing settings: "
            "'Anyone with a link to this project' may be disabled."
        )
    assert response.status_code == 200, (
        "failed to get requirements.txt "
        f"for chapter {chapter}: {response.status_code} {response.reason}. "
        f"last error: {last_error!r}"
    )

    pattern = rf"^\s*{re.escape(PROJECT_NAME)}\s*==\s*([^\s#]+)"
    match = re.search(pattern, response.text, re.MULTILINE)
    if not match:
        other_name = (
            "manipulation" if PROJECT_NAME == "underactuated" else "underactuated"
        )
        other_pattern = rf"^\s*{re.escape(other_name)}\s*==\s*([^\s#]+)"
        other_match = re.search(other_pattern, response.text, re.MULTILINE)
        if other_match:
            pytest.fail(
                f"chapter {chapter} has {other_name}=={other_match.group(1)} in "
                f"requirements.txt, but this repo expects {PROJECT_NAME}. "
                "Please run publish_to_deepnote.py to refresh that project."
            )
        pytest.fail(
            f"failed to extract {PROJECT_NAME} version from requirements.txt "
            f"for chapter {chapter}. requirements.txt: {response.text}"
        )

    version = match.group(1)
    assert version == VERSION_FROM_POETRY, (
        f"deepnote chapter {chapter} notebook has version {version} in "
        f"requirements.txt, but pyproject.toml has {VERSION_FROM_POETRY}. "
        "Please run publish_to_deepnote.py."
    )


@pytest.mark.parametrize(
    ("chapter", "project_id"),
    sorted(DEEPNOTE.items()),
)
def test_deepnote_requirements_match_pyproject_version(
    chapter: str, project_id: str
) -> None:
    _check_project_version(chapter, project_id)

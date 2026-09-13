"""Live operational check, enabled by the owning book's chapters.json."""

import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest
from htmlbook.http_retry import retry_http
from htmlbook.notifier_health import check_health


def test_annotation_notifier_health():
    chapters = Path(__file__).resolve().parent.parent / "chapters.json"
    url = json.loads(chapters.read_text()).get("annotation_notifier_health_url")
    if not url:
        pytest.skip("No annotation notifier configured for this book")

    def read_status():
        # Avoid a cached healthy response concealing a stopped cron job.
        separator = "&" if "?" in url else "?"
        request = Request(
            url + separator + urlencode({"check": time.time_ns()}),
            headers={"Cache-Control": "no-cache"},
        )
        with urlopen(request, timeout=15) as response:
            assert response.status == 200, f"HTTP {response.status}"
            return json.load(response)

    try:
        check_health(retry_http(read_status))
    except Exception as error:
        pytest.fail(
            f"Annotation notifier unhealthy at {url}: {error}. "
            "Check the hourly hypothesis_feed cron job and notifier.log on the "
            "hosting server; see docs/hosting.md.",
            pytrace=False,
        )

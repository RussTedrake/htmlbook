from datetime import datetime, timedelta, timezone

import pytest
from htmlbook.notifier_health import check_health

NOW = datetime(2026, 9, 13, tzinfo=timezone.utc)


@pytest.mark.parametrize("failures", [0, 1])
def test_recent_success(failures):
    check_health(
        {
            "last_success": (NOW - timedelta(hours=1)).isoformat(),
            "consecutive_failures": failures,
        },
        now=NOW,
    )


@pytest.mark.parametrize(
    "status, message",
    [
        (
            {
                "last_success": (NOW - timedelta(hours=4)).isoformat(),
                "consecutive_failures": 0,
            },
            "hours ago",
        ),
        (
            {"last_success": NOW.isoformat(), "consecutive_failures": 2},
            "consecutive failures",
        ),
        (
            {
                "last_success": (NOW + timedelta(hours=1)).isoformat(),
                "consecutive_failures": 0,
            },
            "future",
        ),
        (
            {"last_success": "yesterday", "consecutive_failures": 0},
            "Invalid last_success",
        ),
        (
            {"last_success": "2026-09-13T00:00:00", "consecutive_failures": 0},
            "timezone",
        ),
        ({"last_success": None, "consecutive_failures": 0}, "Missing last_success"),
        (
            {"last_success": NOW.isoformat(), "consecutive_failures": True},
            "Invalid consecutive",
        ),
        ({}, "Invalid consecutive"),
        ([], "JSON object"),
    ],
)
def test_unhealthy_status(status, message):
    with pytest.raises(AssertionError, match=message):
        check_health(status, now=NOW)

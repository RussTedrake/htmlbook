"""Validate a public annotation-notifier heartbeat without private log data."""

from datetime import datetime, timezone


def check_health(status, *, now=None):
    assert isinstance(status, dict), "Notifier status must be a JSON object"
    failures = status.get("consecutive_failures")
    assert type(failures) is int and failures >= 0, "Invalid consecutive_failures"
    stamp = status.get("last_success")
    assert isinstance(stamp, str), "Missing last_success timestamp"
    try:
        last_success = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError as error:
        raise AssertionError("Invalid last_success timestamp") from error
    assert last_success.tzinfo is not None, "last_success must include a timezone"
    age = ((now or datetime.now(timezone.utc)) - last_success).total_seconds()
    assert age >= -300, "Notifier last_success is in the future"
    assert age <= 3 * 3600, f"Notifier last succeeded {age / 3600:.1f} hours ago"
    assert failures < 2, f"Notifier has {failures} consecutive failures"

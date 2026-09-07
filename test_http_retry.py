import io
import ssl
from http.client import IncompleteRead
from unittest.mock import Mock, call
from urllib.error import HTTPError, URLError

import pytest
from htmlbook import http_retry


@pytest.mark.parametrize(
    "error",
    [
        TimeoutError("timed out"),
        URLError(TimeoutError("connect timed out")),
        ConnectionResetError("connection reset"),
        IncompleteRead(b"partial"),
        HTTPError("https://example.org", 503, "Unavailable", {}, io.BytesIO()),
    ],
)
def test_transient_failure_recovers(monkeypatch, error):
    sleep = Mock()
    monkeypatch.setattr(http_retry.time, "sleep", sleep)
    operation = Mock(side_effect=[error, "response"])
    assert http_retry.retry_http(operation) == "response"
    assert operation.call_count == 2
    sleep.assert_called_once_with(1)
    if isinstance(error, HTTPError):
        assert error.closed


def test_retry_budget_is_bounded(monkeypatch):
    sleep = Mock()
    monkeypatch.setattr(http_retry.time, "sleep", sleep)
    error = TimeoutError("still unavailable")
    operation = Mock(side_effect=error)
    with pytest.raises(TimeoutError) as caught:
        http_retry.retry_http(operation)
    assert caught.value is error
    assert operation.call_count == 3
    assert sleep.call_args_list == [call(1), call(2)]


@pytest.mark.parametrize(
    "error",
    [
        HTTPError("https://example.org", 400, "Bad Request", {}, io.BytesIO()),
        HTTPError("https://example.org", 404, "Not Found", {}, io.BytesIO()),
        URLError(ssl.SSLCertVerificationError("invalid certificate")),
        ValueError("invalid JSON"),
    ],
)
def test_permanent_failure_is_not_retried(monkeypatch, error):
    sleep = Mock()
    monkeypatch.setattr(http_retry.time, "sleep", sleep)
    operation = Mock(side_effect=error)
    with pytest.raises(type(error)) as caught:
        http_retry.retry_http(operation)
    assert caught.value is error
    operation.assert_called_once_with()
    sleep.assert_not_called()

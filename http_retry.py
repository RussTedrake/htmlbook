"""Bounded retries for HTTP operations that are safe to repeat."""

import logging
import ssl
import time
from http.client import IncompleteRead, RemoteDisconnected
from urllib.error import HTTPError, URLError


def retry_http(operation):
    """Try a read-only operation up to three times, retaining its own timeout.

    The operation must consume and close its response before returning. Do not
    use this for requests that mutate server state, even if a timeout is raised.
    """
    for attempt in range(3):
        try:
            return operation()
        except HTTPError as error:
            error.close()
            if error.code not in {408, 429, 500, 502, 503, 504} or attempt == 2:
                raise
            reason = str(error)
        except URLError as error:
            if isinstance(error.reason, ssl.SSLCertVerificationError) or attempt == 2:
                raise
            reason = str(error)
        except (
            TimeoutError,
            ConnectionError,
            IncompleteRead,
            RemoteDisconnected,
        ) as error:
            if attempt == 2:
                raise
            reason = str(error)
        delay = 2**attempt
        logging.warning(
            "HTTP attempt %d/3 failed: %s; retrying in %d seconds",
            attempt + 1,
            reason,
            delay,
        )
        time.sleep(delay)

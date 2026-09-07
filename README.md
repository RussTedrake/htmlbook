htmlbook
========

Bibliography metadata is fetched in one JSON POST from the HTTPS endpoint set
by `elib_url` in the consuming book's `chapters.json`. The request is an array
of citation tags; the response is an object with `entries` (records keyed by
tag) and `missing` (an array of unresolved tags). Database access is handled by
the endpoint, not by htmlbook. Both published and draft chapters are included.
Missing entries, invalid responses, and connection failures stop metadata
installation before any HTML files are written, including in `--check` mode.

The shared `elib.cgi` implementation uses MySQL Connector/Python 9.2 or newer.
Serve it directly at `/htmlbook/elib.cgi`. When Apache starts it with system
Python, it re-executes using the consuming repository's `.venv/bin/python`.
Its database
credentials (`user` and `password`) are read from `/etc/elib.json`, or the path
specified by `ELIB_CONFIG`. Keep this configuration outside the document root
and readable by the CGI account. The service only returns fields used by the
renderer, and never returns private paper URLs. Requests are limited to 1000
tags and 128 KiB. Database failures return HTTP 503; invalid requests return 4xx.

To enable MathJax without an internet connection, do
```
git clone https://github.com/mathjax/MathJax --depth 1
```
in the htmlbook root directory.

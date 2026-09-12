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

MathJax 4 pages load `mathjax-config.js`, then `mathjax-loader.js`, both with
`defer`. The loader pins MathJax 4.1.3 and uses CommonHTML with the default New
Computer Modern font. Call `typesetMath()` after inserting or transforming
content; its promise resolves after startup and asynchronous typesetting.
`loadChapter()` waits before scrolling to the URL fragment. The HTML capture
script also waits for typesetting and web fonts before saving the page.

The loader uses the CDN first and falls back to an optional local installation
if the runtime script cannot be fetched. To install the matching runtime and
fonts, run this from the htmlbook root:

```sh
npm install --prefix MathJax --no-save mathjax@4.1.3
```

The fallback points both the runtime and default font data at that installation.
A partial CDN failure after the runtime has loaded is reported by MathJax; it
does not trigger a second runtime. The previous v3 `MathJax/es5` checkout is not
used by this loader.

Run the loading and asynchronous typesetting tests with:

```sh
node --test test_mathjax.js
```

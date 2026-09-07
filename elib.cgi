#!/usr/bin/env python3
"""Read-only bibliography lookup. POST a JSON array of citation tags."""

import json
import os
import sys
import traceback
from pathlib import Path

MAX_BODY_BYTES = 128 * 1024
MAX_TAGS = 1000
MAX_TAG_LENGTH = 255
CONFIG_PATH = Path(os.environ.get("ELIB_CONFIG", "/etc/elib.json"))
FIELDS = (
    "bibtag",
    "bibtype",
    "author",
    "chapter",
    "title",
    "publisher",
    "journal",
    "booktitle",
    "eprint",
    "school",
    "number",
    "volume",
    "pages",
    "month",
    "year",
    "isPublic",
)


class RequestError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def read_tags(environ, stream):
    if environ.get("REQUEST_METHOD") != "POST":
        raise RequestError(
            "405 Method Not Allowed", "Use POST with a JSON array of tags."
        )
    if (
        environ.get("CONTENT_TYPE", "").split(";")[0].strip().lower()
        != "application/json"
    ):
        raise RequestError("415 Unsupported Media Type", "Expected application/json.")
    try:
        length = int(environ.get("CONTENT_LENGTH", ""))
    except ValueError:
        raise RequestError("400 Bad Request", "Invalid Content-Length.") from None
    if not 0 < length <= MAX_BODY_BYTES:
        raise RequestError(
            "413 Content Too Large", "Request body must be 1–131072 bytes."
        )
    body = stream.read(length)
    if len(body) != length:
        raise RequestError("400 Bad Request", "Incomplete request body.")
    try:
        tags = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        raise RequestError("400 Bad Request", "Invalid JSON.") from None
    if not isinstance(tags, list) or len(tags) > MAX_TAGS:
        raise RequestError("400 Bad Request", "Expected an array of at most 1000 tags.")
    if any(
        not isinstance(tag, str)
        or not tag
        or len(tag) > MAX_TAG_LENGTH
        or tag != tag.strip()
        or any(ord(char) < 32 for char in tag)
        for tag in tags
    ):
        raise RequestError(
            "400 Bad Request",
            "Tags must be nonempty strings without surrounding whitespace or control characters.",
        )
    return list(dict.fromkeys(tags))


def lookup(tags):
    if not tags:
        return {"entries": {}, "missing": []}
    import mysql.connector

    config = json.loads(CONFIG_PATH.read_text())
    config.update(
        host="mysql.csail.mit.edu",
        database="elib",
        connection_timeout=10,
        read_timeout=15,
        write_timeout=15,
    )
    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor(dictionary=True)
        try:
            # Private paper URLs never leave the database.
            columns = ", ".join("`" + field + "`" for field in FIELDS)
            placeholders = ", ".join(["%s"] * len(tags))
            cursor.execute(
                f"SELECT {columns}, CASE WHEN isPublic THEN url ELSE NULL END AS url "
                f"FROM bibtex WHERE bibtag IN ({placeholders})",
                tuple(tags),
            )
            rows = {row["bibtag"]: row for row in cursor.fetchall()}
        finally:
            cursor.close()
    finally:
        connection.close()
    # Return exact requested tags only, even if the DB collation ignores case.
    entries = {tag: rows[tag] for tag in tags if tag in rows}
    return {"entries": entries, "missing": [tag for tag in tags if tag not in entries]}


def main():
    status = "200 OK"
    try:
        result = lookup(read_tags(os.environ, sys.stdin.buffer))
        body = json.dumps(result, ensure_ascii=True)
    except RequestError as error:
        status = error.status
        body = json.dumps({"error": str(error)})
    except Exception:
        traceback.print_exc(file=sys.stderr)
        status = "503 Service Unavailable"
        body = json.dumps({"error": "Bibliography lookup unavailable."})
    headers = [
        f"Status: {status}",
        "Content-Type: application/json; charset=utf-8",
        "Cache-Control: no-store",
        "X-Content-Type-Options: nosniff",
    ]
    if status.startswith("405"):
        headers.append("Allow: POST")
    sys.stdout.write("\r\n".join(headers) + "\r\n\r\n" + body + "\n")


if __name__ == "__main__":
    # Apache may start us with system Python. Use the consuming repository's
    # virtual environment without embedding a project-specific absolute path.
    venv = Path(__file__).resolve().parents[2] / ".venv"
    if Path(sys.prefix).resolve() != venv.resolve():
        python = str(venv / "bin" / "python")
        os.execv(python, [python, str(Path(__file__).resolve())])
    main()

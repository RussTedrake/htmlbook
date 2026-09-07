import argparse
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from lxml.html import document_fromstring, parse

if __package__:
    from .http_retry import retry_http
else:
    from http_retry import retry_http

change_detected = False
READ_ONLY = False


def reference_tags(s):
    doc = document_fromstring(s)
    return list(
        dict.fromkeys(
            tag.strip() for ref in doc.findall(".//elib") for tag in ref.text.split("+")
        )
    )


def fetch_bibliography(url, tags):
    """Fetch all requested entries before the installer changes any files."""
    tags = list(dict.fromkeys(tags))
    if not tags:
        return {}
    if not isinstance(url, str) or not url.startswith("https://"):
        raise RuntimeError("Set elib_url in chapters.json to the HTTPS elib.cgi URL.")
    request = Request(
        url,
        data=json.dumps(tags).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    def fetch():
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    try:
        # This POST only looks up bibliography records, so retrying is safe.
        payload = retry_http(fetch)
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise RuntimeError(
            f"ELIB: Failed to fetch bibliography from {url}: {error}"
        ) from error
    if not isinstance(payload, dict):
        raise RuntimeError("ELIB: Invalid bibliography response.")
    entries = payload.get("entries")
    missing = payload.get("missing")
    if (
        not isinstance(entries, dict)
        or not isinstance(missing, list)
        or any(not isinstance(tag, str) for tag in missing)
        or len(missing) != len(set(missing))
        or set(entries) & set(missing)
        or set(entries) | set(missing) != set(tags)
    ):
        raise RuntimeError("ELIB: Incomplete or invalid bibliography response.")
    if missing:
        raise RuntimeError("ELIB: Could not find references: " + ", ".join(missing))
    for tag, entry in entries.items():
        if not isinstance(entry, dict) or entry.get("bibtag") != tag:
            raise RuntimeError(f"ELIB: Invalid bibliography entry for {tag}.")
        # Validate renderability before writing any files; the renderer mutates its input.
        bibtex_entry_to_html(entry.copy())
    return entries


def get_file_as_string(filename):
    f = open(filename, "r")
    s = f.read()
    f.close()
    return s


def write_file_as_string(filename, s):
    global change_detected
    r = get_file_as_string(filename)
    if r != s:
        change_detected = True
        import difflib

        print(
            "".join(
                difflib.unified_diff(
                    r.splitlines(keepends=True), s.splitlines(keepends=True)
                )
            ),
            end="",
        )
        if not READ_ONLY:
            f = open(filename, "w")
            f.write(s)
            f.close()


def replace_string_before(s, before_str, with_str):
    r = with_str + s[s.find(before_str) :]
    return r


def replace_string_after(s, after_str, with_str):
    loc = s.find(after_str) + len(after_str)
    r = s[:loc] + with_str
    return r


def replace_string_between(s, start_str, end_str, with_str):
    index = 0
    while s.find(start_str, index) > 0:
        start = s.find(start_str, index) + len(start_str)
        end = s.find(end_str, start)
        s = s[:start] + with_str + s[end:]
        index = start + len(with_str)
    return s


def bibtex_field_to_html(text):
    # Function to process nested braces
    def process_braces(match):
        content = match.group(1)
        while "{" in content:
            content = re.sub(r"\{([^{}]*)\}", lambda m: m.group(1), content)
        return content

    # Remove outermost braces and process nested ones
    text = re.sub(r"\{([^{}]*)\}", process_braces, text)

    # Replace \& with &amp;
    text = text.replace(r"\&", "&amp;")

    # Replace accented characters
    accent_map = {
        r"\'e": "&eacute;",
        r"\'a": "&aacute;",
        r"\"o": "&ouml;",
        r"\"a": "&auml;",
        r"\'i": "&iacute;",
        r"\'o": "&oacute;",
        r"\'u": "&uacute;",
        r"\"u": "&uuml;",
        r"\`e": "&egrave;",
        r"\`a": "&agrave;",
        r"\^e": "&ecirc;",
        r"\^a": "&acirc;",
        r"\~n": "&ntilde;",
        r"\c{c}": "&ccedil;",
    }
    for latex, html in accent_map.items():
        text = text.replace(latex, html)

    # Replace other LaTeX special characters (extend as needed)
    latex_to_html = {
        r"\textbf{": "<strong>",
        r"\textit{": "<em>",
        r"}": "</strong></em>",  # Closing tag for both bold and italic
    }
    for latex, html in latex_to_html.items():
        text = text.replace(latex, html)

    return text


def bibtex_entry_to_html(entry):
    """Inspired by bibtex2html.py get_entry_output()"""
    # rip out whitespace
    for k, v in entry.items():
        if isinstance(v, str):
            entry[k] = v.strip().replace("\n", " ").replace("\r", "")

    # remove fields that are None
    entry = {k: v for k, v in entry.items() if v is not None and v != ""}

    def field(f):
        if f not in entry:
            raise RuntimeError(
                f"bibtex tag {entry['bibtag']} is missing" f" required field {f}"
            )
        if isinstance(entry[f], str):
            return bibtex_field_to_html(entry[f])
        return entry[f]

    out = ["\n<li id=%s>\n" % field("bibtag")]

    # --- author ---
    if "author" in entry:
        # TODO: Implement more complete bibtex name parsing/output:
        # https://nwalsh.com/tex/texhelp/bibtx-23.html
        authors = [
            " ".join(a.split(",")[::-1]).strip() for a in field("author").split(" and ")
        ]
        out.append('<span class="author">%s</span>, ' % " and ".join(authors))
        out.append("\n")

    if "chapter" in entry:
        # --- chapter ---
        out.append('<span class="title">"%s"</span>, ' % field("chapter"))
        out.append("in: %s, %s" % (field("title"), field("publisher")))
    else:
        # --- title ---
        out.append('<span class="title">"%s"</span>, ' % field("title"))

    if field("bibtype") == "book":
        out.append(field("publisher"))

    out.append("\n")

    # --- journal or similar ---
    if "journal" in entry:
        out.append('<span class="publisher">%s</span>' % field("journal"))
    elif "booktitle" in entry:
        out.append('<span class="publisher">')
        out.append(field("booktitle"))
        out.append("</span> ")
    elif "eprint" in entry:
        out.append('<span class="publisher">%s</span>' % field("eprint"))
    elif field("bibtype") == "phdthesis":
        out.append("PhD thesis, %s" % field("school"))
    elif field("bibtype") == "techreport":
        out.append("Tech. Report, %s" % field("number"))

    # --- volume, pages, notes etc ---
    #  print(entry)
    if "volume" in entry:
        out.append(", vol. %s" % field("volume"))
    if "number" in entry and field("bibtype") != "techreport":
        out.append(", no. %s" % field("number"))
    if "pages" in entry:
        out.append(", pp. %s" % field("pages"))
    if "month" in entry:
        out.append(", %s" % field("month"))

    # --- year ---
    out.append(', <span class="year">%s</span>' % field("year"))

    # final period
    out.append(".\n")

    # todo: add links
    elib_url = "http://groups.csail.mit.edu/robotics-center/public_papers/"
    if "url" in entry and field("isPublic"):
        if "http" not in entry["url"]:
            entry["url"] = elib_url + entry["url"]
        out.append(f'[&nbsp;<a href="{entry["url"]}">link</a>&nbsp;]\n')

    out.append("\n</li>")
    out.append("<br>")
    return "".join(out)


def write_references(elib, s, filename):
    global change_detected
    refs = reference_tags(s)

    if not refs:
        return s

    html = ""
    for r in refs:
        x = elib.get(r)
        if not x:
            print(f"ELIB: Could not find reference {r} referenced from {filename}")
            change_detected = True
            continue

        html += bibtex_entry_to_html(x.copy())

    html = f"<section><h1>References</h1>\n<ol>\n{html}" "\n</ol>\n</section><p/>\n"

    return replace_string_between(s, '<div id="references">', "</div>", html)


def uni(str):
    # All of this, to make sure that e.g. Poincar&eacute; Maps makes it through.
    return (
        str.encode("utf-8")
        .decode("utf-8")
        .encode("ascii", "xmlcharrefreplace")
        .decode("ascii")
    )


def _find_repo_root(start_dir: Path) -> Path:
    current = start_dir.resolve()
    while True:
        if (current / "pyproject.toml").is_file():
            return current
        if current.parent == current:
            raise RuntimeError("Could not find repository root")
        current = current.parent


def install_html_meta_data(
    *, check: bool = False, read_only: bool | None = None
) -> bool:
    global change_detected
    global READ_ONLY

    if read_only is not None:
        check = check or read_only

    root = _find_repo_root(Path(__file__).resolve().parent)
    book_dir = root / "book"
    original_cwd = Path.cwd()

    change_detected = False
    READ_ONLY = check

    os.chdir(book_dir)
    try:
        chapters = json.load(open("chapters.json"))
        chapter_ids = chapters["chapter_ids"]
        parts = chapters["parts"]

        tags = []
        for id in chapter_ids + chapters["draft_chapter_ids"]:
            tags.extend(reference_tags(get_file_as_string(id + ".html")))
        elib = fetch_bibliography(chapters.get("elib_url"), tags)

        # Build TOC
        toc = "\n<h1>Table of Contents</h1>\n"
        toc += "<ul>\n"
        toc += '  <li><a href="#preface">Preface</a></li>\n'

        chapter_num = 1
        appendix_start = 0
        for id in chapter_ids:
            filename = id + ".html"

            doc = parse(filename).getroot()
            chapter = next(doc.iter("chapter"))

            # Write the part if this chapter starts a new one.
            if id in parts:
                toc += (
                    '<p style="margin-bottom: 0; text-decoration: underline;'
                    + 'font-variant: small-caps;"><b>'
                    + uni(parts[id])
                    + "</b></p>\n"
                )
                if parts[id] == "Appendix":
                    appendix_start = chapter_num

            if appendix_start > 0:
                appendix_label = chr(ord("A") + chapter_num - appendix_start)
                toc += (
                    '  <li><a href="'
                    + filename
                    + '">Appendix '
                    + appendix_label
                    + ": "
                    + uni(chapter.find("h1").text)
                    + "</a></li>\n"
                )
            else:
                toc += (
                    '  <li><a href="'
                    + filename
                    + '">Chapter '
                    + str(chapter_num)
                    + ": "
                    + uni(chapter.find("h1").text)
                    + "</a></li>\n"
                )

            chapter_num += 1
            section_num = 1
            if chapter.find("section") is not None:
                toc += "  <ul>\n"
                for section in chapter.findall("section"):
                    hash = "section" + str(section_num)
                    if section.get("id") is not None:
                        hash = section.get("id")
                    toc += (
                        "    <li><a href="
                        + filename
                        + "#"
                        + hash
                        + ">"
                        + uni(section.find("h1").text)
                        + "</a></li>\n"
                    )
                    section_num += 1
                    if section.find("subsection") is not None:
                        toc += "    <ul>\n"
                        for subsection in section.findall("subsection"):
                            toc += (
                                "      <li>"
                                + uni(subsection.find("h1").text)
                                + "</li>\n"
                            )
                            if subsection.find("subsubsection") is not None:
                                toc += "      <ul>\n"
                                for subsubsection in subsection.findall(
                                    "subsubsection"
                                ):
                                    toc += (
                                        "        <li>"
                                        + uni(subsubsection.find("h1").text)
                                        + "</li>\n"
                                    )
                                toc += "      </ul>\n"
                        toc += "    </ul>\n"
                toc += "  </ul>\n"

        toc += "</ul>\n"

        s = get_file_as_string("index.html")
        s = replace_string_between(
            s, '<section id="table_of_contents">', "</section>", toc
        )
        write_file_as_string("index.html", s)

        # Write common headers / footers
        header = get_file_as_string("header.html.in")
        footer = get_file_as_string("footer.html.in")

        chapter_num = 1
        for id in chapter_ids:
            filename = id + ".html"
            s = get_file_as_string(filename)

            # Extract the chapter title
            name_start = s.find("<chapter")
            name_start = s.find("<h1>", name_start) + len("<h1>")
            name_end = s.find("</h1>", name_start)
            name = s[name_start:name_end]

            # Rewrite the header
            this_header = header.replace("$CHAPTER-ID$", id)
            this_header = this_header.replace("$CHAPTER-NAME$", name)
            this_header = this_header.replace("$CHAPTER-NUM$", str(chapter_num))
            s = replace_string_before(s, "<chapter", this_header)

            # Rewrite the footer
            s = replace_string_after(s, "</chapter>", footer)

            # Update the chapter number
            if appendix_start > 0 and chapter_num >= appendix_start:
                s = replace_string_between(
                    s,
                    "<chapter",
                    ">",
                    ' class="appendix" style="counter-reset: chapter '
                    + str(chapter_num - appendix_start)
                    + '"',
                )
            else:
                s = replace_string_between(
                    s,
                    "<chapter",
                    ">",
                    ' style="counter-reset: chapter ' + str(chapter_num - 1) + '"',
                )

            # Write previous and next chapter logic
            if chapter_num > 1:
                s = replace_string_between(
                    s,
                    '<a class="previous_chapter"',
                    "</a>",
                    " href=" + chapter_ids[chapter_num - 2] + ".html>Previous Chapter",
                )
            if chapter_num < len(chapter_ids):
                s = replace_string_between(
                    s,
                    '<a class="next_chapter"',
                    "</a>",
                    " href=" + chapter_ids[chapter_num] + ".html>Next Chapter",
                )

            # Write references
            s = write_references(elib, s, filename)

            write_file_as_string(filename, s)

            chapter_num += 1

        for id in chapters["draft_chapter_ids"]:
            filename = id + ".html"
            s = get_file_as_string(filename)

            # Extract the chapter title
            name_start = s.find("<chapter")
            name_start = s.find("<h1>", name_start) + len("<h1>")
            name_end = s.find("</h1>", name_start)
            name = s[name_start:name_end]

            # Rewrite the header
            this_header = header.replace("$CHAPTER-ID$", id)
            this_header = this_header.replace("$CHAPTER-NAME$", name)
            this_header = this_header.replace("$CHAPTER-NUM$", "DRAFT")
            s = replace_string_before(s, "<chapter", this_header)

            # Rewrite the footer
            s = replace_string_after(s, "</chapter>", footer)

            # Update the chapter number
            s = replace_string_between(
                s, "<chapter", ">", ' style="counter-reset: chapter 100"'
            )

            # Write references
            s = write_references(elib, s, filename)

            write_file_as_string(filename, s)
    finally:
        os.chdir(original_cwd)

    if check and change_detected:
        print(
            "This script would have made changes. You may need to run "
            "'python3 htmlbook/install_html_meta_data.py' from the book "
            "directory."
        )

    return change_detected


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Install ToC and Navigation into book html files."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Do not write changes; fail if updates would be made.",
    )
    # Backward-compatible alias.
    parser.add_argument("--read_only", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    check_mode = args.check or args.read_only
    return int(install_html_meta_data(check=check_mode))


if __name__ == "__main__":
    raise SystemExit(main())

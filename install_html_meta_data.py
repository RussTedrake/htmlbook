import argparse
from lxml.html import parse
import json
import mysql.connector

chapters = json.load(open("chapters.json"))
chapter_ids = chapters['chapter_ids']
parts = chapters['parts']

change_detected = False

parser = argparse.ArgumentParser(
    description='Install ToC and Navigation into book html files.')
parser.add_argument('--read_only', action='store_true')
args = parser.parse_args()


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
        print(''.join(
            difflib.unified_diff(r.splitlines(keepends=True),
                                 s.splitlines(keepends=True))),
              end="")
        if not args.read_only:
            f = open(filename, "w")
            f.write(s)
            f.close()


def replace_string_before(s, before_str, with_str):
    r = with_str + s[s.find(before_str):]
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


def bibtex_entry_to_html(entry):
    """Inspired by bibtex2html.py get_entry_output()"""
    # rip out whitespace
    for k, v in entry.items():
        if isinstance(v, str):
            entry[k] = v.strip().replace("\n", " ").replace("\r", "")

    # remove fields that are None
    entry = {k: v for k, v in entry.items() if v is not None and v != ''}

    def field(f):
        if f not in entry:
            raise RuntimeError(f"bibtex tag {entry['bibtag']} is missing"
                               f" required field {f}")
        return entry[f]

    out = ['\n<li id=%s>\n' % field('bibtag')]

    # --- author ---
    if 'author' in entry:
        # TODO: Implement more complete bibtex name parsing/output:
        # https://nwalsh.com/tex/texhelp/bibtx-23.html
        authors = [
            ' '.join(a.split(',')[::-1]).strip()
            for a in field('author').split(' and ')
        ]
        out.append('<span class="author">%s</span>, ' % ' and '.join(authors))
        out.append('\n')

    if 'chapter' in entry:
        # --- chapter ---
        out.append('<span class="title">"%s"</span>, ' % field('chapter'))
        out.append('in: %s, %s' % (field('title'), field('publisher')))
    else:
        # --- title ---
        out.append('<span class="title">"%s"</span>, ' % field('title'))

    if field('bibtype') == 'book':
        out.append(field('publisher'))

    out.append('\n')

    # --- journal or similar ---
    if 'journal' in entry:
        out.append('<span class="publisher">%s</span>' % field('journal'))
    elif 'booktitle' in entry:
        out.append('<span class="publisher">')
        out.append(field('booktitle'))
        out.append('</span> ')
    elif 'eprint' in entry:
        out.append('<span class="publisher">%s</span>' % field('eprint'))
    elif field('bibtype') == 'phdthesis':
        out.append('PhD thesis, %s' % field('school'))
    elif field('bibtype') == 'techreport':
        out.append('Tech. Report, %s' % field('number'))

    # --- volume, pages, notes etc ---
    #  print(entry)
    if 'volume' in entry:
        out.append(', vol. %s' % field('volume'))
    if 'number' in entry and field('bibtype') != 'techreport':
        out.append(', no. %s' % field('number'))
    if 'pages' in entry:
        out.append(', pp. %s' % field('pages'))
    if 'month' in entry:
        out.append(', %s' % field('month'))

    # --- year ---
    out.append(', <span class="year">%s</span>' % field('year'))

    # final period
    out.append('.\n')

    # todo: add links
    elib_url = 'http://groups.csail.mit.edu/robotics-center/public_papers/'
    if 'url' in entry and field('isPublic'):
        if 'http' not in entry['url']:
            entry['url'] = elib_url + entry['url']
        out.append(f'[&nbsp;<a href="{entry["url"]}">link</a>&nbsp;]\n')

    out.append('\n</li>')
    out.append('<br>')
    return ''.join(out)


def write_references(elib, s, filename):
    global change_detected
    index = 0
    refs = []
    while s.find("<elib", index) > 0:
        start = s.find("<elib", index)
        start = s.find(">", start) + 1
        end = s.find("</elib>", start)
        refs += s[start:end].split("+")
        index = end + len("</elib>")

    if not refs:
        return s

    refs = map(str.strip, refs)  # Strip whitespace
    refs = list(dict.fromkeys(refs))  # Remove duplicates (preserving order)

    html = ''
    for r in refs:
        elib.execute(f"SELECT * FROM bibtex WHERE bibtag = '{r}'")
        x = elib.fetchone()
        if not x:
            print(
                f"ELIB: Could not find reference {r} referenced from {filename}"
            )
            change_detected = True
            continue

        html += bibtex_entry_to_html(x)

    html = (f"<section><h1>References</h1>\n<ol>\n{html}"
            "\n</ol>\n</section><p/>\n")

    return replace_string_between(s, '<div id="references">', '</div>', html)


def uni(str):
    # All of this, to make sure that e.g. Poincar&eacute; Maps makes it through.
    return str.encode('utf-8').decode('utf-8').encode(
        'ascii', 'xmlcharrefreplace').decode('ascii')


# Build TOC
toc = "\n<h1>Table of Contents</h1>\n"
toc += "<ul>\n"
toc += '  <li><a href="#preface">Preface</a></li>\n'

chapter_num = 1
appendix_start = 0
for id in chapter_ids:
    filename = id + ".html"

    # parser = etree.HTMLParser(encoding='utf-8')
    # doc = parse(filename, parser=parser).getroot()
    doc = parse(filename).getroot()
    chapter = next(doc.iter('chapter'))

    # Write the part if this chapter starts a new one.
    if id in parts:
        toc += ('<p style="margin-bottom: 0; text-decoration: underline;'
                + 'font-variant: small-caps;"><b>' + uni(parts[id])
                + '</b></p>\n')
        if parts[id] == 'Appendix':
            appendix_start = chapter_num

    if appendix_start > 0:
        appendix_label = chr(ord('A') + chapter_num - appendix_start)
        toc += ('  <li><a href="' + filename + '">Appendix ' + appendix_label
                + ': ' + uni(chapter.find('h1').text) + '</a></li>\n')
    else:
        toc += ('  <li><a href="' + filename + '">Chapter ' + str(chapter_num)
                + ': ' + uni(chapter.find('h1').text) + '</a></li>\n')

    chapter_num += 1
    section_num = 1
    if chapter.find('section') is not None:
        toc += '  <ul>\n'
        for section in chapter.findall('section'):
            hash = "section" + str(section_num)
            if section.get('id') is not None:
                hash = section.get('id')
            toc += ('    <li><a href=' + filename + '#' + hash + ">"
                    + uni(section.find('h1').text) + '</a></li>\n')
            section_num += 1
            if section.find('subsection') is not None:
                toc += '    <ul>\n'
                for subsection in section.findall('subsection'):
                    toc += ('      <li>' + uni(subsection.find('h1').text)
                            + '</li>\n')
                toc += '    </ul>\n'
        toc += '  </ul>\n'

toc += '</ul>\n'

s = get_file_as_string("index.html")
s = replace_string_between(s, '<section id="table_of_contents">', '</section>',
                           toc)
write_file_as_string("index.html", s)

elib_connector = mysql.connector.connect(host="mysql.csail.mit.edu",
                                         user="elibuser",
                                         password="readonly678",
                                         database="elib")
elib = elib_connector.cursor(dictionary=True)

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
            s, "<chapter", ">",
            ' class="appendix" style="counter-reset: chapter '
            + str(chapter_num - appendix_start) + '"')
    else:
        s = replace_string_between(
            s, "<chapter", ">",
            ' style="counter-reset: chapter ' + str(chapter_num - 1) + '"')

    # Write previous and next chapter logic
    if chapter_num > 1:
        s = replace_string_between(
            s, '<a class="previous_chapter"', '</a>',
            ' href=' + chapter_ids[chapter_num - 2] + '.html>Previous Chapter')
    if chapter_num < len(chapter_ids):
        s = replace_string_between(
            s, '<a class="next_chapter"', '</a>',
            ' href=' + chapter_ids[chapter_num] + '.html>Next Chapter')

    # Write references
    s = write_references(elib, s, filename)

    write_file_as_string(filename, s)

    chapter_num += 1

if args.read_only and change_detected:
    print("This script would have made changes. You may need to run "
          "'python3 htmlbook/install_html_meta_data.py' from the root "
          "directory.")

exit(change_detected)

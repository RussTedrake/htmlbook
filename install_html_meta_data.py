import argparse
from lxml.html import parse, etree
import json

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


# Build TOC
toc = "\n<h1>Table of Contents</h1>\n"
toc += "<ul>\n"
toc += '  <li><a href="#preface">Preface</a></li>\n'

chapter_num = 1
appendix_start = 0
for id in chapter_ids:
    filename = id + ".html"

    doc = parse(filename).getroot()
    chapter = next(doc.iter('chapter'))

    # Write the part if this chapter starts a new one.
    if id in parts:
        toc += ('<p style="margin-bottom: 0; text-decoration: underline;' +
                'font-variant: small-caps;"><b>' + parts[id] + '</b></p>\n')
        if parts[id] == 'Appendix':
            appendix_start = chapter_num

    if appendix_start > 0:
        appendix_label = chr(ord('A') + chapter_num - appendix_start)
        toc += ('  <li><a href="' + filename + '">Appendix ' + appendix_label +
                ': ' + chapter.find('h1').text + '</a></li>\n')
    else:
        toc += ('  <li><a href="' + filename + '">Chapter ' + str(chapter_num) +
                ': ' + chapter.find('h1').text + '</a></li>\n')

    chapter_num += 1
    section_num = 1
    if chapter.find('section') is not None:
        toc += '  <ul>\n'
        for section in chapter.findall('section'):
            hash = "section" + str(section_num)
            if section.get('id') is not None:
                hash = section.get('id')
            toc += ('    <li><a href=' + filename + '#' + hash + ">" +
                    section.find('h1').text + '</a></li>\n')
            section_num += 1
            if section.find('subsection') is not None:
                toc += '    <ul>\n'
                for subsection in section.findall('subsection'):
                    toc += '      <li>' + subsection.find('h1').text + '</li>\n'
                toc += '    </ul>\n'
        toc += '  </ul>\n'

toc += '</ul>\n'

s = get_file_as_string("index.html")
s = replace_string_between(s, '<section id="table_of_contents">', '</section>',
                           toc)
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
    s = replace_string_before(s, "<chapter", this_header)

    # Rewrite the footer
    s = replace_string_after(s, "</chapter>", footer)

    # Update the chapter number
    if appendix_start > 0 and chapter_num >= appendix_start:
        s = replace_string_between(
            s, "<chapter", ">",
            ' class="appendix" style="counter-reset: chapter ' +
            str(chapter_num - appendix_start) + '"')
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

    write_file_as_string(filename, s)

    chapter_num += 1

if args.read_only and change_detected:
    print("This script would have made changes. You may need to run "
          "'python3 htmlbook/install_html_meta_data.py' from the root "
          "directory.")

exit(change_detected)

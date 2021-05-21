import argparse
#import glob
import os
import re

import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote

parser = argparse.ArgumentParser(description='Checks my html file links.')
# Add a workspace argument to support non-hermetic testing through `bazel test`.
parser.add_argument('--cwd',
                    default=os.path.dirname(os.path.abspath(__file__)),
                    help='Execute using this current working directory')
parser.add_argument('files', nargs='+')
args = parser.parse_args()

# Find workspace root by searching parent directories.
os.chdir(args.cwd)
while not os.path.isfile('WORKSPACE.bazel'):
    os.chdir(os.path.dirname(os.getcwd()))


def get_file_as_string(filename):
    f = open(filename, "r")
    s = f.read()
    f.close()
    return s


def getLinksFromHTML(html):

    def getLink(el):
        return el["href"]

    return list(
        map(getLink,
            BeautifulSoup(html, features="html.parser").select("a[href]")))


def html_has_id(html, id):
    id = unquote(id)
    tag = BeautifulSoup(html, features="html.parser").find(id=id)
    return tag is not None


# Check that all links to code files exist.
for filename in args.files:
    s = get_file_as_string(filename)

    broken_links = []

    for link in []: #getLinksFromHTML(s):
        link = link.strip()
        # print(link)  # useful for debugging.
        if '#' in link:
            url, id = link.split(sep='#', maxsplit=1)
        else:
            url = link
            id = ''
        if len(url) == 0:
            if not html_has_id(s, id):
                broken_links.append(link)
        elif url[:4].lower() != 'http':
            if url[:4].lower() == 'data' and os.environ.get('GITHUB_ACTIONS'):
                # Don't require the data directory on CI.  
                # See https://github.com/RussTedrake/htmlbook/issues/10
                continue
            if not os.path.exists(url):
                broken_links.append(link)
            # The index is the only case where I want to allow section tags.
            if filename == 'index.html' and id[:7] == "section":
                continue
            if id and not html_has_id(get_file_as_string(url), id):
                broken_links.append(link)
        elif url.find("colab.research.google.com") != -1:
            try:
                requestObj = requests.head(link)
            except requests.ConnectionError:
                broken_links.append(link)

            if requestObj.status_code == 404:
                broken_links.append(link)
        else:
            if id:
                requestObj = requests.get(link)
                if requestObj.status_code == 404:
                    broken_links.append(link)
                if not html_has_id(requestObj.text, id):
                    broken_links.append(link)
            else:
                try:
                    requestObj = requests.head(link)
                except requests.ConnectionError as err:
                    broken_links.append(link)
                    print(err)

                if requestObj.status_code == 404:
                    broken_links.append(link)

    if broken_links:
        print(f"{filename} has the following broken links:")
        print("\n".join(broken_links))
        exit(-2)

    for tag in ['jupyter', 'pysrcinclude', 'pysrc']:
        index = 0
        while s.find('<' + tag + '>', index) > 0:
            start = s.find('<' + tag + '>', index) + len(tag) + 2
            end = s.find('</' + tag + '>', start)
            index = end + len(tag) + 3
            file = s[start:end]
            if not os.path.exists(file):
                print(filename + " tries to link to the source file " + file
                      + " which doesn't exist")
                exit(-2)

    print("checking for ref")
    for ref in re.finditer('\\\\ref{(.*?)}', s):
        tag = ref[1] # match from inside of braces
        if "\label{" + tag + "}" not in s:
            print(f"Cannot find label matching latex reference {ref[0]}")
            exit(-2)

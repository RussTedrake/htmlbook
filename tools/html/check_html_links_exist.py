import argparse
import os
import re
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(description="Checks my html file links.")
# Add a workspace argument to support non-hermetic testing through `bazel test`.
parser.add_argument(
    "--cwd",
    default=os.path.dirname(os.path.abspath(__file__)),
    help="Execute using this current working directory",
)
parser.add_argument("files", nargs="+")
args = parser.parse_args()

# Find workspace root by searching parent directories.
os.chdir(args.cwd)
while not os.path.isfile("WORKSPACE.bazel"):
    assert os.path.dirname(os.getcwd()) != os.getcwd(), "could not find WORKSPACE.bazel"
    os.chdir(os.path.dirname(os.getcwd()))

repository = os.path.basename(os.getcwd())
repository_url = f"https://{repository}.csail.mit.edu/"

ignore_list = [
    "sr.stanford.edu",
    "www.robotics.tu-berlin.de",
    "colab.research.google.com",
    "accessibility.mit.edu",
]


def get_file_as_string(filename):
    f = open(filename, "r")
    s = f.read()
    f.close()
    return s


def getLinksFromString(s, extension):
    if extension.lower() == ".ipynb":
        links = re.findall(r"\((\s*http.*?)\)", s)
        return links

    else:

        def getLink(el):
            return el["href"]

        return list(
            map(
                getLink,
                BeautifulSoup(s, features="html.parser").select("a[href]"),
            )
        )


def html_has_id(html, id):
    if html.find("github.com") != 1:
        ## We aren't going to find e.g. #L55 in the html source.
        return True
    id = unquote(id)
    tag = BeautifulSoup(html, features="html.parser").find(id=id)
    return tag is not None


# Check that all links to code files exist.
for filename in args.files:
    extension = Path(filename).suffix
    s = get_file_as_string(filename)

    broken_links = []

    for link in getLinksFromString(s, extension):
        link = link.strip()
        if link[: len(repository_url)] == repository_url:
            link = link[len(repository_url) :]
        if "#" in link:
            url, id = link.split(sep="#", maxsplit=1)
        else:
            url = link
            id = ""
        # print(f"url={url}, id={id}", flush=True)  # useful for debugging.

        if len(url) == 0:
            if not html_has_id(s, id):
                broken_links.append(link)
        elif url[:4].lower() != "http":
            if url[:4].lower() == "data" and os.environ.get("GITHUB_ACTIONS"):
                # Don't require the data directory on CI.
                # See https://github.com/RussTedrake/htmlbook/issues/10
                continue
            if url[:6] == "Spring" or url[:4] == "Fall":
                # ignore e.g. https://underactuated.csail.mit.edu/Spring2023/ .
                continue
            # All local content should be in the book
            url = "book/" + url
            if not os.path.exists(url):
                print(f"couldn't find local file {url} in {os.getcwd()}")
                broken_links.append(link)
            # The index is the only case where I want to allow section tags.
            if filename == "index.html" and id[:7] == "section":
                continue
            if id and not html_has_id(get_file_as_string(url), id):
                broken_links.append(link)
        elif any(s in url for s in ignore_list):
            continue
        elif not os.environ.get("GITHUB_ACTIONS"):
            # otherwise there is way too much noise on CI
            try:
                if id:
                    requestObj = requests.get(link, timeout=20)
                else:
                    requestObj = requests.head(link, timeout=20)
                if (
                    requestObj.status_code == 403
                    or requestObj.status_code == 406
                    or requestObj.status_code == 418
                    or requestObj.status_code == 429
                    or requestObj.status_code == 503
                ):
                    continue
                if not requestObj.ok:
                    print(requestObj)
                    broken_links.append(link)
                if id and not html_has_id(requestObj.text, id):
                    print(requestObj)
                    broken_links.append(link)
            except Exception as err:
                broken_links.append(link)
                print(err)

    if broken_links:
        print(f"Found the following broken links:")
        for link in broken_links:
            line = s.count("\n", 0, s.find(link))
            print(f"{link} in {filename}:{line+1}\n")
        exit(-2)

    for tag in ["jupyter", "pysrcinclude", "pysrc"]:
        index = 0
        while s.find("<" + tag + ">", index) > 0:
            start = s.find("<" + tag + ">", index) + len(tag) + 2
            end = s.find("</" + tag + ">", start)
            index = end + len(tag) + 3
            file = "book/" + s[start:end]
            if not os.path.exists(file):
                print(
                    filename
                    + " tries to link to the source file "
                    + file
                    + " which doesn't exist"
                )
                exit(-2)

    for ref in re.finditer("\\\\ref{(.*?)}", s):
        tag = ref[1]  # match from inside of braces
        if "\\label{" + tag + "}" not in s:
            print(f"Cannot find label matching latex reference {ref[0]}")
            exit(-2)

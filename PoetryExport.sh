#!/bin/bash

poetry lock
poetry export --without-hashes --with dev > requirements.txt
# Remove poetry. Required to work around poetry <--> poetry-plugin-export circular
# dependency: https://github.com/python-poetry/poetry-plugin-export/issues/240
sed '/^poetry/d' requirements.txt > requirements.txt.tmp && mv requirements.txt.tmp requirements.txt
# Work around poetry issue: https://github.com/python-poetry/poetry-plugin-export/issues/176
sed -E 's/matplotlib==[0-9]+\.[0-9]+\.[0-9]+ ; python_version >= "3.10"/matplotlib==3.5.1 ; sys_platform == "linux"\
matplotlib==3.7.3 ; sys_platform == "darwin"/' requirements.txt > requirements.txt.tmp && mv requirements.txt.tmp requirements.txt
# Force torch to be cpu-only for bazel. https://drakedevelopers.slack.com/archives/C2PMBJVAN/p1697855405335329
awk '
/torch==[0-9]+\.[0-9]+\.[0-9]+ ; python_version >= "3.10"/ {
    version=$1; sub(/^torch==/, "", version); sub(/ ;.*/, "", version);
    print "--find-links https://download.pytorch.org/whl/torch_stable.html";
    print "torch==" version "+cpu ; python_version >= \"3.10\" and sys_platform == \"linux\"";
    print "torch==" version " ; python_version >= \"3.10\" and sys_platform == \"darwin\"";
    next;
}
1' requirements.txt > requirements-bazel.txt

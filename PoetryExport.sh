#!/bin/bash

# For bazel
poetry export --without-hashes --with dev --all-extras > requirements.txt
# Remove poetry. Required to work around poetry <--> poetry-plugin-export circular
# dependency: https://github.com/python-poetry/poetry-plugin-export/issues/240
# Note that pip_parse does provide a mechanism for handling known cycles:
# https://github.com/bazelbuild/rules_python/blob/9a1a524cb0f9c048fbd0abc9837d4a757d98b9c5/examples/pip_parse/WORKSPACE#L27
sed '/^poetry/d' requirements.txt > requirements.txt.tmp && mv requirements.txt.tmp requirements.txt
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
awk '
/torchvision==[0-9]+\.[0-9]+\.[0-9]+ ; python_version >= "3.10" and python_version < "4.0"/ {
    version=$1; sub(/^torchvision==/, "", version); sub(/ ;.*/, "", version);
    print "--find-links https://download.pytorch.org/whl/torch_stable.html";
    print "torchvision==" version "+cpu ; python_version >= \"3.10\" and sys_platform == \"linux\"";
    print "torchvision==" version " ; python_version >= \"3.10\" and sys_platform == \"darwin\"";
    next;
}
1' requirements-bazel.txt > requirements-bazel.txt.tmp && mv requirements-bazel.txt.tmp requirements-bazel.txt
# Embarassingly, pip_parse does not support markers, so we need to split the
# requirements into separate files.
# https://github.com/bazelbuild/rules_python/issues/1105
awk '/sys_platform == "darwin"/ || !/sys_platform/' requirements-bazel.txt > requirements-bazel-mac.txt
awk '/sys_platform == "linux"/ || !/sys_platform/' requirements-bazel.txt > requirements-bazel-linux.txt

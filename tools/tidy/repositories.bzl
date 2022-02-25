# -*- mode: python -*-
# vi: set ft=python :

# Copyright 2020 Massachusetts Institute of Technology.
# Licensed under the BSD 3-Clause License. See LICENSE.TXT for details.

load("@bazel_tools//tools/build_defs/repo:utils.bzl", "maybe")
load("//htmlbook/tools/repo:local.bzl", "local_file")

def tidy_dependencies():
    maybe(
        local_file,
        name = "tidy_linux",
        path = "/usr/bin/tidy",
        symlinked_file_path = "tidy",
    )

    maybe(
        local_file,
        name = "tidy_macos_i386",
        path = "/usr/local/bin/tidy",
        symlinked_file_path = "tidy",
    )

    maybe(
        local_file,
        name = "tidy_macos_arm64",
        path = "/opt/homebrew/bin/tidy",
        symlinked_file_path = "tidy",
    )

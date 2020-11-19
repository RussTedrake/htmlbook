# -*- mode: python -*-
# vi: set ft=python :

# Copyright 2020 Massachusetts Institute of Technology.
# Licensed under the BSD 3-Clause License. See LICENSE.TXT for details.

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@bazel_tools//tools/build_defs/repo:utils.bzl", "maybe")

def rt_dependencies():
    maybe(
        http_archive,
        "bazel_skylib",
        urls = [
            "https://mirror.bazel.build/github.com/bazelbuild/bazel-skylib/releases/download/1.0.2/bazel-skylib-1.0.2.tar.gz",
            "https://github.com/bazelbuild/bazel-skylib/releases/download/1.0.2/bazel-skylib-1.0.2.tar.gz",
        ],
        sha256 = "97e70364e9249702246c0e9444bccdc4b847bed1eb03c5a3ece4f83dfe6abc44",
    )

    maybe(
        http_archive,
        "rules_python",
        sha256 = "48f7e716f4098b85296ad93f5a133baf712968c13fbc2fdf3a6136158fe86eac",
        strip_prefix = "rules_python-0.1.0",
        url = "https://github.com/bazelbuild/rules_python/archive/0.1.0.tar.gz",
    )

def rt_toolchains():
    native.register_toolchains(
        "//htmlbook/tools/python:linux_toolchain",
        "//htmlbook/tools/python:macos_toolchain",
    )

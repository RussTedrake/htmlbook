# -*- mode: python -*-
# vi: set ft=python :

# Copyright 2020 Massachusetts Institute of Technology.
# Licensed under the BSD 3-Clause License. See LICENSE.TXT for details.

load("@pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_test")

def rt_check_links_test(**attrs):
    if "data" not in attrs:
        attrs["data"] = []
    py_test(
        name = attrs["srcs"][0] + "_linktest",
        srcs = [
          "//book/htmlbook/tools/html:check_html_links_exist",
        ],
        main = "check_html_links_exist.py",
        args = ["$(location " + attrs["srcs"][0] + ")"],
        data = attrs["srcs"] + attrs["data"] + [
          "//book:html",
          "//:workspace",
        ],
        tags = ["no-sandbox"],  # to allow network connections
        deps = [
          requirement("requests"),
          requirement("beautifulsoup4"),
        ],
        visibility = ["//visibility:private"],
    )

def rt_html_test(**attrs):
    if "size" not in attrs or attrs["size"] == None:
        attrs["size"] = "medium"
    if "timeout" not in attrs or attrs["timeout"] == None:
        attrs["timeout"] = "short"
    rt_check_links_test(**attrs)

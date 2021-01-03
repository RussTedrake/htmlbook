# -*- mode: python -*-
# vi: set ft=python :

# Copyright 2020 Massachusetts Institute of Technology.
# Licensed under the BSD 3-Clause License. See LICENSE.TXT for details.

load("@pip//:requirements.bzl", "all_requirements")
load("@rules_python//python:defs.bzl", "py_test")

def rt_check_links_test(**attrs):
    py_test(
        name = attrs["srcs"][0] + "_linktest",
        srcs = ["//htmlbook/tools/html:check_html_links_exist"],
        main = "check_html_links_exist.py",
        args = ["$(location " + attrs["srcs"][0] + ")"],
        data = attrs["srcs"],
        tags = ["no-sandbox"],  # to allow network connections
#    args = [
#        "--cwd",
#        PWD,
#    ], 
        deps = all_requirements,
        visibility = ["//visibility:private"],
    )

def rt_html_test(**attrs):
    if "size" not in attrs or attrs["size"] == None:
        attrs["size"] = "medium"
    if "timeout" not in attrs or attrs["timeout"] == None:
        attrs["timeout"] = "short"
    rt_check_links_test(**attrs)

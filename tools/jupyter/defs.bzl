# -*- mode: python -*-
# vi: set ft=python :

# Copyright 2020 Massachusetts Institute of Technology.
# Licensed under the BSD 3-Clause License. See LICENSE.TXT for details.

load("@rules_python//python:defs.bzl", "py_test")
load("//htmlbook/tools/python:defs.bzl", "rt_py_binary", "rt_py_test")
load("//htmlbook/tools/html:defs.bzl", "rt_check_links_test")

def _nbconvert(attrs, testonly = False):
    out = "{}.ipynb.py".format(attrs["name"])
    grader_throws = ""
    if "grader_throws" in attrs:
      grader_throws = "1"
      attrs.pop("grader_throws")
    native.genrule(
        name = "{}_nbconvert".format(attrs["name"]),
        testonly = testonly,
        srcs = attrs["srcs"],
        outs = [out],
        cmd = "$(location //htmlbook/tools/jupyter:nbconvert) $< " + grader_throws + " > $@",
        tools = ["//htmlbook/tools/jupyter:nbconvert"],
        visibility = ["//visibility:private"],
    )
    attrs["main"] = out
    attrs["srcs"] = [out]
    return _common_attrs(attrs)

def _common_attrs(attrs):
    # TODO(jamiesnape): Enable pycodestyle for ipynb.
#    attrs["pycodestyle"] = False
#    attrs["pydocstyle"] = False
#    attrs["yapf"] = False
    if "tags" in attrs and attrs["tags"] != None:
        attrs["tags"] = attrs["tags"] + ["ipynb"]
    else:
        attrs["tags"] = ["ipynb"]
    return attrs

def rt_ipynb_output_test(**attrs):
    py_test(
        name = attrs["name"] + "_output",
        srcs = ["//htmlbook/tools/jupyter:ipynb_output"],
        main = "ipynb_output.py",
        args = ["$(location " + attrs["srcs"][0] + ")"],
        data = attrs["srcs"],
        visibility = ["//visibility:private"],
    )

def rt_ipynb_binary(**attrs):
    if "ipynboutput" not in attrs or attrs["ipynboutput"]:
        rt_ipynb_output_test(**attrs)
    rt_py_binary(**_nbconvert(attrs, testonly = attrs.get("testonly", False)))

def rt_ipynb_test(**attrs):
    if "size" not in attrs or attrs["size"] == None:
        attrs["size"] = "medium"
    if "timeout" not in attrs or attrs["timeout"] == None:
        attrs["timeout"] = "short"
    if "ipynboutput" not in attrs or attrs["ipynboutput"]:
        rt_ipynb_output_test(**attrs) 
    rt_check_links_test(**attrs)
    rt_py_test(**_nbconvert(attrs, testonly = attrs.get("testonly", True)))

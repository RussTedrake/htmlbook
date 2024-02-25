# -*- mode: python -*-
# vi: set ft=python :

# Copyright 2020 Massachusetts Institute of Technology.
# Licensed under the BSD 3-Clause License. See LICENSE.TXT for details.

load("@pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary", "py_library", "py_test")

def _common_attrs(attrs):
    if "data" not in attrs or attrs["data"] == None:
        attrs["data"] = []
    attrs["data"] = attrs["data"] + ["@drake_models"]        
    if "deps" not in attrs or attrs["deps"] == None:
        attrs["deps"] = []
    attrs["srcs_version"] = "PY3"
    if "tags" in attrs and attrs["tags"] != None:
        if ("block-network" not in attrs["tags"] and
            "requires-network" not in attrs["tags"]):
            attrs["tags"] = attrs["tags"] + ["block-network"]
    else:
        attrs["tags"] = ["block-network"]
    return attrs

def _binary_attrs(attrs):
    attrs["legacy_create_init"] = False
    attrs["python_version"] = "PY3"
    return _common_attrs(attrs)

def _style_test_attrs(attrs):
    if "config" not in attrs or attrs["config"] == None:
        attrs["config"] = "//:setup.cfg"
    if "size" not in attrs or attrs["size"] == None:
        attrs["size"] = "small"
    return attrs

def _test_attrs(attrs):
    if "size" not in attrs or attrs["size"] == None:
        attrs["size"] = "small"
    return _binary_attrs(attrs)

def rt_py_binary(**attrs):
    py_binary(**_binary_attrs(attrs))

def rt_py_library(**attrs):
    py_library(**_common_attrs(attrs))

def rt_py_test(**attrs):
    attrs["deps"] = select({
        "//book/htmlbook/tools/python:installed_deps_true": [],
        "//conditions:default": attrs.get("deps", [])
    })
    py_test(**_test_attrs(attrs))

"""Pytest wrapper: run check_website logic (Bazel rt_py_test, needs network)."""
from book.htmlbook.check_website import test_website_up


def test_website_up_wrapper():
    test_website_up()

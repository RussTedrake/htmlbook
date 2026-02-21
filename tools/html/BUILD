python_sources(
    name="html_tools",
    dependencies=["//:reqs#requests", "//:reqs#beautifulsoup4"],
)

python_tests(
    name="link_check_test",
    dependencies=[
        ":html_tools",
        "//book:html",
        "//:reqs#beautifulsoup4",
        "//:reqs#requests",
    ],
    overrides={
        "test_link_check.py": {"timeout": 180},
    },
)

python_sources(
    name="htmlbook",
    dependencies=["//:reqs#lxml", "//:reqs#mysql-connector-python"],
)

# Scripts that are run as tests (exit 0 = pass). Wrappers run them via subprocess.
python_tests(
    name="htmlbook_tests",
    dependencies=[
        ":htmlbook",
        "//:reqs#lxml",
        "//:reqs#mysql-connector-python",
        "//:reqs#requests",
    ],
    overrides={
        "test_install_html_meta_data.py": {"timeout": 60},
        "test_check_deepnote_requirements.py": {"timeout": 30, "extra_env_vars": ["NETWORK"]},
        "test_check_website.py": {"timeout": 30, "extra_env_vars": ["NETWORK"]},
    },
)

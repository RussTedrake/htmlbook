# Tidy test: run tidy on all book/*.html. Requires system 'tidy' (e.g. brew install tidy-html5).
python_test(
    name="tidy_test",
    source="run_tidy.py",
    dependencies=["//book:html"],
    timeout=120,
)

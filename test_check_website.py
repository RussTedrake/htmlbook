import requests
from htmlbook.book_name import get_project_name


def test_website_up() -> None:
    url = f"http://{get_project_name()}.mit.edu/python/index.html"
    response = requests.get(url, timeout=30)
    assert (
        response.status_code == 200
    ), f"Website {url} returned status code {response.status_code}"

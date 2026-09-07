from urllib.request import urlopen

from htmlbook.book_name import get_project_name
from htmlbook.http_retry import retry_http


def test_website_up() -> None:
    url = f"https://{get_project_name()}.mit.edu/python/index.html"

    def check():
        with urlopen(url, timeout=30) as response:
            assert (
                response.status == 200
            ), f"Website {url} returned status code {response.status}"

    retry_http(check)

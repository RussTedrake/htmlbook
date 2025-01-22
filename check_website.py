import requests
from book_name import get_project_name

def test_website_up():
    url = f"http://{get_project_name()}.mit.edu/python/index.html"
    response = requests.get(url)
    assert response.status_code == 200, f"Website {url} returned status code {response.status_code}"

if __name__ == "__main__":
    test_website_up()

import requests


def add_url(group, url):
    data = {
        "group": group,
        "url": url,
    }
    requests.post("/url", data=data)


def new(name):
    """
    new creates a new healthcheck account
    """
    data = {
        "name": name,
    }
    requests.post("/", data=data)

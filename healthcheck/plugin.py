import requests


def add_url(name, url):
    """
    add_url creates a new url checker
    """
    data = {
        "name": name,
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


def add_watcher(name, watcher):
    """
    add_watcher creates a new watcher
    """
    data = {
        "name": name,
        "watcher": watcher,
    }
    requests.post("/watcher", data=data)

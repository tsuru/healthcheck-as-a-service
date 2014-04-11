import requests


def add_url(group, url):
    data = {
        "group": group,
        "url": url,
    }
    requests.post("/url", data=data)

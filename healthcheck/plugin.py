#! /usr/bin/env python

import urllib2
import urllib
import sys


def post(url, data):
    data = urllib.urlencode(data)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    return response.read()


def add_url(name, url):
    """
    add_url creates a new url checker
    """
    data = {
        "name": name,
        "url": url,
    }
    post("/url", data)


def new(name):
    """
    new creates a new healthcheck account
    """
    data = {
        "name": name,
    }
    post("/", data)


def add_watcher(name, watcher):
    """
    add_watcher creates a new watcher
    """
    data = {
        "name": name,
        "watcher": watcher,
    }
    post("/watcher", data)


def command(command_name):
    commands = {
        "add-url": add_url,
        "new": new,
        "add-watcher": add_watcher,
    }
    return commands[command_name]


def main(cmd, *args):
    command(cmd)(*args)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])

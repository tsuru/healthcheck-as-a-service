#! /usr/bin/env python

import httplib
import sys


API_URL = "{{ API_URL }}"


class CommandNotFound(Exception):
    """
    Exception raised when a command is not found in the registered commands.
    """
    pass


def post(url, data):
    conn = httplib.HTTPConnection(API_URL)
    conn.request('POST', url, data)
    resp = conn.getresponse()
    return resp.read()


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
    if command_name not in commands:
        raise CommandNotFound(
            "Command '{}' does not exist".format(command_name)
        )
    return commands[command_name]


def main(cmd, *args):
    try:
        command(cmd)(*args)
    except CommandNotFound as e:
        print e


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])

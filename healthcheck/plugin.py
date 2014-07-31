#!/usr/bin/env python

# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import httplib
import sys
import urllib


API_URL = "{{ API_URL }}"


class CommandNotFound(Exception):
    """
    Exception raised when a command is not found in the registered commands.
    """
    pass


def request(*args):
    conn = httplib.HTTPConnection(API_URL)
    conn.request(*args)
    resp = conn.getresponse()
    resp.read()
    return resp


def post(url, data):
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"
    }
    return request('POST', url, urllib.urlencode(data), headers)


def delete(url):
    return request('DELETE', url)


def add_url(name, url):
    """
    add_url creates a new url checker
    """
    data = {
        "name": name,
        "url": url,
    }
    post("/url", data)


def remove_url(name, url):
    """
    remove_url removes the url checker
    """
    delete("/{}/url/{}".format(name, url))


def add_watcher(name, watcher):
    """
    add_watcher creates a new watcher
    """
    data = {
        "name": name,
        "watcher": watcher,
    }
    post("/watcher", data)


def remove_watcher(name, watcher):
    """
    remove_watcher creates a new watcher
    """
    delete("/{}/watcher/{}".format(name, watcher))


def command(command_name):
    commands = {
        "add-url": add_url,
        "remove-url": remove_url,
        "add-watcher": add_watcher,
        "remove-watcher": remove_watcher,
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
    main(sys.argv[1], *sys.argv[2:])

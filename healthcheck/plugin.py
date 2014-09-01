#!/usr/bin/env python

# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import json
import sys
import urllib2


def get_env(name):
    env = os.environ.get(name)
    if not env:
        sys.stderr.write("ERROR: missing {}\n".format(name))
        sys.exit(5)
    return env


class Request(urllib2.Request):

    def __init__(self, method, *args, **kwargs):
        self._method = method
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return self._method


def proxy_request(instance_name, method, path, body=None, headers=None):
    target = get_env("TSURU_TARGET").rstrip("/")
    token = get_env("TSURU_TOKEN")

    if not target.startswith("http://") and not target.startswith("https://"):
        target = "http://{}".format(target)

    url = "{}/services/proxy/{}?callback={}".format(target, instance_name,
                                                    path)

    if body:
        body = json.dumps(body)

    request = Request(method, url, data=body)
    request.add_header("Authorization", "bearer " + token)

    if headers:
        for header, value in headers.items():
            request.add_header(header, value)

    return urllib2.urlopen(request, timeout=30)


def add_url(name, url, expected_string=None):
    """
    add-url add a new url checker to the given instance. Usage:

        add-url <instance-name> <url> [expected_string]

    expected_string is an optional parameter that represents the string that
    the healthcheck should expect to find in the body of the response. Example:

        tsuru {plugin_name} add-url mysite http://mysite.com/hc WORKING
    """
    data = {
        "name": name,
        "url": url,
    }
    if expected_string:
        data["expected_string"] = expected_string
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"
    }
    proxy_request(name, "POST", "/url", data, headers)
    msg = "url {} successfully added!\n".format(url)
    sys.stdout.write(msg)


def remove_url(name, url):
    """
    remove-url removes the specified url checker from the specified instance.
    Usage:

        remove-url <name> <url>

    Example:

        tsuru {plugin_name} remove-url mysite http://mysite.com/hc
    """
    url = "/{}/url/{}".format(name, url)
    proxy_request(name, "DELETE", url)
    msg = "url {} successfully removed!\n".format(url)
    sys.stdout.write(msg)


def add_watcher(name, watcher):
    """
    add-watcher creates a new watcher for the given monitoring instance. A
    watcher is an email address that will receive notifications for this
    instance. Usage:

        add-watcher <instance-name> <email>

    Example:

        tsuru {plugin_name} add-watcher mysite mysite+monit@mycompany.com
    """
    data = {
        "name": name,
        "watcher": watcher,
    }
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"
    }
    proxy_request(name, "POST", "/watcher", data, headers)
    msg = "watcher {} successfully added!\n".format(watcher)
    sys.stdout.write(msg)


def remove_watcher(name, watcher):
    """
    remove-watcher removes the specified watcher from the given monitoring
    instance. Usage:

        remove-watcher <instance-name> <email>

    Example:

        tsuru {plugin_name} remove-watcher mysite mysite+monit@mycompany.com
    """
    url = "/{}/watcher/{}".format(name, watcher)
    proxy_request(name, "DELETE", url)
    msg = "watcher {} successfully removed!\n".format(watcher)
    sys.stdout.write(msg)


def show_help(command_name=None, exit=0):
    """
    help displays the help of the specified command. Usage:

        help <command-name>

    Example:

        tsuru {plugin_name} help [command-name]

    The command-name is optional, when ommited the plugin will list all
    available commands.
    """
    plugin_name = os.environ.get("TSURU_PLUGIN_NAME", "hc")
    commands = _get_commands()
    if command_name and command_name in commands:
        command = commands[command_name]
        doc = command.__doc__.format(plugin_name=plugin_name)
        sys.stderr.write(doc.rstrip() + "\n")
        sys.exit(exit)
    msg = "Usage: tsuru {plugin_name} command [args]\n\n"
    sys.stderr.write(msg.format(plugin_name=plugin_name))
    sys.stderr.write("Available commands:\n")

    for name in sorted(commands.keys()):
        if name != "help":
            sys.stderr.write("  {}\n".format(name))
    sys.stderr.write("  help\n")

    msg = "Use tsuru {plugin_name} help <commandname> to get more details."
    sys.stderr.write("\n" + msg.format(plugin_name=plugin_name) + "\n")
    sys.exit(exit)


def _get_commands():
    return {
        "add-url": add_url,
        "remove-url": remove_url,
        "add-watcher": add_watcher,
        "remove-watcher": remove_watcher,
        "help": show_help,
    }


def command(command_name):
    commands = _get_commands()
    if command_name in commands:
        return commands[command_name]
    show_help(exit=2)


def main(cmd, *args):
    command(cmd)(*args)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help(exit=2)
    main(sys.argv[1], *sys.argv[2:])

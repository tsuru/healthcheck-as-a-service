#!/usr/bin/env python

# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import os
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


def proxy_request(service_name, instance_name, method, path, body=None, headers=None):
    target = get_env("TSURU_TARGET").rstrip("/")
    token = get_env("TSURU_TOKEN")

    if not target.startswith("http://") and not target.startswith("https://"):
        target = "http://{}".format(target)

    url = "{}/services/{}/proxy/{}?callback={}".format(target, service_name, instance_name, path)

    if body:
        body = json.dumps(body)

    request = Request(method, url, data=body)
    request.add_header("Authorization", "bearer " + token)

    if headers:
        for header, value in headers.items():
            request.add_header(header, value)

    return urllib2.urlopen(request, timeout=30)


def add_url(service_name, name, url, expected_string=None, comment=None):
    """
    add-url add a new url checker to the given instance. Usage:

        add-url <service-name> <instance-name> <url> [expected_string] [comment]

    expected_string is an optional parameter that represents the string that
    the healthcheck should expect to find in the body of the response. Example:

        tsuru {plugin_name} add-url hcaas mysite http://mysite.com/hc WORKING

    comment is an optional parameter that refers to what to do when a trigger
    is triggered. Example:

        tsuru {plugin_name} add-url hcaas mysite http://mysite.com/hc 'restart the app'

    """
    data = {
        "name": name,
        "url": url,
    }
    if expected_string:
        data["expected_string"] = expected_string
    if comment:
        data["comment"] = comment
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/plain"
    }
    proxy_request(service_name, name, "POST", "/url", data, headers)
    msg = "url {} successfully added!\n".format(url)
    sys.stdout.write(msg)


def remove_url(service_name, name, url):
    """
    remove-url removes the specified url checker from the specified instance.
    Usage:

        remove-url <service_name> <name> <url>

    Example:

        tsuru {plugin_name} remove-url hcaas mysite http://mysite.com/hc
    """
    body = {"name": name, "url": url}
    headers = {"Content-Type": "application/json"}
    try:
        proxy_request(service_name, name, "DELETE", "/url", body=body, headers=headers)
    except urllib2.HTTPError:
        sys.stdout.write("URL %s not found.\n" % url)
        return
    msg = "url {} successfully removed!\n".format(url)
    sys.stdout.write(msg)


def list_urls(service_name, name):
    """
    list-urls list all urls from an instance.
    Usage:

        list-urls <service_name> <name>

    Example:

        tsuru {plugin_name} list-urls hcaas mysite
    """
    url = "/url?name={}".format(name)
    headers = {"Content-Type": "application/json"}
    response = proxy_request(service_name, name, "GET", url, "", headers)
    urls = response.read()
    sys.stdout.write(urls + "\n")


def add_watcher(service_name, name, watcher):
    """
    add-watcher creates a new watcher for the given monitoring instance. A
    watcher is an email address that will receive notifications for this
    instance. Usage:

        add-watcher <service_name> <instance-name> <email>

    Example:

        tsuru {plugin_name} add-watcher hcaas mysite mysite+monit@mycompany.com
    """
    data = {
        "name": name,
        "watcher": watcher,
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/plain"
    }
    proxy_request(service_name, name, "POST", "/watcher", data, headers)
    msg = "watcher {} successfully added!\n".format(watcher)
    sys.stdout.write(msg)


def remove_watcher(service_name, name, watcher):
    """
    remove-watcher removes the specified watcher from the given monitoring
    instance. Usage:

        remove-watcher <service_name> <instance-name> <email>

    Example:

        tsuru {plugin_name} remove-watcher hcaas mysite mysite+monit@mycompany.com
    """
    url = "/{}/watcher/{}".format(name, watcher)
    proxy_request(service_name, name, "DELETE", url)
    msg = "watcher {} successfully removed!\n".format(watcher)
    sys.stdout.write(msg)


def list_watchers(service_name, name):
    """
    list-watchers list all watchers from an instance.
    Usage:

        list-watchers <service_name> <name>

    Example:

        tsuru {plugin_name} list-watchers hcaas mysite
    """
    url = '/watcher?name={}'.format(name)
    headers = {"Content-Type": "application/json"}
    response = proxy_request(service_name, name, "GET", url, "", headers)
    watchers_json = response.read()
    watchers = json.loads(watchers_json)
    for watcher in watchers:
        sys.stdout.write(watcher + "\n")


def show_help(command_name=None, exit=0):
    """
    help displays the help of the specified command. Usage:

        help <command-name>

    Example:

        tsuru {plugin_name} help [command-name]

    The command-name is optional, when omitted the plugin will list all
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
        "list-urls": list_urls,
        "add-watcher": add_watcher,
        "remove-watcher": remove_watcher,
        "list-watchers": list_watchers,
        "help": show_help,
    }


def command(command_name):
    commands = _get_commands()
    if command_name in commands:
        return commands[command_name]
    show_help(exit=2)


def main(cmd, *args):
    try:
        command(cmd)(*args)
    except TypeError:
        show_help(cmd, exit=2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help(exit=2)
    main(sys.argv[1], *sys.argv[2:])

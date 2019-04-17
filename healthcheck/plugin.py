#!/usr/bin/env python

# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import os
import sys

try:
    from urllib2 import urlopen, Request, HTTPError
except ImportError:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


def get_env(name):
    env = os.environ.get(name)
    if not env:
        sys.stderr.write("ERROR: missing {}\n".format(name))
        sys.exit(5)
    return env


def proxy_request(service_name, instance_name, method, path, body=None, headers=None):
    target = get_env("TSURU_TARGET").rstrip("/")
    token = get_env("TSURU_TOKEN")

    if not target.startswith("http://") and not target.startswith("https://"):
        target = "http://{}".format(target)

    if instance_name:
        url = "{}/services/{}/proxy/{}?callback=/resources/{}/{}".format(target, service_name, instance_name, instance_name, path.lstrip("/"))
    else:
        url = "{}/services/proxy/service/{}?callback=/resources/{}".format(target, service_name, path.lstrip("/"))

    request = Request(url)
    request.add_header("Authorization", "bearer " + token)
    request.get_method = lambda: method
    if body:
        body = json.dumps(body)
        try:
            request.add_data(body)
        except AttributeError:
            request.data = body.encode('utf-8')

    if headers:
        for header, value in headers.items():
            request.add_header(header, value)

    try:
        return urlopen(request, timeout=30)
    except HTTPError as error:
        return error
    except Exception:
        raise


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
    parsed_url = urlparse(url)
    if parsed_url.scheme == '':
        sys.stderr.write("ERROR: missing url scheme\n")
        sys.exit(2)

    data = {
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

    result = proxy_request(service_name, name, "POST", "/url", data, headers)
    if result.getcode() == 201:
        msg = "url {} successfully added!\n".format(url)
        sys.stdout.write(msg)
    else:
        msg = result.read().decode('utf-8').rstrip("\n")
        sys.stderr.write("ERROR: " + msg + "\n")
        sys.exit(1)


def remove_url(service_name, name, url):
    """
    remove-url removes the specified url checker from the specified instance.
    Usage:

        remove-url <service_name> <name> <url>

    Example:

        tsuru {plugin_name} remove-url hcaas mysite http://mysite.com/hc
    """
    body = {"url": url}
    headers = {"Content-Type": "application/json"}
    result = proxy_request(service_name, name, "DELETE", "/url", body=body, headers=headers)
    if result.getcode() == 204:
        msg = "url {} successfully removed!\n".format(url)
        sys.stdout.write(msg)
    else:
        msg = result.read().decode('utf-8').rstrip("\n")
        sys.stderr.write("ERROR: " + msg + "\n")
        sys.exit(1)


def list_urls(service_name, name):
    """
    list-urls list all urls from an instance.
    Usage:

        list-urls <service_name> <name>

    Example:

        tsuru {plugin_name} list-urls hcaas mysite
    """
    url = "/url"
    headers = {"Content-Type": "application/json"}
    result = proxy_request(service_name, name, "GET", url, "", headers)
    if result.getcode() == 200:
        urls = result.read()
        sys.stdout.write(urls + "\n")
    else:
        msg = result.read().decode('utf-8').rstrip("\n")
        sys.stderr.write("ERROR: " + msg + "\n")
        sys.exit(1)


def add_watcher(service_name, name, watcher, password=None):
    """
    add-watcher creates a new watcher for the given monitoring instance. A
    watcher is an email address that will receive notifications for this
    instance. Usage:

        add-watcher <service_name> <instance-name> <email> [password]

    password is an optional parameter used to create a user when email does
    not exists in zabbix. Example:

        tsuru {plugin_name} add-watcher hcaas mysite mysite+monit@mycompany.com
    """
    data = {
        "watcher": watcher,
    }
    if password:
        data["password"] = password

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/plain"
    }
    result = proxy_request(service_name, name, "POST", "/watcher", data, headers)
    if result.getcode() == 201:
        msg = "watcher {} successfully added!\n".format(watcher)
        sys.stdout.write(msg)
    else:
        msg = result.read().decode('utf-8').rstrip("\n")
        sys.stderr.write("ERROR: " + msg + "\n")
        sys.exit(1)


def remove_watcher(service_name, name, watcher):
    """
    remove-watcher removes the specified watcher from the given monitoring
    instance. Usage:

        remove-watcher <service_name> <instance-name> <email>

    Example:

        tsuru {plugin_name} remove-watcher hcaas mysite mysite+monit@mycompany.com
    """
    url = "/watcher/{}".format(watcher)
    result = proxy_request(service_name, name, "DELETE", url)
    if result.getcode() == 204:
        msg = "watcher {} successfully removed!\n".format(watcher)
        sys.stdout.write(msg)
    else:
        msg = result.read().decode('utf-8').rstrip("\n")
        sys.stderr.write("ERROR: " + msg + "\n")
        sys.exit(1)


def list_watchers(service_name, name):
    """
    list-watchers list all watchers from an instance.
    Usage:

        list-watchers <service_name> <name>

    Example:

        tsuru {plugin_name} list-watchers hcaas mysite
    """
    url = '/watcher'
    headers = {"Content-Type": "application/json"}
    result = proxy_request(service_name, name, "GET", url, "", headers)
    if result.getcode() == 200:
        watchers_json = result.read()
        watchers = json.loads(watchers_json)
        for watcher in watchers:
            sys.stdout.write(watcher + "\n")
    else:
        msg = result.read().decode('utf-8').rstrip("\n")
        sys.stderr.write("ERROR: " + msg + "\n")
        sys.exit(1)


def list_service_groups(service_name, name, keyword=None):
    """
    list-service-groups list available hostgroups from service.
    Usage:

        list-service-groups <service_name> <instance-name> [keyword]

    keyword is an optional parameter that represents a prefix string to search.

    Examples:

        tsuru {plugin_name} list-service-groups hcaas mysite

        tsuru {plugin_name} list-service-groups hcaas mysite projects
    """
    url = "/servicegroups"
    if keyword:
        url += "?keyword=" + keyword

    headers = {"Content-Type": "application/json"}
    result = proxy_request(service_name, name, "GET", url, "", headers)
    if result.getcode() == 200:
        groups_json = result.read()
        groups = json.loads(groups_json)
        for group in groups:
            sys.stdout.write(group + "\n")
    else:
        msg = result.read().decode('utf-8').rstrip("\n")
        sys.stderr.write("ERROR: " + msg + "\n")
        sys.exit(1)


def add_group(service_name, name, group):
    """
    add-group inserts the given monitoring instances to a new hostgroup. A
    group is a zabbix hostgroup that will receive notifications for this
    instance. Usage:

        add-group <service_name> <instance-name> <hostgroup>

        tsuru {plugin_name} add-group hcaas mysite MyZabbixHostGroup
    """
    data = {
        "group": group,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/plain"
    }
    result = proxy_request(service_name, name, "POST", "/groups", data, headers)
    if result.getcode() == 201:
        msg = "group {} successfully added!\n".format(group)
        sys.stdout.write(msg)
    else:
        msg = result.read().decode('utf-8').rstrip("\n")
        sys.stderr.write("ERROR: " + msg + "\n")
        sys.exit(1)


def remove_group(service_name, name, group):
    """
    remove-group removes the specified group from the given monitoring
    instance. Usage:

        remove-group <service_name> <instance-name> <group>

    Example:

        tsuru {plugin_name} remove-group hcaas mysite MyZabbixHostGroup
    """
    body = {"group": group}
    headers = {"Content-Type": "application/json"}
    result = proxy_request(service_name, name, "DELETE", "/groups", body=body, headers=headers)
    if result.getcode() == 204:
        msg = "group {} successfully removed!\n".format(group)
        sys.stdout.write(msg)
    else:
        msg = result.read().decode('utf-8').rstrip("\n")
        sys.stderr.write("ERROR: " + msg + "\n")
        sys.exit(1)


def list_groups(service_name, name):
    """
    list-groups list all hostgroups from an instance.
    Usage:

        list-groups <service_name> <instance-name>

    Example:

        tsuru {plugin_name} list-groups hcaas mysite
    """
    url = "/groups"
    headers = {"Content-Type": "application/json"}
    result = proxy_request(service_name, name, "GET", url, "", headers)
    if result.getcode() == 200:
        groups_json = result.read()
        groups = json.loads(groups_json)
        for group in groups:
            sys.stdout.write(group + "\n")
    else:
        msg = result.read().decode('utf-8').rstrip("\n")
        sys.stderr.write("ERROR: " + msg + "\n")
        sys.exit(1)


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
        "list-service-groups": list_service_groups,
        "add-group": add_group,
        "remove-group": remove_group,
        "list-groups": list_groups,
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

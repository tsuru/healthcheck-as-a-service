# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import mock
import json
import os
import unittest

from healthcheck.plugin import (add_url, add_watcher, list_urls, command, main,
                                remove_watcher, remove_url, list_watchers, show_help)


class PluginTest(unittest.TestCase):

    def set_envs(self):
        os.environ["TSURU_TARGET"] = self.target = "https://cloud.tsuru.io/"
        os.environ["TSURU_TOKEN"] = self.token = "abc123"
        os.environ["TSURU_PLUGIN_NAME"] = self.plugin_name = "hc"

    def delete_envs(self):
        del os.environ["TSURU_TARGET"], os.environ["TSURU_TOKEN"], \
            os.environ["TSURU_PLUGIN_NAME"]

    def setUp(self):
        self.set_envs()

    def tearDown(self):
        self.delete_envs()

    @mock.patch("urllib2.urlopen")
    @mock.patch("healthcheck.plugin.Request")
    def test_add_url(self, Request, urlopen):
        request = mock.Mock()
        Request.return_value = request

        add_url("name", "url")

        Request.assert_called_with(
            'POST',
            self.target + 'services/proxy/name?callback=/url',
            data=json.dumps({'url': 'url', 'name': 'name'})
        )

        calls = [
            mock.call("Authorization", "bearer {}".format(self.token)),
            mock.call("Content-Type", "application/json"),
            mock.call("Accept", "text/plain"),
        ]
        self.assertEqual(calls, request.add_header.call_args_list)
        urlopen.assert_called_with(request, timeout=30)

    @mock.patch("urllib2.urlopen")
    @mock.patch("healthcheck.plugin.Request")
    def test_add_url_with_expected_string_args(self, Request, urlopen):
        request = mock.Mock()
        Request.return_value = request

        add_url("name", "url", "WORKING")

        Request.assert_called_with(
            'POST',
            self.target + 'services/proxy/name?callback=/url',
            data=json.dumps({'url': 'url', 'name': 'name',
                             'expected_string': 'WORKING'})
        )

        calls = [
            mock.call("Authorization", "bearer {}".format(self.token)),
            mock.call("Content-Type", "application/json"),
            mock.call("Accept", "text/plain"),
        ]
        self.assertEqual(calls, request.add_header.call_args_list)
        urlopen.assert_called_with(request, timeout=30)

    @mock.patch("urllib2.urlopen")
    @mock.patch("healthcheck.plugin.Request")
    def test_add_url_with_comment_args(self, Request, urlopen):
        request = mock.Mock()
        Request.return_value = request

        add_url("name", "url", comment="http://test.com")

        Request.assert_called_with(
            'POST',
            self.target + 'services/proxy/name?callback=/url',
            data=json.dumps({'url': 'url', 'name': 'name',
                             'comment': 'http://test.com'})
        )

        calls = [
            mock.call("Authorization", "bearer {}".format(self.token)),
            mock.call("Content-Type", "application/json"),
            mock.call("Accept", "text/plain"),
        ]
        self.assertEqual(calls, request.add_header.call_args_list)
        urlopen.assert_called_with(request, timeout=30)

    @mock.patch("urllib2.urlopen")
    @mock.patch("healthcheck.plugin.Request")
    def test_list_urls(self, Request, urlopen):
        request = mock.Mock()
        Request.return_value = request

        response = mock.Mock()
        response.read.return_value = json.dumps(['http://test.com'])
        urlopen.return_value = response

        list_urls("name")

        Request.assert_called_with(
            'GET',
            self.target + 'services/proxy/name?callback=/url?name=name',
            data=''
        )

        calls = [
            mock.call("Authorization", "bearer {}".format(self.token)),
            mock.call("Content-Type", "application/json"),
        ]
        self.assertEqual(calls, request.add_header.call_args_list)
        urlopen.assert_called_with(request, timeout=30)

    @mock.patch("urllib2.urlopen")
    @mock.patch("healthcheck.plugin.Request")
    def test_remove_url(self, Request, urlopen):
        request = mock.Mock()
        Request.return_value = request

        remove_url("name", "url")

        Request.assert_called_with(
            'DELETE',
            self.target + 'services/proxy/name?callback=/url',
            data=json.dumps({"url": "url", "name": "name"}),
        )
        calls = [
            mock.call("Authorization", "bearer " + self.token),
            mock.call("Content-Type", "application/json"),
        ]
        self.assertEqual(calls, request.add_header.call_args_list)
        urlopen.assert_called_with(request, timeout=30)

    @mock.patch("urllib2.urlopen")
    @mock.patch("healthcheck.plugin.Request")
    def test_add_watcher(self, Request, urlopen):
        request = mock.Mock()
        Request.return_value = request

        add_watcher("name", "watcher@watcher.com")

        Request.assert_called_with(
            'POST',
            self.target + 'services/proxy/name?callback=/watcher',
            data=json.dumps({'watcher': 'watcher@watcher.com', 'name': 'name'})
        )

        calls = [
            mock.call("Authorization", "bearer " + self.token),
            mock.call("Content-Type", "application/json"),
            mock.call("Accept", "text/plain"),
        ]
        request.add_header.has_calls(calls)
        urlopen.assert_called_with(request, timeout=30)

    @mock.patch("urllib2.urlopen")
    @mock.patch("healthcheck.plugin.Request")
    def test_remove_watcher(self, Request, urlopen):
        request = mock.Mock()
        Request.return_value = request

        remove_watcher("name", "watcher@watcher.com")

        uri = 'services/proxy/name?callback=/name/watcher/watcher@watcher.com'
        Request.assert_called_with(
            'DELETE',
            self.target + uri,
            data=None,
        )
        request.add_header.assert_called_with("Authorization",
                                              "bearer " + self.token)
        urlopen.assert_called_with(request, timeout=30)

    @mock.patch("urllib2.urlopen")
    @mock.patch("healthcheck.plugin.Request")
    def test_list_watchers(self, Request, urlopen):
        request = mock.Mock()
        Request.return_value = request

        response = mock.Mock()
        response.read.return_value = json.dumps(['bla@test.com'])
        urlopen.return_value = response

        list_watchers("name")

        Request.assert_called_with(
            'GET',
            self.target + 'services/proxy/name?callback=/watcher?name=name',
            data=''
        )

        calls = [
            mock.call("Authorization", "bearer {}".format(self.token)),
            mock.call("Content-Type", "application/json"),
        ]
        self.assertEqual(calls, request.add_header.call_args_list)
        urlopen.assert_called_with(request, timeout=30)

    @mock.patch("sys.stderr")
    def test_help(self, stderr):
        with self.assertRaises(SystemExit) as cm:
            show_help("add-url")
        exc = cm.exception
        self.assertEqual(0, exc.code)
        doc = add_url.__doc__.format(plugin_name="hc")
        stderr.write.assert_called_with(doc.rstrip() + "\n")

    @mock.patch("sys.stderr")
    def test_help_with_exit_code(self, stderr):
        with self.assertRaises(SystemExit) as cm:
            show_help("add-watcher", exit=2)
        exc = cm.exception
        self.assertEqual(2, exc.code)
        doc = add_watcher.__doc__.format(plugin_name="hc")
        stderr.write.assert_called_with(doc.rstrip() + "\n")

    def test_commands(self):
        expected_commands = {
            "add-url": add_url,
            "add-watcher": add_watcher,
            "remove-url": remove_url,
            "remove-watcher": remove_watcher,
        }
        for key, cmd in expected_commands.items():
            self.assertEqual(command(key), cmd)

    @mock.patch("sys.stderr")
    def test_command_not_found(self, stderr):
        with self.assertRaises(SystemExit) as cm:
            command("waaaat")
        exc = cm.exception
        self.assertEqual(2, exc.code)
        calls = [
            mock.call("Usage: tsuru hc command [args]\n\n"),
            mock.call("Available commands:\n"),
            mock.call("  add-url\n"),
            mock.call("  add-watcher\n"),
            mock.call("  list-urls\n"),
            mock.call("  list-watchers\n"),
            mock.call("  remove-url\n"),
            mock.call("  remove-watcher\n"),
            mock.call("  help\n"),
            mock.call("\nUse tsuru hc help <commandname> to"
                      " get more details.\n"),
        ]
        self.assertEqual(calls, stderr.write.call_args_list)

    @mock.patch("healthcheck.plugin.add_url")
    def test_main(self, add_url_mock):
        main("add-url", "myhc", "http://tsuru.io")
        add_url_mock.assert_called_with("myhc", "http://tsuru.io")

    @mock.patch("healthcheck.plugin.show_help")
    def test_main_wrong_params(self, show_help_mock):
        main("add-url")
        show_help_mock.assert_called_with("add-url", exit=2)

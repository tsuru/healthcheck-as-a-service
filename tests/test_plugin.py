import unittest
import mock

from healthcheck.plugin import (add_url, add_watcher, new, post,
                                command, main, CommandNotFound, API_URL)


class PluginTest(unittest.TestCase):

    @mock.patch("healthcheck.plugin.post")
    def test_add_url(self, post_mock):
        add_url("name", "url")
        expected_data = {
            "name": "name",
            "url": "url",
        }
        post_mock.assert_called_with("/url", expected_data)

    @mock.patch("healthcheck.plugin.post")
    def test_new(self, post_mock):
        new("name")
        expected_data = {
            "name": "name",
        }
        post_mock.assert_called_with("/", expected_data)

    @mock.patch("healthcheck.plugin.post")
    def test_add_watcher(self, post_mock):
        add_watcher("name", "watcher@watcher.com")
        expected_data = {
            "name": "name",
            "watcher": "watcher@watcher.com",
        }
        post_mock.assert_called_with("/watcher", expected_data)

    @mock.patch("httplib.HTTPConnection")
    def test_post(self, http_connection_mock):
        url = "url"
        data = {"name": "name"}

        conn_mock = http_connection_mock.return_value
        resp_mock = conn_mock.getresponse.return_value

        post(url, data)

        http_connection_mock.assert_called_with(API_URL)
        conn_mock.request.assert_called_with('POST', url, data)
        conn_mock.getresponse.assert_called_with()
        resp_mock.read.assert_called_with()

    def test_commands(self):
        expected_commands = {
            "add-url": add_url,
            "new": new,
            "add-watcher": add_watcher,
        }
        for key, cmd in expected_commands.items():
            self.assertEqual(command(key), cmd)

    def test_commands_not_found(self):
        with self.assertRaises(CommandNotFound):
            command('notfound')

    @mock.patch("healthcheck.plugin.add_url")
    def test_main(self, add_url_mock):
        main("add-url", "myhc", "http://tsuru.io")
        add_url_mock.assert_called_with("myhc", "http://tsuru.io")

    def test_api_url(self):
        self.assertEqual("{{ API_URL }}", API_URL)

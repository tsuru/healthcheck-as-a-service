import unittest
import mock

from healthcheck.plugin import add_url, add_watcher, new


class PluginTest(unittest.TestCase):

    @mock.patch("requests.post")
    def test_add_url(self, post_mock):
        add_url("name", "url")
        expected_data = {
            "name": "name",
            "url": "url",
        }
        post_mock.assert_called_with("/url", data=expected_data)

    @mock.patch("requests.post")
    def test_new(self, post_mock):
        new("name")
        expected_data = {
            "name": "name",
        }
        post_mock.assert_called_with("/", data=expected_data)

    @mock.patch("requests.post")
    def test_add_watcher(self, post_mock):
        add_watcher("name", "watcher@watcher.com")
        expected_data = {
            "name": "name",
            "watcher": "watcher@watcher.com",
        }
        post_mock.assert_called_with("/watcher", data=expected_data)

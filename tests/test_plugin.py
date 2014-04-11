import unittest
import mock

from healthcheck.plugin import add_url, new


class PluginTest(unittest.TestCase):

    @mock.patch("requests.post")
    def test_add_url(self, post_mock):
        add_url("group", "url")
        expected_data = {
            "group": "group",
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

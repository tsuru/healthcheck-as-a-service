import unittest
import mock

from healthcheck.plugin import add_url


class PluginTest(unittest.TestCase):

    @mock.patch("requests.post")
    def test_add_url(self, post_mock):
        add_url("group", "url")
        expected_data = {
            "group": "group",
            "url": "url",
        }
        post_mock.assert_called_with("/url", data=expected_data)

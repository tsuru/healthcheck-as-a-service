import unittest
import mock

from healthcheck import api


class APITestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = api.app.test_client()

    @mock.patch("healthcheck.backends.Zabbix")
    def test_add_url(self, zabbix_class):
        zabbix_mock = zabbix_class.return_value
        resp = self.api.post(
            "/url",
            data={"name": "hc", "url": "http://bla.com"}
        )
        self.assertEqual(201, resp.status_code)
        zabbix_mock.add_url.assert_called_with("hc", "http://bla.com")

import unittest
import mock
import inspect

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

    @mock.patch("healthcheck.backends.Zabbix")
    def test_add_watcher(self, zabbix_class):
        zabbix_mock = zabbix_class.return_value
        resp = self.api.post(
            "/watcher",
            data={"name": "hc", "watcher": "watcher@watcher.com"}
        )
        self.assertEqual(201, resp.status_code)
        zabbix_mock.add_watcher.assert_called_with("hc", "watcher@watcher.com")

    @mock.patch("healthcheck.backends.Zabbix")
    def test_new(self, zabbix_class):
        zabbix_mock = zabbix_class.return_value
        resp = self.api.post(
            "/",
            data={"name": "hc"}
        )
        self.assertEqual(201, resp.status_code)
        zabbix_mock.new.assert_called_with("hc")

    @mock.patch("healthcheck.backends.Zabbix")
    def test_remove(self, zabbix_class):
        zabbix_mock = zabbix_class.return_value
        resp = self.api.delete("/hc")
        self.assertEqual(204, resp.status_code)
        zabbix_mock.remove.assert_called_with("hc")

    @mock.patch("healthcheck.backends.Zabbix")
    def test_remove_watcher(self, zabbix_class):
        zabbix_mock = zabbix_class.return_value
        resp = self.api.delete("/hc/watcher/watcher@watcher.com")
        self.assertEqual(204, resp.status_code)
        zabbix_mock.delete_watcher.assert_called_with(
            "hc", "watcher@watcher.com")

    def test_plugin(self):
        resp = self.api.get("/plugin")
        self.assertEqual(200, resp.status_code)
        from healthcheck import plugin
        expected_source = inspect.getsource(plugin)
        self.assertEqual(expected_source, resp.data)

# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
import unittest
import mock
import inspect
import os

from healthcheck import api, backends
from . import managers


class APITestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = api.app.test_client()
        cls.manager = managers.FakeManager()
        api.get_manager = lambda: cls.manager

    def setUp(self):
        self.manager.new("hc")

    def tearDown(self):
        self.manager.remove("hc")

    def test_add_url(self):
        resp = self.api.post(
            "/url",
            data={"name": "hc", "url": "http://bla.com"}
        )
        self.assertEqual(201, resp.status_code)
        self.assertIn(
            "http://bla.com",
            self.manager.healthchecks["hc"]["urls"]
        )

    def test_remove_url(self):
        self.manager.add_url("hc", "http://bla.com")
        resp = self.api.delete("/hc/url/http://bla.com")
        self.assertEqual(204, resp.status_code)
        self.assertNotIn(
            "http://bla.com",
            self.manager.healthchecks["hc"]["urls"]
        )

    def test_add_watcher(self):
        resp = self.api.post(
            "/watcher",
            data={"name": "hc", "watcher": "watcher@watcher.com"}
        )
        self.assertEqual(201, resp.status_code)
        self.assertIn(
            "watcher@watcher.com",
            self.manager.healthchecks["hc"]["users"]
        )

    def test_new(self):
        resp = self.api.post(
            "/resources",
            data={"name": "other"}
        )
        self.assertEqual(201, resp.status_code)
        self.assertIn("other", self.manager.healthchecks)

    def test_remove(self):
        self.manager.new("blabla")
        resp = self.api.delete("/blabla")
        self.assertEqual(204, resp.status_code)
        self.assertNotIn("blabla", self.manager.healthchecks)

    def test_remove_watcher(self):
        self.manager.add_watcher("hc", "watcher@watcher.com")
        resp = self.api.delete("/hc/watcher/watcher@watcher.com")
        self.assertEqual(204, resp.status_code)
        self.assertNotIn(
            "watcher@watcher.com",
            self.manager.healthchecks["hc"]["users"]
        )

    def test_plugin(self):
        url = "http://bla.com"
        os.environ["API_URL"] = url
        resp = self.api.get("/plugin")
        self.assertEqual(200, resp.status_code)
        from healthcheck import plugin
        expected_source = inspect.getsource(plugin).replace(
            "{{ API_URL }}", url)
        self.assertEqual(expected_source, resp.data)
        self.assertIn(url, resp.data)


class GetManagerTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        reload(api)

    @mock.patch("pyzabbix.ZabbixAPI")
    def test_get_manager(self, zabbix_mock):
        os.environ["ZABBIX_URL"] = ""
        os.environ["ZABBIX_USER"] = ""
        os.environ["ZABBIX_PASSWORD"] = ""
        os.environ["ZABBIX_HOST"] = ""
        os.environ["ZABBIX_HOST_GROUP"] = ""
        manager = api.get_manager()
        self.assertIsInstance(manager, backends.Zabbix)

    @mock.patch("healthcheck.backends.Zabbix")
    def test_get_manager_that_does_not_exist(self, zabbix_mock):
        os.environ["API_MANAGER"] = "doesnotexist"
        with self.assertRaises(ValueError):
            api.get_manager()

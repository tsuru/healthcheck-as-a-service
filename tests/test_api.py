# Copyright 2015 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
import json
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
            "/resources/hc/url",
            data=json.dumps({"url": "http://bla.com"})
        )
        self.assertEqual(201, resp.status_code)
        self.assertIn(
            {"url": "http://bla.com", "expected_string": None, "comment": ""},
            self.manager.healthchecks["hc"]["urls"]
        )

    def test_add_url_expected_string(self):
        resp = self.api.post(
            "/resources/hc/url",
            data=json.dumps({"url": "http://blabla.com",
                             "expected_string": "WORKING"})
        )
        self.assertEqual(201, resp.status_code)
        self.assertIn(
            {"url": "http://blabla.com", "expected_string": "WORKING", "comment": ""},
            self.manager.healthchecks["hc"]["urls"]
        )

    def test_add_url_comment(self):
        resp = self.api.post(
            "/resources/hc/url",
            data=json.dumps({"url": "http://blabla.com", "comment": "ble"})
        )
        self.assertEqual(201, resp.status_code)
        self.assertIn(
            {"url": "http://blabla.com", "expected_string": None, "comment": "ble"},
            self.manager.healthchecks["hc"]["urls"]
        )

    def test_add_url_bad_request(self):
        resp = self.api.post(
            "/resources/hc/url",
        )
        self.assertEqual(400, resp.status_code)
        self.assertEqual(resp.data, 'url is required')

        resp = self.api.post(
            "/resources/hc/url",
            data=json.dumps({})
        )
        self.assertEqual(400, resp.status_code)
        self.assertEqual(resp.data, 'url is required')

    def test_list_urls(self):
        self.manager.add_url("hc", "http://bla.com")
        resp = self.api.get(
            "/resources/hc/url",
        )
        self.assertEqual(200, resp.status_code)
        self.assertIn(
            "http://bla.com",
            resp.data
        )

    def test_remove_url(self):
        self.manager.add_url("hc", "http://bla.com/")
        resp = self.api.delete("/resources/hc/url",
                               data=json.dumps({"url": "http://bla.com/"}))
        self.assertEqual(204, resp.status_code)
        self.assertNotIn(
            "http://bla.com/",
            self.manager.healthchecks["hc"]["urls"]
        )

    def test_remove_url_no_data(self):
        resp = self.api.delete("/resources/hc/url")
        self.assertEqual(400, resp.status_code)
        self.assertEqual("url is required", resp.data)

    def test_remove_url_invalid_data(self):
        resp = self.api.delete("/resources/hc/url", data={})
        self.assertEqual(400, resp.status_code)
        self.assertEqual("url is required", resp.data)

    def test_remove_url_invalid_url(self):
        resp = self.api.delete("/resources/hc/url",
                               data=json.dumps({"url": "http://url-not-exist.com/"}))
        self.assertEqual(404, resp.status_code)
        self.assertEqual("URL not found.", resp.data)

    def test_add_watcher(self):
        resp = self.api.post(
            "/resources/hc/watcher",
            data=json.dumps({"watcher": "watcher@watcher.com"})
        )
        self.assertEqual(201, resp.status_code)
        self.assertIn(
            "watcher@watcher.com",
            self.manager.healthchecks["hc"]["users"]
        )

    def test_add_watcher_with_password(self):
        resp = self.api.post(
            "/resources/hc/watcher",
            data=json.dumps({
                "watcher": "watcher@watcher.com",
                "password": "teste",
            })
        )
        self.assertEqual(201, resp.status_code)
        self.assertIn(
            "watcher@watcher.com",
            self.manager.healthchecks["hc"]["users"]
        )

    def test_add_watcher_bad_request(self):
        resp = self.api.post("/resources/hc/watcher")
        self.assertEqual(400, resp.status_code)
        self.assertEqual(resp.data, "watcher is required")

        resp = self.api.post("/resources/hc/watcher", data=json.dumps({}))
        self.assertEqual(400, resp.status_code)
        self.assertEqual(resp.data, "watcher is required")

    def test_list_watchers(self):
        self.manager.add_watcher("hc", "test@test.com")
        resp = self.api.get(
            "/resources/hc/watcher",
        )
        self.assertEqual(200, resp.status_code)
        self.assertIn(
            "test@test.com",
            resp.data
        )

    def test_new(self):
        resp = self.api.post(
            "/resources",
            data={"name": "other"}
        )
        self.assertEqual(201, resp.status_code)
        self.assertIn("other", self.manager.healthchecks)

    def test_bind_unit(self):
        resp = self.api.post("/resources/name/bind")
        self.assertEqual(201, resp.status_code)

    def test_bind_app(self):
        resp = self.api.post("/resources/name/bind-app")
        self.assertEqual(200, resp.status_code)

    def test_unbind_unit(self):
        resp = self.api.delete("/resources/name/bind")
        self.assertEqual(200, resp.status_code)

    def test_unbind_app(self):
        resp = self.api.delete("/resources/name/bind-app")
        self.assertEqual(200, resp.status_code)

    def test_remove(self):
        self.manager.new("blabla")
        resp = self.api.delete("/resources/blabla")
        self.assertEqual(204, resp.status_code)
        self.assertNotIn("blabla", self.manager.healthchecks)

    def test_remove_watcher_compat(self):
        self.manager.add_watcher("hc", "watcher@watcher.com")
        resp = self.api.delete("/resources/hc/XanythingX/watcher/watcher@watcher.com")
        self.assertEqual(204, resp.status_code)
        self.assertNotIn(
            "watcher@watcher.com",
            self.manager.healthchecks["hc"]["users"]
        )

    def test_remove_watcher(self):
        self.manager.add_watcher("hc", "watcher@watcher.com")
        resp = self.api.delete("/resources/hc/watcher/watcher@watcher.com")
        self.assertEqual(204, resp.status_code)
        self.assertNotIn(
            "watcher@watcher.com",
            self.manager.healthchecks["hc"]["users"]
        )

    def test_plugin(self):
        resp = self.api.get("/plugin")
        self.assertEqual(200, resp.status_code)
        from healthcheck import plugin
        expected_source = inspect.getsource(plugin)
        self.assertEqual(expected_source, resp.data)

    def test_add_group(self):
        resp = self.api.post(
            "/resources/hc/groups",
            data=json.dumps({"group": "mygroup"})
        )
        self.assertEqual(201, resp.status_code)
        self.assertIn(
            "mygroup",
            self.manager.healthchecks["hc"]["host_groups"]
        )

    def test_add_group_bad_request(self):
        resp = self.api.post("/resources/hc/groups")
        self.assertEqual(400, resp.status_code)
        self.assertEqual(resp.data, "group is required")

        resp = self.api.post("/resources/hc/groups", data=json.dumps({}))
        self.assertEqual(400, resp.status_code)
        self.assertEqual(resp.data, "group is required")

    def test_list_service_groups(self):
        resp = self.api.get(
            "/resources/groups",
        )
        self.assertEqual(200, resp.status_code)
        self.assertIn(
            "mygroup",
            resp.data
        )

    def test_list_service_groups_keyword(self):
        resp = self.api.get(
            "/resources/groups?keyword=my",
        )
        self.assertEqual(200, resp.status_code)
        self.assertIn(
            "mygroup",
            resp.data
        )
        self.assertNotIn(
            "anothergroup",
            resp.data
        )

    def test_list_groups(self):
        self.manager.add_group("hc", "mygroup")
        resp = self.api.get(
            "/resources/hc/groups",
        )
        self.assertEqual(200, resp.status_code)
        self.assertIn(
            "mygroup",
            resp.data
        )

    def test_remove_group(self):
        self.manager.add_group("hc", "mygroup")
        resp = self.api.delete("/resources/hc/groups",
                               data=json.dumps({"group": "mygroup"}))
        self.assertEqual(204, resp.status_code)
        self.assertNotIn(
            "mygroup",
            self.manager.healthchecks["hc"]["host_groups"]
        )


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

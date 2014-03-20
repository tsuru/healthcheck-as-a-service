from unittest import TestCase
from healthcheck.storage import Item

import mock
import os


class ZabbixTest(TestCase):
    def remove_env(self, env):
        if env in os.environ:
            del os.environ[env]

    @mock.patch("healthcheck.storage.MongoStorage")
    @mock.patch("pyzabbix.ZabbixAPI")
    def setUp(self, zabbix_mock, mongo_mock):
        url = "http://zbx.com"
        user = "user"
        password = "pass"
        os.environ["ZABBIX_URL"] = url
        os.environ["ZABBIX_USER"] = user
        os.environ["ZABBIX_PASSWORD"] = password
        os.environ["ZABBIX_HOST"] = "1"
        zapi_mock = mock.Mock()
        zabbix_mock.return_value = zapi_mock

        instance_mock = mock.Mock()
        mongo_mock.return_value = instance_mock

        from healthcheck.backends import Zabbix
        self.backend = Zabbix()
        zabbix_mock.assert_called_with(url)
        zapi_mock.login.assert_called_with(user, password)

        mongo_mock.assert_called_with()
        instance_mock.conn.assert_called_with()
        self.backend.storage = mock.Mock()

    def test_add_url(self):
        url = "http://mysite.com"
        name = "healthcheck for {}".format(url)
        self.backend.zapi.httptest.create.return_value = {"itemids": [1]}
        self.backend.zapi.trigger.create.return_value = {"triggerids": [1]}
        self.backend.add_url(url)
        self.backend.zapi.httptest.create.assert_called_with(
            name=name,
            steps=[{
                "name": name,
                "url": url,
                "status_codes": 200,
                "no": 1,
            }],
            hostid="1",
        )
        expression = "{{Zabbix Server:web.test.rspcode[{},{}].last()}}#200"
        self.backend.zapi.trigger.create.assert_called_with(
            description="trigger for url {}".format(url),
            expression=expression.format(name, name),
            priority=5,
        )
        self.backend.storage.add_item.assert_called()

    def test_delete_url(self):
        url = "http://mysite.com"
        item_id = 1
        trigger_id = 1
        item = Item(url, item_id=item_id, trigger_id=trigger_id)
        self.backend.storage.find_item_by_url.return_value = item
        self.backend.delete_url(url)
        self.backend.zapi.httptest.delete.assert_called_with([item_id])
        self.backend.zapi.trigger.delete.assert_called_with([trigger_id])

    def test_add_watcher(self):
        email = "andrews@corp.globo.com"
        self.backend.add_watcher(email)

    def test_add_action(self):
        self.backend.add_action("url")
        self.backend.zapi.action.create.assert_called_with(
            name="action for url url",
            recovery_msg=1,
            conditions=[],
            operations=[],
        )

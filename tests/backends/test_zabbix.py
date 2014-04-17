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
        old_add_action = self.backend._add_action
        self.backend._add_action = mock.Mock()
        self.backend.storage.find_group_by_name.return_value = mock.Mock(id=13)
        self.backend.add_url("hc_name", url)
        self.backend.storage.find_group_by_name.assert_called_with("hc_name")
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
        self.assertTrue(self.backend.storage.add_item.called)
        self.backend._add_action.assert_called_with('http://mysite.com', 1, 13)
        self.backend._add_action = old_add_action

    def test_remove_url(self):
        url = "http://mysite.com"
        item_id = 1
        trigger_id = 1
        action_id = 8
        item = Item(
            url,
            item_id=item_id,
            trigger_id=trigger_id,
            action_id=action_id
        )
        self.backend.storage.find_item_by_url.return_value = item
        old_action = self.backend._remove_action
        self.backend._remove_action = mock.Mock()
        self.backend.remove_url("hc_name", url)
        self.backend._remove_action.assert_called_with(8)
        self.backend.zapi.httptest.remove.assert_called_with([item_id])
        self.backend.zapi.trigger.remove.assert_called_with([trigger_id])
        self.backend._remove_action = old_action

    def test_add_watcher(self):
        email = "andrews@corp.globo.com"
        self.backend.add_watcher("hc_name", email)

    def test_add_action(self):
        self.backend.zapi.action.create.return_value = {"actionids": ["1"]}
        self.backend._add_action("url", "8", "14")
        self.backend.zapi.action.create.assert_called_with(
            name="action for url url",
            recovery_msg=1,
            conditions=[
                {"conditiontype": 16, "value": "", "operator": 7},
                {"conditiontype": 5, "value": "1"},
                {"conditiontype": 2, "value": "8"},
            ],
            operations=[
                {
                    "operationtype": 0,
                    "opmessage_grp": [{"usrgrpid": "14"}],
                    "opmessage": {
                        "mediatypeid": "1"
                    }
                }
            ],
        )

    def test_add_group(self):
        name = "group name"
        self.backend.zapi.usergroup.create.return_value = {"usrgrpids": [2]}
        self.backend._add_group(name)
        self.assertTrue(self.backend.storage.add_group.called)
        self.backend.zapi.usergroup.create.assert_called_with(
            name=name,
            rights={"permission": 2, "id": "1"},
        )

    def test_new(self):
        name = "blah"
        old_add_group = self.backend._add_group
        self.backend._add_group = mock.Mock()
        self.backend.new(name)
        self.backend._add_group.assert_called_with(name)
        self.backend._add_group = old_add_group

    def test_remove_group(self):
        self.backend._remove_group("id")
        self.backend.zapi.usergroup.remove.assert_called_with(
            ["id"]
        )

    def test_remove_action(self):
        self.backend._remove_action("id")
        self.backend.zapi.action.remove.assert_called_with(
            ["id"]
        )

    def test_remove_watcher(self):
        email = "andrews@corp.globo.com"
        self.backend.remove_watcher("healthcheck", email)

    def test_remove(self):
        name = "blah"
        id = "someid"
        group_mock = mock.Mock(id=id, name=name)
        self.backend.storage.find_group_by_name.return_value = group_mock
        self.backend.remove(name)
        self.backend.zapi.usergroup.remove.assert_called_with([id])
        self.backend.storage.remove_group(group_mock)

# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase

from healthcheck.storage import Item, User

import mock
import os


class ZabbixTest(TestCase):

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
        os.environ["ZABBIX_HOST_GROUP"] = "2"
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
        hc_name = "hc_name"
        item_name = "healthcheck for {}".format(url)

        self.backend.zapi.httptest.create.return_value = {"httptestids": [1]}
        self.backend.zapi.trigger.create.return_value = {"triggerids": [1]}
        old_add_action = self.backend._add_action
        self.backend._add_action = mock.Mock()
        hmock = mock.Mock(host_id="1", group_id=13)
        self.backend.storage.find_healthcheck_by_name.return_value = hmock

        self.backend.add_url(hc_name, url)

        self.backend.storage.find_healthcheck_by_name.assert_called_with(
            hc_name)
        self.backend.zapi.httptest.create.assert_called_with(
            name=item_name,
            steps=[{
                "name": item_name,
                "url": url,
                "status_codes": 200,
                "no": 1,
            }],
            hostid="1",
        )
        expression = "{{%s:web.test.rspcode[{},{}].last()}}#200" % hc_name
        self.backend.zapi.trigger.create.assert_called_with(
            description="trigger for url {}".format(url),
            expression=expression.format(item_name, item_name),
            priority=5,
        )
        self.assertTrue(self.backend.storage.add_item.called)
        self.backend._add_action.assert_called_with('http://mysite.com', 1, 13)
        self.backend._add_action = old_add_action

    def test_add_url_expected_string(self):
        url = "http://mysite.com"
        hc_name = "hc_name"
        item_name = "healthcheck for {}".format(url)

        self.backend.zapi.httptest.create.return_value = {"httptestids": [1]}
        self.backend.zapi.trigger.create.return_value = {"triggerids": [1]}
        old_add_action = self.backend._add_action

        def set_old_add_action():
            self.backend._add_action = old_add_action
        self.addCleanup(set_old_add_action)
        self.backend._add_action = mock.Mock()
        hmock = mock.Mock(host_id="1", group_id=13)
        self.backend.storage.find_healthcheck_by_name.return_value = hmock

        self.backend.add_url(hc_name, url, expected_string="WORKING")

        self.backend.storage.find_healthcheck_by_name.assert_called_with(
            hc_name)
        self.backend.zapi.httptest.create.assert_called_with(
            name=item_name,
            steps=[{
                "name": item_name,
                "url": url,
                "status_codes": 200,
                "no": 1,
                "required": "WORKING",
            }],
            hostid="1",
        )

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
        self.backend.zapi.httptest.delete.assert_called_with(item_id)
        self.backend._remove_action = old_action
        self.backend.storage.remove_item.assert_called_with(item)

    def test_add_watcher(self):
        email = "andrews@corp.globo.com"
        name = "hc_name"
        hmock = mock.Mock(group_id="someid")
        self.backend.storage.find_healthcheck_by_name.return_value = hmock
        self.backend.zapi.user.create.return_value = {"userids": ["123"]}

        self.backend.add_watcher(name, email)

        self.backend.storage.find_healthcheck_by_name.assert_called_with(name)
        self.backend.zapi.user.create.assert_called_with(
            alias=email,
            passwd="",
            usrgrps=["someid"],
            user_medias=[{
                "mediatypeid": "1",
                "sendto": email,
                "active": 0,
                "severity": 63,
                "period": "1-7,00:00-24:00",
            }],
        )
        self.assertTrue(self.backend.storage.add_user.called)

    def test_add_action(self):
        self.backend.zapi.action.create.return_value = {"actionids": ["1"]}

        self.backend._add_action("url", "8", "14")

        self.backend.zapi.action.create.assert_called_with(
            operations=[
                {
                    'mediatypeid': 0,
                    'esc_step_to': 1,
                    'esc_step_from': 1,
                    'operationtype': 0,
                    'esc_period': 0,
                    'evaltype': 0,
                    'opmessage': {'mediatypeid': '0', 'default_msg': 1},
                    'opmessage_grp': [
                        {'usrgrpid': '14'}
                    ]
                }
            ],
            status=0,
            name='action for url url',
            esc_period=3600,
            evaltype=0,
            eventsource=0,
            conditions=[
                {
                    'operator': 7,
                    'conditiontype': 16,
                    'value': ''
                },
                {
                    'conditiontype': 5,
                    'value': '1'
                },
                {
                    'conditiontype': 2,
                    'value': '8'
                }
            ],
            recovery_msg=1
        )

    def test_add_group(self):
        name = "group name"
        host_group = "host group name"
        self.backend.zapi.usergroup.create.return_value = {"usrgrpids": [2]}
        self.backend._add_group(name, host_group)
        self.backend.zapi.usergroup.create.assert_called_with(
            name=name,
            rights={"permission": 2, "id": host_group},
        )

    def test_add_host(self):
        name = "host name"
        self.backend.zapi.host.create.return_value = {"hostids": [2]}

        result = self.backend._add_host(name, host_group="123")

        self.assertEqual(result, 2)

        expected = [{
            'ip': '127.0.0.1',
            'useip': 1,
            'dns': '',
            'main': 1,
            'type': 1,
            'port': '10050'
        }]
        self.backend.zapi.host.create.assert_called_with(
            interfaces=expected, host=name, groups=[{"groupid": "123"}])

    def test_remove_host(self):
        id = "id"
        self.backend._remove_host(id)
        self.backend.zapi.host.delete.assert_called_with("id")

    def test_new(self):
        name = "blah"

        old_add_group = self.backend._add_group
        self.backend._add_group = mock.Mock()

        old_add_host = self.backend._add_host
        self.backend._add_host = mock.Mock()

        self.backend.new(name)

        self.backend._add_group.assert_called_with(name, "2")
        self.backend._add_group = old_add_group

        self.backend._add_host.assert_called_with(name, "2")
        self.backend._add_host = old_add_host

        self.assertTrue(self.backend.storage.add_healthcheck.called)

    def test_remove_group(self):
        self.backend._remove_group("id")
        self.backend.zapi.usergroup.delete.assert_called_with("id")

    def test_remove_action(self):
        self.backend._remove_action("id")
        self.backend.zapi.action.delete.assert_called_with("id")

    def test_remove_watcher(self):
        user = User("123", "email@email.com", "group")
        self.backend.storage.find_user_by_email.return_value = user
        self.backend.remove_watcher("healthcheck", user.email)
        self.backend.zapi.user.delete.assert_called_with("123")
        self.backend.storage.remove_user.assert_called_with(user)

    def test_remove(self):
        name = "blah"
        id = "someid"
        hmock = mock.Mock(group_id=id, host_id=id)
        self.backend.storage.find_healthcheck_by_name.return_value = hmock

        self.backend.remove(name)

        self.backend.zapi.usergroup.delete.assert_called_with(id)
        self.backend.zapi.host.delete.assert_called_with(id)
        self.backend.storage.remove_healthcheck.assert_called_with(hmock)

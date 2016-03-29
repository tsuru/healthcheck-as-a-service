# -*- coding: utf-8 -*-
# Copyright 2015 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import unittest

import mock

from healthcheck.backends import (WatcherAlreadyRegisteredError,
                                  WatcherNotInInstanceError, get_value)
from healthcheck.storage import Item, User, HealthCheck, UserNotFoundError


class ZabbixTest(unittest.TestCase):

    @mock.patch("healthcheck.storage.MongoStorage")
    @mock.patch("pyzabbix.ZabbixAPI")
    def setUp(self, zabbix_mock, mongo_mock):
        os.environ["ZABBIX_URL"] = self.url = "http://zbx.com"
        os.environ["ZABBIX_USER"] = self.user = "user"
        os.environ["ZABBIX_PASSWORD"] = self.password = "pass"
        os.environ["ZABBIX_HOST"] = "1"
        os.environ["ZABBIX_HOST_GROUP"] = "2"
        zapi_mock = mock.Mock()
        zapi_mock.trigger.get.return_value = {"result": [{"comments": "teste"}]}
        zabbix_mock.return_value = zapi_mock

        instance_mock = mock.Mock()
        mongo_mock.return_value = instance_mock

        from healthcheck.backends import Zabbix
        self.backend = Zabbix()
        zabbix_mock.assert_called_with(self.url)
        zapi_mock.login.assert_called_with(self.user, self.password)

        mongo_mock.assert_called_with()
        instance_mock.conn.assert_called_with()
        self.backend.storage = mock.Mock()

    def test_get_value(self):
        url = get_value("ZABBIX_URL")
        self.assertEqual(self.url, url)

    def test_get_value_failure(self):
        with self.assertRaises(Exception) as cm:
            get_value("ZABBIX_URL_URL_URL_URL_")
        exc = cm.exception
        expected = (u"You must define the ZABBIX_URL_URL_URL_URL_ environment"
                    u" variable.")
        self.assertEqual((expected,), exc.args)

    def test_add_url(self):
        url = "http://mysite.com/012345678901234567890123456789012345678"
        hc_name = "hc_name"
        item_name = "hc for {}".format(url)

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
            retries=3,
        )
        expression = ("{{hc_name:web.test.rspcode[{item_name},"
                      "{item_name}].last()}}#200 | {{hc_name:web.test.fail["
                      "{item_name}].last()}}#0 & {{hc_name:web.test.error["
                      "{item_name}].str(required pattern not found)}}=1")
        self.backend.zapi.trigger.create.assert_called_with(
            description="trigger for url {}".format(url),
            expression=expression.format(item_name=item_name),
            priority=5,
            comments=None,
        )
        self.assertTrue(self.backend.storage.add_item.called)
        self.backend._add_action.assert_called_with(url, 1, 13)
        self.backend._add_action = old_add_action

    def test_add_url_expected_string(self):
        url = "http://mysite.com"
        hc_name = "hc_name"
        item_name = "hc for {}".format(url)

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
            retries=3,
        )

    def test_add_url_comment(self):
        url = "http://mysite.com"
        hc_name = "hc_name"

        self.backend.zapi.httptest.create.return_value = {"httptestids": [1]}
        self.backend.zapi.trigger.create.return_value = {"triggerids": [1]}
        old_add_action = self.backend._add_action

        def set_old_add_action():
            self.backend._add_action = old_add_action
        self.addCleanup(set_old_add_action)
        self.backend._add_action = mock.Mock()
        hmock = mock.Mock(host_id="1", group_id=13)
        self.backend.storage.find_healthcheck_by_name.return_value = hmock

        self.backend.add_url(hc_name, url, comment="http://test.com")
        self.backend.zapi.trigger.create.assert_called_with(
            description="trigger for url {}".format(url),
            expression='{hc_name:web.test.rspcode[hc for http://mysite.com,hc for http://mysite.com].last()}#200 \
| {hc_name:web.test.fail[hc for http://mysite.com].last()}#0 & {hc_name:web.test.error\
[hc for http://mysite.com].str(required pattern not found)}=1',
            priority=5,
            comments="http://test.com",
        )

    def test_add_url_big_url(self):
        url = "http://mysite.com/01234567890123456789012345" \
              "67890123456789012345678901234567890123456789"
        hc_name = "hc_name"
        item_name = "hc for http://mysite.com/" \
                    "012345678901234567890123456789012345..."

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
            retries=3,
        )
        expression = ("{{hc_name:web.test.rspcode[{item_name},"
                      "{item_name}].last()}}#200 | {{hc_name:web.test.fail["
                      "{item_name}].last()}}#0 & {{hc_name:web.test.error["
                      "{item_name}].str(required pattern not found)}}=1")
        self.backend.zapi.trigger.create.assert_called_with(
            description="trigger for url {}".format(url),
            expression=expression.format(item_name=item_name),
            priority=5,
            comments=None,
        )
        self.assertTrue(self.backend.storage.add_item.called)
        self.backend._add_action.assert_called_with(url, 1, 13)
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
        self.backend.zapi.httptest.delete.assert_called_with(item_id)
        self.backend._remove_action = old_action
        self.backend.storage.remove_item.assert_called_with(item)

    def test_add_watcher(self):
        email = "andrews@corp.globo.com"
        name = "hc_name"
        hmock = mock.Mock(group_id="someid")
        self.backend.storage.find_user_by_email.side_effect = UserNotFoundError
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

    def test_add_watcher_user_to_group(self):
        email = "andrews@corp.globo.com"
        name = "hc_name"
        hmock = mock.Mock(group_id="someid")
        umock = mock.Mock(id="userid3")
        usersmock = [mock.Mock(id="userid1"), mock.Mock(id="userid2")]
        self.backend.storage.find_user_by_email.return_value = umock
        self.backend.storage.find_users_by_group.return_value = usersmock
        self.backend.storage.find_healthcheck_by_name.return_value = hmock

        self.backend.add_watcher(name, email)

        self.backend.storage.find_healthcheck_by_name.assert_called_with(name)
        self.backend.storage.find_user_by_email.assert_called_with(email)
        self.backend.storage.find_users_by_group.assert_called_with("someid")
        self.backend.zapi.usergroup.update.assert_called_with(
            usrgrpid="someid",
            userids=["userid1", "userid2", "userid3"],
        )
        self.backend.storage.add_user_to_group.assert_called_with(umock,
                                                                  "someid")

    def test_add_watcher_user_already_in_the_group(self):
        email = "andrews@corp.globo.com"
        name = "hc_name"
        hmock = mock.Mock(group_id="someid")
        umock = mock.Mock(id="userid2")
        usersmock = [mock.Mock(id="userid1"), mock.Mock(id="userid2")]
        self.backend.storage.find_user_by_email.return_value = umock
        self.backend.storage.find_users_by_group.return_value = usersmock
        self.backend.storage.find_healthcheck_by_name.return_value = hmock
        with self.assertRaises(WatcherAlreadyRegisteredError):
            self.backend.add_watcher(name, email)

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
            def_shortdata=("hcaas {HOST.NAME} #{EVENT.ID} {TRIGGER.STATUS}: "
                           "{ITEM.VALUE3}"),
            def_longdata=("{TRIGGER.NAME}: {TRIGGER.STATUS}\r\n"
                          "HTTP status code: {ITEM.VALUE1}"),
            r_shortdata="hcaas {HOST.NAME} #{EVENT.ID} {TRIGGER.STATUS}",
            r_longdata=("{TRIGGER.NAME}: {TRIGGER.STATUS}\r\n"
                        "HTTP status code: {ITEM.VALUE1}"),
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
        hmock = mock.Mock(group_id="group")
        user = User("123", "email@email.com", "group")
        self.backend.storage.find_healthcheck_by_name.return_value = hmock
        self.backend.storage.find_user_by_email.return_value = user
        self.backend.remove_watcher("healthcheck", user.email)
        self.backend.zapi.user.delete.assert_called_with("123")
        self.backend.storage.remove_user.assert_called_with(user)

    def test_remove_watcher_not_last_group(self):
        group = "group1"
        hmock = mock.Mock(group_id=group)
        user = User("123", "email@email.com", "group1", "group2")
        users = [mock.Mock(id="123"), mock.Mock(id="456"),
                 mock.Mock(id="789")]
        self.backend.storage.find_users_by_group.return_value = users
        self.backend.storage.find_user_by_email.return_value = user
        self.backend.storage.find_healthcheck_by_name.return_value = hmock
        self.backend.remove_watcher("healthcheck", user.email)
        self.backend.zapi.usergroup.update.assert_called_with(
            usrgrpid="group1",
            userids=["456", "789"],
        )
        self.backend.storage.remove_user_from_group.assert_called_with(user, group)

    def test_remove_watcher_not_in_healthcheck(self):
        hmock = mock.Mock(group_id="group1")
        user = User("123", "email@email.com", "group2")
        self.backend.storage.find_healthcheck_by_name.return_value = hmock
        self.backend.storage.find_user_by_email.return_value = user
        with self.assertRaises(WatcherNotInInstanceError):
            self.backend.remove_watcher("healthcheck", user.email)

    def test_remove(self):
        name = "blah"
        id = "someid"
        url = 'http://test.com/healthcheck'

        old_remove_url = self.backend.remove_url
        self.backend.remove_url = mock.Mock()
        old_remove_watcher = self.backend.remove_watcher
        self.backend.remove_watcher = mock.Mock()
        self.backend.storage.find_urls_by_healthcheck_name.return_value = [url]

        hmock = mock.Mock(group_id=id, host_id=id)
        self.backend.storage.find_healthcheck_by_name.return_value = hmock
        watchers = ['test@example.com']
        self.backend.storage.find_watchers_by_healthcheck_name.return_value = watchers
        user = User("123", "email@email.com", id)
        self.backend.storage.find_user_by_email.return_value = user

        self.backend.remove(name)

        self.backend.storage.find_urls_by_healthcheck_name.assert_called_with(name)
        self.backend.zapi.usergroup.delete.assert_called_with(id)
        self.backend.zapi.host.delete.assert_called_with(id)
        self.backend.storage.remove_healthcheck.assert_called_with(hmock)
        assert self.backend.remove_url.called
        assert self.backend.remove_watcher.called

        self.backend.remove_url = old_remove_url
        self.backend.remove_watcher = old_remove_watcher

    def test_remove_with_urls(self):
        name = "blah"
        url = "http://mysite.com"
        item_id = 1
        trigger_id = 2
        action_id = 3
        group_id = "4"
        host_id = "5"
        user_id = "6"
        item = Item(
            url,
            item_id=item_id,
            trigger_id=trigger_id,
            action_id=action_id
        )

        self.backend.storage.find_item_by_url.return_value = item
        self.backend.storage.find_urls_by_healthcheck_name.return_value = [url]
        hc = HealthCheck(name, group_id=group_id, host_id=host_id)
        self.backend.storage.find_healthcheck_by_name.return_value = hc
        watchers = ['test@example.com']
        self.backend.storage.find_watchers_by_healthcheck_name.return_value = watchers
        user = User(user_id, "email@email.com", group_id)
        self.backend.storage.find_user_by_email.return_value = user
        self.backend.zapi.trigger.get.return_value = [{"comments": "xxx"}]

        self.backend.remove(name)

        self.backend.zapi.usergroup.delete.assert_called_with(group_id)
        self.backend.zapi.host.delete.assert_called_with(host_id)
        self.backend.zapi.action.delete.assert_called_with(action_id)
        self.backend.zapi.httptest.delete.assert_called_with(item_id)
        self.backend.zapi.user.delete.assert_called_with(user_id)
        self.backend.storage.remove_healthcheck.assert_called_with(hc)
        self.backend.storage.remove_item.assert_called_with(item)
        self.backend.storage.find_healthcheck_by_name.assert_called_with(name)
        self.backend.storage.find_urls_by_healthcheck_name.assert_called_with(name)
        self.backend.storage.find_item_by_url.assert_called_with(url)

    def test_remove_with_urls_more_than_one_group(self):
        name = "blah"
        url = "http://mysite.com"
        item_id = 1
        trigger_id = 2
        action_id = 3
        group_id = "4"
        another_group_id = "4-2"
        host_id = "5"
        user_id = "6"
        item = Item(
            url,
            item_id=item_id,
            trigger_id=trigger_id,
            action_id=action_id
        )

        self.backend.storage.find_item_by_url.return_value = item
        self.backend.storage.find_urls_by_healthcheck_name.return_value = [url]
        hc = HealthCheck(name, group_id=group_id, host_id=host_id)
        self.backend.storage.find_healthcheck_by_name.return_value = hc
        watchers = ['test@example.com']
        self.backend.storage.find_watchers_by_healthcheck_name.return_value = watchers
        user = User(user_id, "email@email.com", group_id, another_group_id)
        self.backend.storage.find_user_by_email.return_value = user
        self.backend.storage.find_users_by_group.return_value = [user]
        self.backend.zapi.trigger.get.return_value = [{"comments": "xxx"}]

        self.backend.remove(name)

        self.backend.zapi.usergroup.delete.assert_called_with(group_id)
        self.backend.zapi.host.delete.assert_called_with(host_id)
        self.backend.zapi.action.delete.assert_called_with(action_id)
        self.backend.zapi.httptest.delete.assert_called_with(item_id)
        self.backend.zapi.usergroup.update.assert_called_with(usrgrpid=group_id, userids=[])
        self.backend.storage.remove_healthcheck.assert_called_with(hc)
        self.backend.storage.remove_item.assert_called_with(item)
        self.backend.storage.find_healthcheck_by_name.assert_called_with(name)
        self.backend.storage.find_urls_by_healthcheck_name.assert_called_with(name)
        self.backend.storage.find_item_by_url.assert_called_with(url)
        self.backend.storage.find_users_by_group.assert_called_with(group_id)

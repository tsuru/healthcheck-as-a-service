# -*- coding: utf-8 -*-
# Copyright 2015 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os

from healthcheck.storage import HealthCheck, Item, User, UserNotFoundError


def get_value(key):
    try:
        value = os.environ[key]
    except KeyError:
        msg = u"You must define the {} " \
              u"environment variable.".format(key)
        raise Exception(msg)
    return value


class Zabbix(object):
    def __init__(self):
        url = get_value("ZABBIX_URL")
        user = get_value("ZABBIX_USER")
        password = get_value("ZABBIX_PASSWORD")
        self.host_group_id = get_value("ZABBIX_HOST_GROUP")

        from pyzabbix import ZabbixAPI
        self.zapi = ZabbixAPI(url)
        self.zapi.login(user, password)

        from healthcheck.storage import MongoStorage
        self.storage = MongoStorage()
        self.storage.conn()

    def add_url(self, name, url, expected_string=None, comment=None):
        hc = self.storage.find_healthcheck_by_name(name)
        item_id = self._add_item(name, url, expected_string)
        trigger_id = self._add_trigger(name, url, comment)
        action_id = self._add_action(url, trigger_id, hc.group_id)
        item = Item(
            url,
            item_id=item_id,
            trigger_id=trigger_id,
            action_id=action_id,
            group_id=hc.group_id,
        )
        self.storage.add_item(item)

    def _add_item(self, healthcheck_name, url, expected_string=None):
        hc = self.storage.find_healthcheck_by_name(healthcheck_name)
        item_name = self._create_item_name(url)
        step = {"name": item_name, "url": url,
                "status_codes": 200, "no": 1}
        if expected_string:
            step["required"] = expected_string
        item_result = self.zapi.httptest.create(
            name=item_name,
            steps=[step],
            hostid=hc.host_id,
            retries=int(os.environ.get("ZABBIX_RETRIES", 3)),
        )
        return item_result['httptestids'][0]

    def _create_item_name(self, url):
        name = "hc for {}".format(url)
        if len(name) > 64:
            return name[:61] + "..."
        return name

    def _add_trigger(self, host_name, url, comment=None):
        item_name = self._create_item_name(url)
        status_expression = ("{{%s:web.test.rspcode[{item_name},"
                             "{item_name}].last()}}#200") % host_name
        failed_expression = "{{%s:web.test.fail[{item_name}].last()}}#0" % \
            host_name
        string_expression = ("{{%s:web.test.error[{item_name}]."
                             "str(required pattern not found)}}=1") % host_name
        expression = "%s | %s & %s" % (status_expression, failed_expression,
                                       string_expression)
        trigger_result = self.zapi.trigger.create(
            description="trigger for url {}".format(url),
            expression=expression.format(item_name=item_name),
            priority=5,
            comments=comment,
        )
        return trigger_result['triggerids'][0]

    def remove_url(self, name, url):
        item = self.storage.find_item_by_url(url)
        self._remove_action(item.action_id)
        self.zapi.httptest.delete(item.item_id)
        self.storage.remove_item(item)

    def list_urls(self, name):
        urls_comments = []
        urls = self.storage.find_urls_by_healthcheck_name(name)
        for url in urls:
            url_comment = [url]
            item = self.storage.find_item_by_url(url)
            trigger = self.zapi.trigger.get(triggerids=item.trigger_id)
            url_comment.append(trigger[0].get('comments', ""))
            urls_comments.append(url_comment)
        return urls_comments

    def new(self, name):
        host = self._add_host(name, self.host_group_id)
        group = self._add_group(name, self.host_group_id)
        hc = HealthCheck(
            name=name,
            host_group_id=self.host_group_id,
            host_id=host,
            group_id=group
        )
        self.storage.add_healthcheck(hc)

    def add_watcher(self, name, email):
        hc = self.storage.find_healthcheck_by_name(name)
        try:
            user = self.storage.find_user_by_email(email)
            self._add_user_to_group(hc, user)
        except UserNotFoundError:
            self._add_new_user(hc, email)

    def _add_user_to_group(self, hc, user):
        users = self.storage.find_users_by_group(hc.group_id)
        ids = [u.id for u in users]
        if user.id in ids:
            raise WatcherAlreadyRegisteredError()
        ids.append(user.id)
        self.zapi.usergroup.update(
            usrgrpid=hc.group_id,
            userids=ids,
        )
        self.storage.add_user_to_group(user, hc.group_id)

    def _add_new_user(self, hc, email):
        result = self.zapi.user.create(
            alias=email,
            passwd="",
            usrgrps=[hc.group_id],
            user_medias=[{
                "mediatypeid": "1",
                "sendto": email,
                "active": 0,
                "severity": 63,
                "period": "1-7,00:00-24:00",
            }],
        )
        user_id = result["userids"][0]
        user = User(user_id, email, hc.group_id)
        self.storage.add_user(user)

    def list_watchers(self, name):
        return self.storage.find_watchers_by_healthcheck_name(name)

    def remove_watcher(self, name, email):
        hc = self.storage.find_healthcheck_by_name(name)
        user = self.storage.find_user_by_email(email)
        if hc.group_id not in user.groups_id:
            raise WatcherNotInInstanceError()
        if len(user.groups_id) > 1:
            self._remove_user_from_group(hc, user)
        else:
            self._remove_user(user)

    def _remove_user_from_group(self, hc, user):
        users = self.storage.find_users_by_group(hc.group_id)
        ids = [u.id for u in users if u.id != user.id]
        self.zapi.usergroup.update(
            usrgrpid=hc.group_id,
            userids=ids,
        )
        self.storage.remove_user_from_group(user, hc.group_id)

    def _remove_user(self, user):
        self.zapi.user.delete(user.id)
        self.storage.remove_user(user)

    def remove(self, name):
        urls = self.storage.find_urls_by_healthcheck_name(name)
        for url in urls:
            self.remove_url(name, url)

        watchers = self.list_watchers(name)
        for watcher in watchers:
            self.remove_watcher(name, watcher)

        healthcheck = self.storage.find_healthcheck_by_name(name)
        self._remove_group(healthcheck.group_id)
        self._remove_host(healthcheck.host_id)
        self.storage.remove_healthcheck(healthcheck)

    def _add_action(self, url, trigger_id, group_id):
        result = self.zapi.action.create(
            name="action for url {}".format(url),
            eventsource=0,
            recovery_msg=1,
            status=0,
            esc_period=3600,
            def_shortdata=("hcaas {HOST.NAME} #{EVENT.ID} {TRIGGER.STATUS}: "
                           "{ITEM.VALUE3}"),
            def_longdata=("{TRIGGER.NAME}: {TRIGGER.STATUS}\r\n"
                          "HTTP status code: {ITEM.VALUE1}"),
            r_shortdata="hcaas {HOST.NAME} #{EVENT.ID} {TRIGGER.STATUS}",
            r_longdata=("{TRIGGER.NAME}: {TRIGGER.STATUS}\r\n"
                        "HTTP status code: {ITEM.VALUE1}"),
            evaltype=0,
            conditions=[
                # Maintenance status not in maintenance
                {"conditiontype": 16, "value": "", "operator": 7},
                # Trigger value = PROBLEM
                {"conditiontype": 5, "value": "1"},
                # Trigger = trigger id
                {"conditiontype": 2, "value": trigger_id},
            ],
            operations=[
                {
                    "operationtype": 0,
                    "esc_period": 0,
                    "esc_step_from": 1,
                    "esc_step_to": 1,
                    "evaltype": 0,
                    "mediatypeid": 0,
                    "opmessage_grp": [
                        {
                            "usrgrpid": group_id
                        }
                    ],
                    "opmessage": {
                        "default_msg": 1,
                        "mediatypeid": "0"
                    }
                }
            ],
        )
        return result["actionids"][0]

    def _add_group(self, name, host_group):
        result = self.zapi.usergroup.create(
            name=name,
            rights={"permission": 2, "id": host_group},
        )
        return result["usrgrpids"][0]

    def _add_host(self, name, host_group):
        result = self.zapi.host.create(
            host=name,
            groups=[{"groupid": host_group}],
            interfaces=[{
                "type": 1,
                "main": 1,
                "useip": 1,
                "ip": "127.0.0.1",
                "dns": "",
                "port": "10050"
            }]
        )
        return result["hostids"][0]

    def _remove_host(self, id):
        self.zapi.host.delete(id)

    def _remove_group(self, id):
        self.zapi.usergroup.delete(id)

    def _remove_action(self, id):
        self.zapi.action.delete(id)


class WatcherAlreadyRegisteredError(Exception):
    pass


class WatcherNotInInstanceError(Exception):
    pass

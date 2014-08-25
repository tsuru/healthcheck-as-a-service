# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os

from healthcheck.storage import Item, User, HealthCheck


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

    def add_url(self, name, url):
        hc = self.storage.find_healthcheck_by_name(name)
        item_id = self._add_item(name, url)
        trigger_id = self._add_trigger(name, url)
        action_id = self._add_action(url, trigger_id, hc.group_id)
        item = Item(
            url,
            item_id=item_id,
            trigger_id=trigger_id,
            action_id=action_id,
            group_id=hc.group_id,
        )
        self.storage.add_item(item)

    def remove_url(self, name, url):
        item = self.storage.find_item_by_url(url)
        self._remove_action(item.action_id)
        self.zapi.httptest.delete(item.item_id)
        self.storage.remove_item(item)

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

    def remove_watcher(self, name, email):
        user = self.storage.find_user_by_email(email)
        self._remove_user(user.id)
        self.storage.remove_user(user)

    def remove(self, name):
        healthcheck = self.storage.find_healthcheck_by_name(name)
        self._remove_group(healthcheck.group_id)
        self._remove_host(healthcheck.host_id)
        self.storage.remove_healthcheck(healthcheck)

    def _add_item(self, healthcheck_name, url):
        hc = self.storage.find_healthcheck_by_name(healthcheck_name)
        item_name = "healthcheck for {}".format(url)
        item_result = self.zapi.httptest.create(
            name=item_name,
            steps=[{
                "name": item_name,
                "url": url,
                "status_codes": 200,
                "no": 1,
            }],
            hostid=hc.host_id,
        )
        return item_result['httptestids'][0]

    def _add_trigger(self, host_name, url):
        item_name = "healthcheck for {}".format(url)
        expression = "{{%s:web.test.rspcode[{},{}].last()}}#200" % host_name
        trigger_result = self.zapi.trigger.create(
            description="trigger for url {}".format(url),
            expression=expression.format(item_name, item_name),
            priority=5,
        )
        return trigger_result['triggerids'][0]

    def _add_action(self, url, trigger_id, group_id):
        result = self.zapi.action.create(
            name="action for url {}".format(url),
            eventsource=0,
            recovery_msg=1,
            status=0,
            esc_period=3600,
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

    def _remove_user(self, id):
        self.zapi.user.delete(id)

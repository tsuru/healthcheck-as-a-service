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
        self.host_id = get_value("ZABBIX_HOST")

        from pyzabbix import ZabbixAPI
        self.zapi = ZabbixAPI(url)
        self.zapi.login(user, password)

        from healthcheck.storage import MongoStorage
        self.storage = MongoStorage()
        self.storage.conn()

    def add_url(self, name, url):
        item_name = "healthcheck for {}".format(url)
        item_id = self._add_item(item_name, url)
        trigger_id = self._add_trigger(item_name, url)
        group_id = self.storage.find_group_by_name(name).id
        action_id = self._add_action(url, trigger_id, group_id)
        item = Item(
            url,
            item_id=item_id,
            trigger_id=trigger_id,
            action_id=action_id,
            group_id=group_id,
        )
        self.storage.add_item(item)

    def remove_url(self, name, url):
        item = self.storage.find_item_by_url(url)
        self._remove_action(item.action_id)
        self.zapi.httptest.delete(item.item_id)
        self.storage.remove_item(item)

    def new(self, name):
        host_group = self._add_host_group(name)
        host = self._add_host(name, host_group)
        group = self._add_group(name, host_group)
        hc = HealthCheck(
            name=name,
            host_group_id=host_group,
            host_id=host,
            group_id=group
        )
        self.storage.add_healthcheck(hc)

    def add_watcher(self, name, email):
        group_id = self.storage.find_group_by_name(name).id
        result = self.zapi.user.create(
            alias=email,
            passwd="",
            usrgrps=[group_id],
            user_medias=[{
                "mediatypeid": "1",
                "sendto": email,
                "active": 0,
                "severity": 63,
                "period": "1-7,00:00-24:00",
            }],
        )
        user_id = result["userids"][0]
        user = User(user_id, email, group_id)
        self.storage.add_user(user)

    def remove_watcher(self, name, email):
        user = self.storage.find_user_by_email(email)
        self._remove_user(user.id)
        self.storage.remove_user(user)

    def remove(self, name):
        group = self.storage.find_group_by_name(name)
        self._remove_group(group.id)
        self.storage.remove_group(group)

    def _add_item(self, name, url):
        item_result = self.zapi.httptest.create(
            name=name,
            steps=[{
                "name": name,
                "url": url,
                "status_codes": 200,
                "no": 1,
            }],
            hostid=self.host_id,
        )
        return item_result['httptestids'][0]

    def _add_trigger(self, name, url):
        expression = "{{Zabbix Server:web.test.rspcode[{},{}].last()}}#200"
        trigger_result = self.zapi.trigger.create(
            description="trigger for url {}".format(url),
            expression=expression.format(name, name),
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

    def _add_host_group(self, name):
        self.zapi.hostgroup.create(name=name)

    def _remove_host_group(self, id):
        self.zapi.hostgroup.delete([id])

    def _add_host(self, name, host_group):
        self.zapi.host.create(host=name, groups=[host_group])

    def _remove_host(self, id):
        self.zapi.host.delete([id])

    def _remove_group(self, id):
        self.zapi.usergroup.delete(id)

    def _remove_action(self, id):
        self.zapi.action.delete(id)

    def _remove_user(self, id):
        self.zapi.user.delete(id)

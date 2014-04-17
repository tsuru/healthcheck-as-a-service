import os

from healthcheck.storage import Item, Group


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
        self.zapi.httptest.remove([item.item_id])
        self.zapi.trigger.remove([item.trigger_id])

    def new(self, name):
        self._add_group(name)

    def add_watcher(self, name, email):
        group_id = self.storage.find_group_by_name(name).id
        self.zapi.user.create(
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

    def remove_watcher(self, name, email):
        pass

    def remove(self, name):
        group = self.storage.find_group_by_name(name)
        self._remove_group(group.id)
        self.storage.remove_item(group)

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
        return item_result['itemids'][0]

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
            recovery_msg=1,
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
                    "opmessage_grp": [{"usrgrpid": group_id}],
                    "opmessage": {
                        "mediatypeid": "1"
                    }
                }
            ],
        )
        return result["actionids"][0]

    def _add_group(self, name):
        result = self.zapi.usergroup.create(
            name=name,
            rights={"permission": 2, "id": self.host_id},
        )
        group_id = result["usrgrpids"][0]
        group = Group(name=name, id=group_id)
        self.storage.add_group(group)
        return group_id

    def _remove_group(self, id):
        self.zapi.usergroup.remove([id])

    def _remove_action(self, id):
        self.zapi.action.remove([id])

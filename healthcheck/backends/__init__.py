import os

from healthcheck.storage import Item, Group, User


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
        self.host_group_id = get_value("ZABBIX_HOST_GROUP")

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
        self._add_group(name)

    def add_watcher(self, name, email):
        group_id = self.storage.find_group_by_name(name).id
        result = self.zapi.user.create(
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

    def _add_group(self, name):
        result = self.zapi.usergroup.create(
            name=name,
            rights={"permission": 2, "id": self.host_group_id},
        )
        group_id = result["usrgrpids"][0]
        group = Group(name=name, id=group_id)
        self.storage.add_group(group)
        return group_id

    def _remove_group(self, id):
        self.zapi.usergroup.delete(id)

    def _remove_action(self, id):
        self.zapi.action.delete(id)

    def _remove_user(self, id):
        self.zapi.user.delete(id)

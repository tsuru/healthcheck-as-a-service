import os

from healthcheck.storage import Item


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

    def add_url(self, url):
        name = "healthcheck for {}".format(url)
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
        expression = "{{Zabbix Server:web.test.rspcode[{},{}].last()}}#200"
        trigger_result = self.zapi.trigger.create(
            description="trigger for url {}".format(url),
            expression=expression.format(name, name),
            priority=5,
        )
        trigger_id = trigger_result['triggerids'][0]
        action_id = self.add_action(url, trigger_id, "")
        item = Item(
            url,
            item_id=item_result['itemids'][0],
            trigger_id=trigger_id,
            action_id=action_id,
        )
        self.storage.add_item(item)

    def delete_url(self, url):
        item = self.storage.find_item_by_url(url)
        self.zapi.httptest.delete([item.item_id])
        self.zapi.trigger.delete([item.trigger_id])

    def add_action(self, url, trigger_id, group_id):
        result = self.zapi.action.create(
            name="action for url {}".format(url),
            recovery_msg=1,
            conditions=[
                #Maintenance status not in maintenance
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

    def add_group(self, name):
        result = self.zapi.usergroup.create(
            name=name,
            rights={"permission": 2, "id": self.host_id},
        )
        return result["usrgrpids"][0]

    def delete_group(self, id):
        self.zapi.usergroup.delete([id])

    def add_watcher(self, email):
        pass

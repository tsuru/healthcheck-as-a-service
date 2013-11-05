from unittest import TestCase

from healthcheck.backends import Zabbix


class ZabbixTest(TestCase):
    def test_add_url(self):
        backend = Zabbix()
        url = "http://mysite.com"
        backend.add_url(url)

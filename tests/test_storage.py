import unittest
import mock
import os

from healthcheck.storage import Item, MongoStorage


class ItemTest(unittest.TestCase):

    def test_item(self):
        item = Item("http://teste.com")
        self.assertEqual(item.url, "http://teste.com")

    def test_to_json(self):
        item = Item("http://teste.com")
        self.assertDictEqual(item.to_json(), {"url": "http://teste.com"})


class MongoStorageTest(unittest.TestCase):

    def remove_env(self, env):
        if env in os.environ:
            del os.environ[env]

    def setUp(self):
        self.storage = MongoStorage()
        self.url = "http://myurl.com"
        self.item = Item(self.url)

    @mock.patch("pymongo.MongoClient")
    def test_mongodb_host_environ(self, mongo_mock):
        self.storage.conn()
        mongo_mock.assert_called_with(host="localhost", port=27017)

        os.environ["MONGODB_HOST"] = "0.0.0.0"
        self.addCleanup(self.remove_env, "MONGODB_HOST")
        storage = MongoStorage()
        storage.conn()
        mongo_mock.assert_called_with(host="0.0.0.0", port=27017)

    @mock.patch("pymongo.MongoClient")
    def test_mongodb_port_environ(self, mongo_mock):
        self.storage.conn()
        mongo_mock.assert_called_with(host='localhost', port=27017)

        os.environ["MONGODB_PORT"] = "3333"
        self.addCleanup(self.remove_env, "MONGODB_PORT")
        storage = MongoStorage()
        storage.conn()
        mongo_mock.assert_called_with(host='localhost', port=3333)

    def test_add_item(self):
        self.storage.add_item(self.item)
        result = self.storage.find_item_by_url(self.url)
        self.assertEqual(result.url, self.url)
        self.storage.remove_item(self.item)

    def test_find_item_by_url(self):
        self.storage.add_item(self.item)
        result = self.storage.find_item_by_url(self.item.url)
        self.assertEqual(result.url, self.url)
        self.storage.remove_item(self.item)

    def test_remove_item(self):
        self.storage.add_item(self.item)
        result = self.storage.find_item_by_url(self.item.url)
        self.assertEqual(result.url, self.url)
        self.storage.remove_item(self.item)
        length = self.storage.conn()['hcapi']['items'].find(
            {"url": self.url}).count()
        self.assertEqual(length, 0)

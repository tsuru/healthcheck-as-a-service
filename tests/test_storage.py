import unittest
import mock
import os

from healthcheck.storage import Item


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

    @mock.patch("pymongo.MongoClient")
    def test_mongodb_host_environ(self, mongo_mock):
        from healthcheck.storage import MongoStorage
        storage = MongoStorage()
        storage.conn()
        mongo_mock.assert_called_with(host="localhost", port=27017)

        os.environ["MONGODB_HOST"] = "0.0.0.0"
        self.addCleanup(self.remove_env, "MONGODB_HOST")
        storage = MongoStorage()
        storage.conn()
        mongo_mock.assert_called_with(host="0.0.0.0", port=27017)

    @mock.patch("pymongo.MongoClient")
    def test_mongodb_port_environ(self, mongo_mock):
        from healthcheck.storage import MongoStorage
        storage = MongoStorage()
        storage.conn()
        mongo_mock.assert_called_with(host='localhost', port=27017)

        os.environ["MONGODB_PORT"] = "3333"
        self.addCleanup(self.remove_env, "MONGODB_PORT")
        storage = MongoStorage()
        storage.conn()
        mongo_mock.assert_called_with(host='localhost', port=3333)

    def test_add_item(self):
        from healthcheck.storage import MongoStorage
        storage = MongoStorage()
        url = "http://myurl.com"
        item = Item(url)
        storage.add_item(item)
        result = storage.conn()['hcapi']['items'].find_one({"url": url})
        self.assertEqual(result["url"], url)
        storage.conn()['hcapi']['items'].remove({"url": url})

    def test_find_item_by_url(self):
        from healthcheck.storage import MongoStorage
        storage = MongoStorage()
        url = "http://myurl.com"
        item = Item(url)
        storage.add_item(item)
        result = storage.find_item_by_url(item.url)
        self.assertEqual(result.url, url)
        storage.conn()['hcapi']['items'].remove({"url": url})

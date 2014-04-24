import unittest
import mock
import os

from healthcheck.storage import Item, MongoStorage, Group, User


class UserTest(unittest.TestCase):

    def test_user(self):
        id = "someid"
        email = "watcher@watcher.com"
        group_id = "anotherid"
        user = User(id=id, email=email, group_id=group_id)
        self.assertEqual(user.id, id)
        self.assertEqual(user.email, email)
        self.assertEqual(user.group_id, group_id)

    def test_to_json(self):
        user = User(id="someid", email="w@w.com", group_id="id")
        expected = {"id": "someid", "email": "w@w.com", "group_id": "id"}
        self.assertDictEqual(expected, user.to_json())


class GroupTest(unittest.TestCase):

    def test_group(self):
        group = Group(name="name", id="xpto")
        self.assertEqual(group.name, "name")
        self.assertEqual(group.id, "xpto")

    def test_to_json(self):
        group = Group(name="name", id="xpto")
        self.assertDictEqual(group.to_json(), {"name": "name", "id": "xpto"})


class ItemTest(unittest.TestCase):

    def test_item(self):
        item = Item("http://teste.com", item_id=1)
        self.assertEqual(item.url, "http://teste.com")
        self.assertEqual(item.item_id, 1)

    def test_to_json(self):
        item = Item("http://teste.com", id=1)
        self.assertDictEqual(
            item.to_json(), {"url": "http://teste.com", "id": 1})


class MongoStorageTest(unittest.TestCase):

    def remove_env(self, env):
        if env in os.environ:
            del os.environ[env]

    def setUp(self):
        self.storage = MongoStorage()
        self.url = "http://myurl.com"
        self.item = Item(self.url)
        self.group = Group("name", "id")
        self.user = User("id", "w@w.com", "group_id")

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

    def test_add_group(self):
        self.storage.add_group(self.group)
        result = self.storage.conn()['hcapi']['groups'].find_one(
            {"name": self.group.name})
        self.assertEqual(result["name"], self.group.name)
        result = self.storage.conn()['hcapi']['groups'].remove(
            {"name": self.group.name})

    def test_find_group_by_name(self):
        self.storage.add_group(self.group)
        result = self.storage.find_group_by_name(self.group.name)
        self.assertEqual(result.name, self.group.name)
        result = self.storage.conn()['hcapi']['groups'].remove(
            {"name": self.group.name})

    def test_remove_group(self):
        self.storage.add_group(self.group)
        result = self.storage.find_group_by_name(self.group.name)
        self.assertEqual(result.name, self.group.name)
        self.storage.remove_group(self.group)
        length = self.storage.conn()['hcapi']['groups'].find(
            {"name": self.group.name}).count()
        self.assertEqual(length, 0)

    def test_add_user(self):
        self.storage.add_user(self.user)
        result = self.storage.conn()['hcapi']['users'].find_one(
            {"email": self.user.email})
        self.assertEqual(result["email"], self.user.email)
        result = self.storage.conn()['hcapi']['users'].remove(
            {"email": self.user.email})

    def test_remove_user(self):
        self.storage.add_user(self.user)
        result = self.storage.conn()['hcapi']['users'].find_one(
            {"email": self.user.email})
        self.assertEqual(result["email"], self.user.email)
        self.storage.remove_user(self.user)
        length = self.storage.conn()['hcapi']['users'].find(
            {"email": self.user.email}).count()
        self.assertEqual(length, 0)

    def test_find_user_by_email(self):
        self.storage.add_user(self.user)
        result = self.storage.find_user_by_email(self.user.email)
        self.assertEqual(result.email, self.user.email)
        self.storage.remove_user(self.user)

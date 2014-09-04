# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
import mock
import os

from healthcheck.storage import Item, MongoStorage, User, HealthCheck, Jsonable


class JsonableTest(unittest.TestCase):

    def test_to_json(self):
        jsonable = Jsonable()
        jsonable.id = 1
        self.assertDictEqual(jsonable.to_json(), {"id": 1})


class HealthCheckTest(unittest.TestCase):

    def test_healthcheck(self):
        name = "myhc"
        group_id = "123"
        hc = HealthCheck(name=name, group_id=group_id)
        self.assertEqual(hc.name, name)
        self.assertEqual(hc.group_id, group_id)

    def test_to_json(self):
        hc = HealthCheck("myhc", id=1)
        self.assertDictEqual(hc.to_json(), {"name": "myhc", "id": 1})


class UserTest(unittest.TestCase):

    def test_user(self):
        id = "someid"
        email = "watcher@watcher.com"
        group_id = "anotherid"
        user = User(id, email, group_id)
        self.assertEqual(user.id, id)
        self.assertEqual(user.email, email)
        self.assertEqual(user.groups_id, (group_id,))

    def test_to_json(self):
        user = User("someid", "w@w.com", "id")
        expected = {"id": "someid", "email": "w@w.com", "groups_id": ("id",)}
        self.assertDictEqual(expected, user.to_json())


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
        self.user = User("id", "w@w.com", "group_id")
        self.healthcheck = HealthCheck("bla")

    @mock.patch("pymongo.MongoClient")
    def test_mongodb_host_environ(self, mongo_mock):
        self.storage.conn()
        mongo_mock.assert_called_with('mongodb://localhost:27017/')

        os.environ["MONGODB_URI"] = "mongodb://myhost:2222/"
        self.addCleanup(self.remove_env, "MONGODB_URI")
        storage = MongoStorage()
        storage.conn()
        mongo_mock.assert_called_with('mongodb://myhost:2222/')

    @mock.patch("pymongo.MongoClient")
    def test_mongodb_port_environ(self, mongo_mock):
        self.storage.conn()
        mongo_mock.assert_called_with('mongodb://localhost:27017/')

        os.environ["MONGODB_URI"] = "mongodb://myhost:2222/"
        self.addCleanup(self.remove_env, "MONGODB_URI")
        storage = MongoStorage()
        storage.conn()
        mongo_mock.assert_called_with('mongodb://myhost:2222/')

    def test_add_item(self):
        self.storage.add_item(self.item)
        result = self.storage.find_item_by_url(self.url)
        self.assertEqual(result.url, self.url)
        self.storage.remove_item(self.item)

    def test_find_item_by_url(self):
        self.storage.add_item(self.item)
        result = self.storage.find_item_by_url(self.item.url)
        for attr, value in result.__dict__.items():
            self.assertEqual(getattr(self.item, attr), value)
        self.storage.remove_item(self.item)

    def test_remove_item(self):
        self.storage.add_item(self.item)
        result = self.storage.find_item_by_url(self.item.url)
        self.assertEqual(result.url, self.url)
        self.storage.remove_item(self.item)
        length = self.storage.conn()['hcapi']['items'].find(
            {"url": self.url}).count()
        self.assertEqual(length, 0)

    def test_add_user(self):
        self.storage.add_user(self.user)
        result = self.storage.find_user_by_email(self.user.email)
        self.assertEqual(result.email, self.user.email)
        self.storage.remove_user(self.user)

    def test_add_healthcheck(self):
        self.storage.add_healthcheck(self.healthcheck)
        result = self.storage.find_healthcheck_by_name(self.healthcheck.name)
        self.assertEqual(result.name, self.healthcheck.name)
        self.storage.remove_healthcheck(self.healthcheck)

    def test_remove_healthcheck(self):
        self.storage.add_healthcheck(self.healthcheck)
        result = self.storage.find_healthcheck_by_name(self.healthcheck.name)
        self.assertEqual(result.name, self.healthcheck.name)
        self.storage.remove_healthcheck(self.healthcheck)
        length = self.storage.conn()['hcapi']['healthchecks'].find(
            {"name": self.healthcheck.name}).count()
        self.assertEqual(length, 0)

    def test_find_healthcheck_by_name(self):
        self.storage.add_healthcheck(self.healthcheck)
        result = self.storage.find_healthcheck_by_name(self.healthcheck.name)
        self.assertEqual(result.name, self.healthcheck.name)
        self.storage.remove_healthcheck(self.healthcheck)

    def test_remove_user(self):
        self.storage.add_user(self.user)
        result = self.storage.find_user_by_email(self.user.email)
        self.assertEqual(result.email, self.user.email)
        self.storage.remove_user(self.user)
        length = self.storage.conn()['hcapi']['users'].find(
            {"email": self.user.email}).count()
        self.assertEqual(length, 0)

    def test_find_user_by_email(self):
        self.storage.add_user(self.user)
        result = self.storage.find_user_by_email(self.user.email)
        self.assertEqual(result.email, self.user.email)
        self.storage.remove_user(self.user)

    def test_find_users_by_group(self):
        user1 = User("id1", "w@w.com", "group_id1", "group_id2", "group_id3")
        user2 = User("id2", "e@w.com", "group_id2", "group_id3")
        user3 = User("id3", "f@w.com", "group_id3")
        self.storage.add_user(user1)
        self.addCleanup(self.storage.remove_user, user1)
        self.storage.add_user(user2)
        self.addCleanup(self.storage.remove_user, user2)
        self.storage.add_user(user3)
        self.addCleanup(self.storage.remove_user, user3)
        users = self.storage.find_users_by_group("group_id3")
        self.assertEqual([user1, user2, user3], users)
        users = self.storage.find_users_by_group("group_id2")
        self.assertEqual([user1, user2], users)
        users = self.storage.find_users_by_group("group_id1")
        self.assertEqual([user1], users)

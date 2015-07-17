# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os


class Jsonable(object):

    def to_json(self):
        return self.__dict__


class HealthCheck(Jsonable):

    def __init__(self, name, **kwargs):
        self.name = name
        for key, value in kwargs.items():
            setattr(self, key, value)


class User(Jsonable):

    def __init__(self, id, email, *groups_id):
        self.email = email
        self.groups_id = groups_id
        self.id = id

    def __eq__(self, other):
        return other.email == self.email and \
            other.groups_id == self.groups_id and \
            other.id == self.id


class Item(Jsonable):

    def __init__(self, url, **kwargs):
        self.url = url
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_json(self):
        return self.__dict__


class MongoStorage(object):

    def __init__(self):
        self.database_name = os.environ.get("MONGODB_DATABASE", "hcapi")
        self.db = self.conn()[self.database_name]

    def conn(self):
        mongodb_uri = os.environ.get(
            "MONGODB_URI", "mongodb://localhost:27017/"
        )
        from pymongo import MongoClient
        return MongoClient(mongodb_uri)

    def add_item(self, item):
        self.db.items.insert(item.to_json())

    def find_item_by_url(self, url):
        result = self.db.items.find_one(
            {"url": url}
        )
        if not result:
            raise ItemNotFoundError()
        return Item(**result)

    def find_urls_by_healthcheck_name(self, name):
        items = []
        healthcheck = self.find_healthcheck_by_name(name)
        mgo_urls = self.db.items.find(
            {
                "group_id": healthcheck.group_id
            }, {"url": 1}
        )
        for url in mgo_urls:
            items.append(url['url'])
        return items

    def find_watchers_by_healthcheck_name(self, name):
        healthcheck = self.find_healthcheck_by_name(name)
        watchers = self.find_users_by_group(healthcheck.group_id)
        return [watcher.email for watcher in watchers]

    def remove_item(self, item):
        self.db.items.remove({"url": item.url})

    def add_user(self, user):
        self.db.users.insert(user.to_json())

    def remove_user(self, user):
        self.db.users.remove({"email": user.email})

    def add_healthcheck(self, healthcheck):
        self.db.healthchecks.insert(
            healthcheck.to_json()
        )

    def remove_healthcheck(self, healthcheck):
        self.db.healthchecks.remove(
            {"name": healthcheck.name}
        )

    def find_healthcheck_by_name(self, name):
        result = self.db.healthchecks.find_one(
            {"name": name}
        )
        if not result:
            raise HealthCheckNotFoundError()
        return HealthCheck(**result)

    def find_user_by_email(self, email):
        result = self.db.users.find_one(
            {"email": email}
        )
        if not result:
            raise UserNotFoundError()
        return User(result["id"], result["email"], *result["groups_id"])

    def find_users_by_group(self, group_id):
        items = self.db.users.find(
            {"groups_id": group_id},
        )
        return [User(r["id"], r["email"], *r["groups_id"]) for r in items]

    def add_user_to_group(self, user, group):
        self.db.users.update({"id": user.id}, {"$push": {"groups_id": group}})

    def remove_user_from_group(self, user, group):
        self.db.users.update({"id": user.id}, {"$pull": {"groups_id": group}})


class ItemNotFoundError(Exception):
    pass


class HealthCheckNotFoundError(Exception):
    pass


class UserNotFoundError(Exception):
    pass

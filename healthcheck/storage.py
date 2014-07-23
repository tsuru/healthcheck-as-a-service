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

    def __init__(self, id, email, group_id):
        self.email = email
        self.group_id = group_id
        self.id = id


class Item(Jsonable):

    def __init__(self, url, **kwargs):
        self.url = url
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_json(self):
        return self.__dict__


class MongoStorage(object):

    def conn(self):
        mongodb_host = os.environ.get("MONGODB_HOST", "localhost")
        mongodb_port = int(os.environ.get("MONGODB_PORT", 27017))

        from pymongo import MongoClient
        return MongoClient(host=mongodb_host, port=mongodb_port)

    def add_item(self, item):
        self.conn()['hcapi']['items'].insert(item.to_json())

    def find_item_by_url(self, url):
        result = self.conn()['hcapi']['items'].find_one({"url": url})
        return Item(**result)

    def remove_item(self, item):
        self.conn()['hcapi']['items'].remove({"url": item.url})

    def add_user(self, user):
        self.conn()['hcapi']['users'].insert(user.to_json())

    def remove_user(self, user):
        self.conn()['hcapi']['users'].remove({"email": user.email})

    def add_healthcheck(self, healthcheck):
        self.conn()['hcapi']['healthchecks'].insert(healthcheck.to_json())

    def remove_healthcheck(self, healthcheck):
        self.conn()['hcapi']['healthchecks'].remove({"name": healthcheck.name})

    def find_healthcheck_by_name(self, name):
        result = self.conn()['hcapi']['healthchecks'].find_one({"name": name})
        name = result.pop("name")
        return HealthCheck(name, **result)

    def find_user_by_email(self, email):
        result = self.conn()['hcapi']['users'].find_one({"email": email})
        return User(result["id"], result["email"], result["group_id"])

import os


class User(object):

    def __init__(self, id, email, group_id):
        self.email = email
        self.group_id = group_id
        self.id = id

    def to_json(self):
        return self.__dict__


class Group(object):

    def __init__(self, name, id):
        self.name = name
        self.id = id

    def to_json(self):
        return self.__dict__


class Item(object):

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
        return Item(result["url"])

    def remove_item(self, item):
        self.conn()['hcapi']['items'].remove({"url": item.url})

    def add_group(self, group):
        self.conn()['hcapi']['groups'].insert(group.to_json())

    def find_group_by_name(self, name):
        result = self.conn()['hcapi']['groups'].find_one({"name": name})
        return Group(result["name"], result["id"])

    def remove_group(self, group):
        self.conn()['hcapi']['groups'].remove({"name": group.name})

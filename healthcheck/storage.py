import os


class Group(object):

    def __init__(self, name):
        self.name = name

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

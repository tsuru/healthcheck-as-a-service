import os


class Item(object):

    def __init__(self, url):
        self.url = url

    def to_json(self):
        return {
            "url": self.url,
        }


class MongoStorage(object):

    def conn(self):
        mongodb_host = os.environ.get("MONGODB_HOST", "localhost")
        mongodb_port = int(os.environ.get("MONGODB_PORT", 27017))

        from pymongo import MongoClient
        return MongoClient(host=mongodb_host, port=mongodb_port)

    def add_item(self, item):
        self.conn()['hcapi']['items'].insert(item.to_json())

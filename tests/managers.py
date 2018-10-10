# Copyright 2015 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from healthcheck.storage import ItemNotFoundError


class FakeManager(object):
    def __init__(self):
        self.healthchecks = {}

    def add_url(self, name, url, expected_string=None, comment=""):
        item = {"url": url, "expected_string": expected_string, "comment": comment}
        self.healthchecks[name]["urls"].append(item)

    def list_urls(self, name):
        return [[item['url'], item['comment']] for item in self.healthchecks[name]['urls']]

    def remove_url(self, name, url):
        index = -1
        for i, u in enumerate(self.healthchecks[name]["urls"]):
            if u["url"] == url:
                index = i
                break
        if index > -1:
            self.healthchecks[name]["urls"].pop(index)
        else:
            raise ItemNotFoundError

    def new(self, name):
        self.healthchecks[name] = {"urls": [], "users": []}

    def add_watcher(self, name, email, password=None):
        self.healthchecks[name]["users"].append(email)

    def remove_watcher(self, name, email):
        self.healthchecks[name]["users"].remove(email)

    def list_watchers(self, name):
        return self.healthchecks[name]['users']

    def remove(self, name):
        del self.healthchecks[name]

# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.


class FakeManager(object):
    def __init__(self):
        self.healthchecks = {}

    def add_url(self, name, url, expected_string=None):
        item = {"url": url, "expected_string": expected_string}
        self.healthchecks[name]["urls"].append(item)

    def list_urls(self, name):
        return [item['url'] for item in self.healthchecks[name]['urls']]

    def remove_url(self, name, url):
        index = -1
        for i, u in enumerate(self.healthchecks[name]["urls"]):
            if u["url"] == u:
                index = i
                break
        if index > -1:
            self.healthchecks[name]["urls"].pop(index)

    def new(self, name):
        self.healthchecks[name] = {"urls": [], "users": []}

    def add_watcher(self, name, email):
        self.healthchecks[name]["users"].append(email)

    def remove_watcher(self, name, email):
        self.healthchecks[name]["users"].remove(email)

    def remove(self, name):
        del self.healthchecks[name]

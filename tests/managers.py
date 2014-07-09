# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.


class FakeManager(object):
    def __init__(self):
        self.healthchecks = {}

    def add_url(self, name, url):
        self.healthchecks[name]["urls"].append(url)

    def remove_url(self, name, url):
        self.healthchecks[name]["urls"].remove(url)

    def new(self, name):
        self.healthchecks[name] = {"urls": [], "users": []}

    def add_watcher(self, name, email):
        self.healthchecks[name]["users"].append(email)

    def remove_watcher(self, name, email):
        self.healthchecks[name]["users"].remove(email)

    def remove(self, name):
        del self.healthchecks[name]

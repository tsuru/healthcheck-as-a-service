# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.


class Action(object):

    def backward(self):
        raise NotImplementedError()

    def forward(self):
        raise NotImplementedError()


class Pipeline(object):

    def __init__(self, actions):
        self.actions = actions

    def execute(self, **kwargs):
        try:
            for action in self.actions:
                action.forward(**kwargs)
        except:
            self.rollback(action, **kwargs)

    def rollback(self, action, **kwargs):
        index = self.actions.index(action) - 1

        while index >= 0:
            action = self.actions[index]
            action.backward(**kwargs)
            index = index - 1

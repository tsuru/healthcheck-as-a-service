# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.


class Action(object):

    def backward(self):
        raise NotImplementedError()

    def forward(self):
        raise NotImplementedError()

# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest

from healthcheck.actions import Action


class ActionTest(unittest.TestCase):

    def test_interface(self):
        with self.assertRaises(NotImplementedError):
            Action().forward()

        with self.assertRaises(NotImplementedError):
            Action().backward()

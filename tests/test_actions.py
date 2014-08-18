# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest

import mock

from healthcheck.actions import Action, Pipeline


class ActionTest(unittest.TestCase):

    def test_interface(self):
        with self.assertRaises(NotImplementedError):
            Action().forward()

        with self.assertRaises(NotImplementedError):
            Action().backward()


class PipelineTest(unittest.TestCase):

    def test_pipeline(self):
        action = mock.Mock()
        pipeline = Pipeline(actions=[action])
        self.assertListEqual(pipeline.actions, [action])

    def test_execute(self):
        action = mock.Mock()
        pipeline = Pipeline(actions=[action])

        pipeline.execute()

        action.forward.assert_called_with()

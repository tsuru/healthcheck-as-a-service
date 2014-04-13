import unittest

from healthcheck import api


class APITestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = api.app.test_client()

    def test_add_url(self):
        resp = self.api.post("/url")
        self.assertEqual(201, resp.status_code)

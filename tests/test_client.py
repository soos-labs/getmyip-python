"""Тесты клиента: HTTP мокается на уровне urlopen, сеть не нужна."""

import io
import json
import unittest
from unittest import mock

from getmyip_pro import APIError, Client, Result


def fake_urlopen(payload: dict, status: int = 200):
    def opener(req, timeout=None):
        if status != 200:
            import urllib.error

            raise urllib.error.HTTPError(
                req.full_url, status, "err", {}, io.BytesIO(json.dumps(payload).encode())
            )
        m = mock.MagicMock()
        m.__enter__.return_value = io.BytesIO(json.dumps(payload).encode())
        m.__exit__.return_value = False
        return m

    return opener


SAMPLE = {"ip": "8.8.8.8", "country": "United States", "country_code": "US", "asn": 15169, "org": "Google LLC"}


class ClientTest(unittest.TestCase):
    def test_me(self):
        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen(SAMPLE)):
            r = Client().me()
        self.assertEqual(r.ip, "8.8.8.8")
        self.assertEqual(r.asn, 15169)

    def test_lookup_unknown_fields_survive(self):
        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen({**SAMPLE, "new_field": 1})):
            r = Client().lookup("8.8.8.8")
        self.assertEqual(r.extra["new_field"], 1)

    def test_batch(self):
        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen({"results": [SAMPLE, SAMPLE]})):
            rs = Client().batch(["8.8.8.8", "1.1.1.1"])
        self.assertEqual(len(rs), 2)
        self.assertIsInstance(rs[0], Result)

    def test_api_error(self):
        err = fake_urlopen({"error": "rate_limited"}, 429)
        # не parenthesized-with: файл должен парситься и на 3.9
        with mock.patch("urllib.request.urlopen", side_effect=err), self.assertRaises(APIError) as cm:
            Client().me()
        self.assertEqual(cm.exception.status, 429)
        self.assertEqual(cm.exception.error, "rate_limited")

    def test_api_key_and_user_agent_headers(self):
        captured = {}

        def opener(req, timeout=None):
            captured["key"] = req.get_header("X-api-key")
            captured["ua"] = req.get_header("User-agent")
            m = mock.MagicMock()
            m.__enter__.return_value = io.BytesIO(json.dumps(SAMPLE).encode())
            m.__exit__.return_value = False
            return m

        with mock.patch("urllib.request.urlopen", side_effect=opener):
            Client(api_key="k1").me()
        self.assertEqual(captured["key"], "k1")
        # дефолтный Python-urllib/* UA режется ботозащитой edge — клиент обязан слать свой
        self.assertTrue(captured["ua"].startswith("getmyip-pro-python/"), captured["ua"])


if __name__ == "__main__":
    unittest.main()

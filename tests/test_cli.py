"""Интеграционные тесты CLI: реальный HTTP-сервер на localhost, CLI наведён
через GETMYIP_BASE_URL."""

import contextlib
import io
import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from getmyip_pro.cli import main

ROUTES = {
    "/v1/json": (200, {"ip": "45.82.64.40", "country": "Netherlands", "country_code": "NL", "org": "WorldStream B.V.", "asn": 49981}),
    "/v1/8.8.8.8": (200, {"ip": "8.8.8.8", "country": "United States", "country_code": "US", "org": "Google LLC", "asn": 15169, "timezone": "America/Chicago"}),
    "/v1/bad": (400, {"error": "invalid ip"}),
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # имя из API BaseHTTPRequestHandler
        status, payload = ROUTES.get(self.path, (404, {"error": "not found"}))
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # тишина в тестах
        pass


class CLITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        os.environ["GETMYIP_BASE_URL"] = f"http://127.0.0.1:{cls.srv.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        os.environ.pop("GETMYIP_BASE_URL", None)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_human_lookup(self):
        code, out, _ = self.run_cli("8.8.8.8")
        self.assertEqual(code, 0)
        for want in ("IP:       8.8.8.8", "United States (US)", "Google LLC (AS15169)", "America/Chicago"):
            self.assertIn(want, out)

    def test_me(self):
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("45.82.64.40", out)

    def test_json(self):
        code, out, _ = self.run_cli("-json", "8.8.8.8")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["ip"], "8.8.8.8")

    def test_field(self):
        code, out, _ = self.run_cli("-field", "org", "8.8.8.8")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "Google LLC")

    def test_unknown_field(self):
        code, _, err = self.run_cli("-field", "nope", "8.8.8.8")
        self.assertEqual(code, 1)
        self.assertIn("unknown field", err)

    def test_api_error(self):
        code, _, err = self.run_cli("bad")
        self.assertEqual(code, 1)
        self.assertIn("invalid ip", err)


if __name__ == "__main__":
    unittest.main()

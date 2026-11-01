import json
import os
import shutil
import sys
import tempfile
import unittest
import urllib.error
import urllib.request

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server as server_module
from test_api import make_api

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestRouteTable(unittest.TestCase):
    def test_routes_parse_and_match_api(self):
        import webapp
        routes = server_module.load_routes(ROOT)
        self.assertGreater(len(routes), 50)
        api = webapp.DesktopApi(folder=tempfile.mkdtemp())
        try:
            self.assertEqual(server_module.check_routes_against(api, routes), [])
        finally:
            api.session.session_log_connection.close()

    def test_every_public_api_method_has_a_route(self):
        import inspect
        import webapp
        routes = server_module.load_routes(ROOT)
        handlers = {r["handler"] for r in routes.values()}
        public = {name for name, member in inspect.getmembers(webapp.DesktopApi, inspect.isfunction) if not name.startswith("_")}
        self.assertEqual(public - handlers, set(), f"API methods without a route: {public - handlers}")

    def test_paths_are_unique_per_method(self):
        routes = server_module.load_routes(ROOT)
        seen = set()
        for name, route in routes.items():
            key = (route["method"], route["path"])
            self.assertNotIn(key, seen, f"duplicate route {key} ({name})")
            seen.add(key)


class TestHttpServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.mkdtemp()
        shutil.copytree(os.path.join(ROOT, "web"), os.path.join(cls.folder, "web"))
        shutil.copytree(os.path.join(ROOT, "fonts"), os.path.join(cls.folder, "fonts"))
        import webapp
        cls.api = webapp.DesktopApi(folder=cls.folder)
        cls.api.session.session_log_connection.close()
        cls.api.session = make_api(cls.folder).session
        cls.server = server_module.ApiServer(cls.api, cls.folder).start()
        cls.base = f"http://127.0.0.1:{cls.server.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        if cls.api.session.connection:
            cls.api.session.connection.close()
        shutil.rmtree(cls.folder)

    def call(self, method, path, body=None, token=True, query=None):
        url = self.base + path
        if query:
            url += "?" + "&".join(f"{k}={v}" for k, v in query.items())
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("Content-Type", "application/json")
        if token:
            request.add_header("X-Iceberg-Token", self.server.token)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read().decode())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read().decode())

    def test_static_files_and_index(self):
        with urllib.request.urlopen(self.base + "/", timeout=10) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("text/html", response.headers["Content-Type"])
            self.assertIn("<title>Iceberg", response.read().decode())
        with urllib.request.urlopen(self.base + "/routes.js", timeout=10) as response:
            self.assertIn("javascript", response.headers["Content-Type"])
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(self.base + "/../api.py", timeout=10)
        self.assertEqual(raised.exception.code, 404)

    def test_token_required(self):
        status, payload = self.call("GET", "/api/status", token=False)
        self.assertEqual(status, 401)
        self.assertFalse(payload["ok"])
        status, payload = self.call("GET", "/api/status", token=False, query={"token": self.server.token})
        self.assertEqual(status, 200)

    def test_unknown_and_wrong_method(self):
        self.assertEqual(self.call("GET", "/api/nope")[0], 404)
        self.assertEqual(self.call("DELETE", "/api/status")[0], 405)

    def test_full_flow_over_http(self):
        status, payload = self.call("GET", "/api/status")
        self.assertEqual(status, 200)
        self.assertFalse(payload["database_loaded"])
        keys = os.path.join(self.folder, "keys")
        os.makedirs(keys, exist_ok=True)
        status, created = self.call("POST", "/api/databases", {"fields": {"business_name": "HTTP Books", "address": "1 Main", "sales_tax": "5", "save_location": keys, "receipts_location": self.folder}})
        self.assertEqual(status, 200)
        self.assertTrue(created["ok"], created)
        status, bad = self.call("POST", "/api/transactions", {"fields": {"name": "", "date": "x", "amount": "1", "debit_account": "10002", "credit_account": "10002"}})
        self.assertEqual(status, 200)
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["errors"][0]["field"], "name")
        status, added = self.call("POST", "/api/transactions", {"fields": {"name": "Rent", "date": "2025-01-05", "amount": "1200", "debit_account": "11010", "credit_account": "10002"}})
        self.assertTrue(added["ok"], added)
        status, ledger = self.call("GET", "/api/ledger", query={"search": "rent", "year": "2025"})
        self.assertEqual(len(ledger["rows"]), 1)
        status, one = self.call("GET", f"/api/transactions/{added['id']}")
        self.assertEqual(one["transaction"]["name"], "Rent")
        status, updated = self.call("PUT", f"/api/transactions/{added['id']}", {"fields": {"name": "Rent January", "date": "2025-01-05", "amount": "1200", "debit_account": "11010", "credit_account": "10002"}})
        self.assertTrue(updated["ok"], updated)
        status, dash = self.call("GET", "/api/dashboard", query={"type_prefix": "11"})
        self.assertTrue(all(a["id"].startswith("11") for a in dash["accounts"]))
        status, saved = self.call("POST", "/api/databases/save")
        self.assertTrue(saved["ok"], saved)
        status, periods = self.call("GET", "/api/reports/periods")
        self.assertIn("Balance Sheet", periods["types"])
        status, report = self.call("POST", "/api/reports/run", {"report_type": "Income Statement", "start": "2025-01-01", "end": "2025-12-31"})
        self.assertIn("Net Loss", report["text"])
        status, dialog = self.call("POST", "/api/dialogs/folder")
        self.assertEqual(status, 200)          # no window: a cancelled pick, not a failure
        self.assertTrue(dialog["ok"])
        self.assertIsNone(dialog["path"])

    def test_real_javascript_client_end_to_end(self):
        """routes.js + client.js in Node against this server: no mocks anywhere."""
        import shutil as _shutil
        import subprocess
        node = _shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        folder = tempfile.mkdtemp()
        _shutil.copytree(os.path.join(ROOT, "fonts"), os.path.join(folder, "fonts"))
        api = make_api(folder)
        import webapp
        desktop = webapp.DesktopApi(folder=folder)
        desktop.session.session_log_connection.close()
        desktop.session = api.session
        http = server_module.ApiServer(desktop, ROOT).start()
        try:
            env = dict(os.environ, ICEBERG_URL=f"http://127.0.0.1:{http.port}", ICEBERG_TOKEN=http.token, ICEBERG_KEYS=folder)
            result = subprocess.run([node, os.path.join(ROOT, "web", "tools", "e2e.js")], capture_output=True, text=True, timeout=120, env=env)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            summary = json.loads(result.stdout.strip().splitlines()[-1])
            self.assertEqual(summary["paid"], "Paid")
            self.assertEqual(summary["checking"], 1031875)
        finally:
            http.stop()
            if api.session.connection:
                api.session.connection.close()
            _shutil.rmtree(folder)

    def test_real_page_boots_in_jsdom(self):
        """The shipped index.html, every script it loads, against this server (needs node + jsdom)."""
        import shutil as _shutil
        import subprocess
        node = _shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        env = dict(os.environ, ICEBERG_URL=self.base, ICEBERG_TOKEN=self.server.token)
        env["NODE_PATH"] = os.pathsep.join(p for p in [os.environ.get("NODE_PATH", ""), "/tmp/jsdomtest/node_modules", os.path.join(ROOT, "node_modules")] if p)
        result = subprocess.run([node, "--test", "--test-timeout=40000", os.path.join(ROOT, "web", "tools", "page.test.js")], capture_output=True, text=True, timeout=60, env=env)
        if "jsdom not installed" in result.stdout:
            self.skipTest("jsdom is not installed (npm install jsdom)")
        self.assertEqual(result.returncode, 0, result.stdout[-3000:] + result.stderr[-2000:])

    def test_bad_json_body(self):
        request = urllib.request.Request(self.base + "/api/transactions", data=b"{not json", method="POST")
        request.add_header("X-Iceberg-Token", self.server.token)
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(request, timeout=10)
        self.assertEqual(raised.exception.code, 400)


if __name__ == "__main__":
    unittest.main()

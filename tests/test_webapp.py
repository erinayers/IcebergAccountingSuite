import inspect
import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestWebHost(unittest.TestCase):
    def test_host_imports_without_pywebview_and_exposes_api(self):
        import webapp
        api = webapp.DesktopApi(folder=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        try:
            public = {name for name, _ in inspect.getmembers(api, inspect.ismethod) if not name.startswith("_")}
            for required in ("status", "recent_databases", "create_database", "open_database", "save", "dashboard", "ledger",
                             "transaction", "transaction_form", "add_transaction", "update_transaction", "account_register",
                             "report", "report_periods", "autosave_if_due", "shutdown", "pick_key_file", "pick_folder", "pick_file", "open_path"):
                self.assertIn(required, public)
            self.assertFalse(api.status()["database_loaded"])
            self.assertIsNone(api.pick_folder()["path"])  # no window: a cancelled pick, not an error
        finally:
            api.session.session_log_connection.close()

    def test_front_end_files_reference_each_other(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "web", "index.html"), encoding="utf-8") as handle:
            html = handle.read()
        for name in ("app.css", "routes.js", "client.js", "render.js", "render_records.js", "render_tools.js", "app.js", "mock.js"):
            self.assertIn(name, html)
            self.assertTrue(os.path.isfile(os.path.join(root, "web", name)))

    def test_front_end_never_bypasses_the_client(self):
        """Screens talk to Api.* only; routes.js is the single contract (checked by tests/test_server.py)."""
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "web", "app.js"), encoding="utf-8") as handle:
            js = handle.read()
        self.assertNotIn("window.pywebview.api", js)
        self.assertNotIn("fetch(", js)
        self.assertIn("window.ApiClient.build", js)


if __name__ == "__main__":
    unittest.main()

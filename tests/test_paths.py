import os
import shutil
import sys
import tempfile
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paths


class TestPaths(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp)

    def test_default_user_data_dir_per_platform(self):
        self.assertEqual(paths.default_user_data_dir("win32", {"LOCALAPPDATA": r"C:\Users\u\AppData\Local"}, home="C:/Users/u"), os.path.join(r"C:\Users\u\AppData\Local", "Iceberg"))
        self.assertEqual(paths.default_user_data_dir("win32", {}, home="/h"), os.path.join("/h", "AppData", "Local", "Iceberg"))
        self.assertEqual(paths.default_user_data_dir("darwin", {}, home="/h"), "/h/Library/Application Support/Iceberg")
        self.assertEqual(paths.default_user_data_dir("linux", {}, home="/h"), "/h/.local/share/iceberg")
        self.assertEqual(paths.default_user_data_dir("linux", {"XDG_DATA_HOME": "/x"}, home="/h"), "/x/iceberg")

    def test_source_checkout_is_portable_packaged_build_is_not(self):
        self.assertTrue(paths.is_portable(self.temp, frozen=False))
        self.assertFalse(paths.is_portable(self.temp, frozen=True))
        open(os.path.join(self.temp, "portable.txt"), "w").close()
        self.assertTrue(paths.is_portable(self.temp, frozen=True))

    def test_data_root_precedence(self):
        custom = os.path.join(self.temp, "custom")
        self.assertEqual(paths.data_root(["--data-dir", custom], {}, self.temp, frozen=True), (os.path.abspath(custom), "custom"))
        self.assertEqual(paths.data_root(["--data-dir=" + custom], {"ICEBERG_DATA_DIR": "/ignored"}, self.temp, frozen=True), (os.path.abspath(custom), "custom"))
        self.assertEqual(paths.data_root([], {"ICEBERG_DATA_DIR": custom}, self.temp, frozen=True), (os.path.abspath(custom), "custom"))
        self.assertEqual(paths.data_root([], {}, self.temp, frozen=False), (self.temp, "portable"))
        root, mode = paths.data_root([], {}, self.temp, frozen=True)
        self.assertEqual(mode, "user")
        self.assertNotEqual(root, self.temp)

    def test_layout_user_vs_portable(self):
        user = paths.Layout(self.temp, "user", app_dir="/app", resources="/app").ensure()
        self.assertEqual(user.databases, os.path.join(self.temp, "databases"))
        self.assertTrue(os.path.isdir(user.databases))
        self.assertTrue(os.path.isdir(user.logs))
        self.assertEqual(user.fonts, os.path.join("/app", "fonts"))
        portable = paths.Layout(self.temp, "portable", app_dir=self.temp, resources=self.temp)
        self.assertEqual(portable.databases, self.temp)
        self.assertEqual(portable.backups, os.path.join(self.temp, "backups"))
        described = portable.describe()
        self.assertEqual(described["mode"], "portable")
        self.assertTrue(described["log_file"].endswith("iceberg.log"))

    def test_api_writes_into_the_layout(self):
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from test_api import make_api
        import api as api_module
        import db_calls
        from session import CONSOLE_LOG_SCHEMA, IcebergSession
        resources = os.path.join(self.temp, "app")
        shutil.copytree(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts"), os.path.join(resources, "fonts"))
        layout = paths.Layout(os.path.join(self.temp, "data"), "user", app_dir=resources, resources=resources)
        log = db_calls.create_connection(":memory:")
        db_calls.create_tables(log, CONSOLE_LOG_SCHEMA)
        api = api_module.IcebergApi(layout=layout, session=IcebergSession(session_log_connection=log))
        try:
            keys = os.path.join(self.temp, "keys")
            os.makedirs(keys)
            created = api.create_database({"business_name": "Layout Co", "address": "1 Main", "sales_tax": "0", "save_location": keys, "receipts_location": self.temp})
            self.assertTrue(created["ok"], created)
            self.assertTrue(os.path.isfile(os.path.join(layout.databases, "Layout_Co.icb")))
            api.add_transaction({"name": "x", "date": "2025-01-01", "amount": "1", "debit_account": "10002", "credit_account": "14001"})
            saved = api.save()
            self.assertTrue(saved["backup"].startswith(layout.backups))
            self.assertEqual(api.backups()["folder"], os.path.join(layout.backups, "Layout_Co"))
            self.assertTrue(os.path.isfile(layout.log_file))
            with open(layout.log_file, encoding="utf-8") as handle:
                self.assertIn("Database created", handle.read())
            self.assertEqual(api.status()["paths"]["mode"], "user")
            self.assertEqual(api.paths()["paths"]["databases"], layout.databases)
            api.save_preferences({"theme": "dark"})
            self.assertTrue(os.path.isfile(os.path.join(layout.root, "preferences.json")))
            self.assertEqual(api.recent_databases()[0]["backups"], 1)
        finally:
            api.session.connection.close()


if __name__ == "__main__":
    unittest.main()

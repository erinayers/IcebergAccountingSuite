import os
import shutil
import sys
import tempfile
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api as api_module
import books
import db_calls
from session import CONSOLE_LOG_SCHEMA, IcebergSession


def make_api(folder):
    log = db_calls.create_connection(":memory:")
    db_calls.create_tables(log, CONSOLE_LOG_SCHEMA)
    return api_module.IcebergApi(folder=folder, session=IcebergSession(session_log_connection=log))


class TestApi(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.keys = os.path.join(self.folder, "keys")
        os.makedirs(self.keys)
        self.api = make_api(self.folder)
        self.fields = {"business_name": "Eskin Ventures", "address": "1 Main St", "sales_tax": "6.25%",
                       "save_location": self.keys, "receipts_location": self.folder, "owner_name": "E. Skin"}

    def tearDown(self):
        if self.api.session.connection:
            self.api.session.connection.close()
        shutil.rmtree(self.folder)

    def test_status_without_database(self):
        status = self.api.status()
        self.assertFalse(status["database_loaded"])
        self.assertIsNone(status["autosave_in"])
        self.assertIn("Welcome", status["console"][0])
        self.assertFalse(self.api.dashboard()["ok"])
        self.assertFalse(self.api.ledger()["ok"])
        self.assertEqual(self.api.recent_databases(), [])

    def test_create_database_validates_fields(self):
        result = self.api.create_database(dict(self.fields, sales_tax="six", business_name=""))
        self.assertFalse(result["ok"])
        self.assertEqual({e["field"] for e in result["errors"]}, {"sales_tax", "business_name"})
        self.assertEqual(os.listdir(self.keys), [])

    def test_create_open_and_dashboard(self):
        result = self.api.create_database(self.fields)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["db_name"], "Eskin_Ventures.icb")
        self.assertTrue(os.path.isfile(os.path.join(self.folder, "Eskin_Ventures.icb")))
        self.assertTrue(os.path.isfile(result["key_path"]))
        self.assertFalse(db_calls.is_sqlite_file(os.path.join(self.folder, "Eskin_Ventures.icb")))
        status = self.api.status()
        self.assertTrue(status["database_loaded"])
        self.assertEqual(status["business_name"], "Eskin Ventures")
        self.assertFalse(status["unsaved"])
        dash = self.api.dashboard()
        self.assertTrue(dash["ok"])
        self.assertEqual(len(dash["accounts"]), len(books.DEFAULT_ACCOUNTS))
        self.assertTrue(dash["summary"]["in_balance"])
        self.assertEqual(self.api.properties_summary()["sales_tax"], "0.0625")
        recent = self.api.recent_databases()
        self.assertEqual(recent[0]["label"], "Eskin Ventures")

        # duplicate is refused before anything is written
        again = self.api.create_database(self.fields)
        self.assertFalse(again["ok"])
        self.assertIn("already exists", again["errors"][0]["message"])

        # reopen through the key file
        other = make_api(self.folder)
        opened = other.open_database(result["key_path"])
        self.assertTrue(opened["ok"], opened)
        self.assertEqual(other.status()["business_name"], "Eskin Ventures")
        other.session.connection.close()

    def test_open_errors_are_messages_not_exceptions(self):
        self.assertFalse(self.api.open_database("")["ok"])
        self.assertIn("filekey", self.api.open_database(os.path.join(self.folder, "x.txt"))["message"])
        db_calls.generate_filekey("missing.icb", self.keys)
        result = self.api.open_database(os.path.join(self.keys, "missing.icbkey"))
        self.assertFalse(result["ok"])
        self.assertIn("Database not found", result["message"])

    def test_transactions_round_trip_with_validation_and_save(self):
        self.api.create_database(self.fields)
        form = self.api.transaction_form()
        self.assertEqual(form["next_id"], 1)
        self.assertTrue(any(a["id"] == "10002" for a in form["accounts"]))

        bad = self.api.add_transaction({"name": "", "date": "2025-13-01", "amount": "x", "debit_account": "10002", "credit_account": "10002"})
        self.assertFalse(bad["ok"])
        self.assertEqual([e["field"] for e in bad["errors"]], ["name", "date", "amount", "credit_account"])

        good = {"name": "Owner investment", "date": "2025-01-02", "amount": "$10,000.00", "debit_account": "10002 - Checking", "credit_account": "14001", "notes": "seed money"}
        added = self.api.add_transaction(good)
        self.assertTrue(added["ok"], added)
        self.assertEqual(added["id"], 1)
        self.assertTrue(self.api.status()["unsaved"])

        duplicate = self.api.add_transaction(good)
        self.assertFalse(duplicate["ok"])
        self.assertTrue(duplicate["needs_confirmation"])
        confirmed = self.api.add_transaction(good, confirm_warnings=True)
        self.assertTrue(confirmed["ok"])

        ledger = self.api.ledger()
        self.assertEqual(len(ledger["rows"]), 2)
        self.assertEqual(ledger["rows"][0]["amount"], 1000000)
        self.assertEqual(ledger["rows"][0]["debit_name"], "Fixed Asset Bank Account Checking")
        self.assertEqual(ledger["years"], ["2025"])
        self.assertEqual(len(self.api.ledger(search="seed")["rows"]), 2)
        self.assertEqual(len(self.api.ledger(search="nothing here")["rows"]), 0)
        self.assertEqual(len(self.api.ledger(year="2024")["rows"]), 0)

        one = self.api.transaction(1)
        self.assertTrue(one["ok"])
        self.assertEqual(one["transaction"]["name"], "Owner investment")
        self.assertFalse(self.api.transaction(99)["ok"])

        updated = self.api.update_transaction(2, dict(good, name="Owner investment (dup)", amount="1"))
        self.assertTrue(updated["ok"])
        self.assertEqual(self.api.transaction(2)["transaction"]["amount"], 100)

        dash = self.api.dashboard()
        self.assertEqual(dash["summary"]["assets"], 1000100)
        self.assertEqual(dash["summary"]["owner_equity"], 1000100)
        checking = next(a for a in dash["accounts"] if a["id"] == "10002")
        self.assertEqual(checking["balance"], 1000100)
        expenses_only = self.api.dashboard(type_prefix="11")
        self.assertTrue(all(a["id"].startswith("11") for a in expenses_only["accounts"]))

        register = self.api.account_register("10002")
        self.assertTrue(register["ok"])
        self.assertEqual(register["account"]["balance"], 1000100)
        self.assertEqual(register["rows"][0]["running_balance"], 1000100)
        self.assertFalse(self.api.account_register("19999")["ok"])

        saved = self.api.save()
        self.assertTrue(saved["ok"], saved)
        self.assertFalse(self.api.status()["unsaved"])
        self.assertTrue(os.path.isfile(saved["backup"]))
        self.assertEqual(self.api.recent_databases()[0]["backups"], 1)

    def test_autosave_only_when_due_and_dirty(self):
        self.api.create_database(self.fields)
        self.assertTrue(self.api.autosave_if_due()["ok"])
        self.api.session.last_autosave -= 10_000
        self.assertEqual(self.api.autosave_if_due()["message"], "")   # nothing changed, nothing written
        self.api.add_transaction({"name": "x", "date": "2025-01-01", "amount": "1", "debit_account": "10002", "credit_account": "14001"})
        self.api.session.last_autosave -= 10_000
        self.assertIn("Autosave", self.api.autosave_if_due()["message"])

    def test_reports(self):
        self.api.create_database(self.fields)
        self.api.add_transaction({"name": "Sale", "date": "2025-02-01", "amount": "250", "debit_account": "10002", "credit_account": "15001"})
        result = self.api.report("Income Statement", "2025-01-01", "2025-12-31")
        self.assertTrue(result["ok"])
        self.assertIn("Net Income", result["text"])
        self.assertFalse(self.api.report("Income Statement", "bad", "2025-12-31")["ok"])
        self.assertFalse(self.api.report("Income Statement", "2025-12-31", "2025-01-01")["ok"])
        self.assertFalse(self.api.report("Nope", "2025-01-01", "2025-12-31")["ok"])
        periods = self.api.report_periods()
        self.assertIn("Balance Sheet", periods["types"])
        self.assertTrue(all(p["start"] <= p["end"] for p in periods["presets"]))

    def test_unexpected_errors_become_messages(self):
        self.api.create_database(self.fields)
        self.api.session.ledger_name = "tbl_does_not_exist"
        result = self.api.add_transaction({"name": "x", "date": "2025-01-01", "amount": "1", "debit_account": "10002", "credit_account": "14001"})
        self.assertFalse(result["ok"])
        self.assertIn("Something went wrong", result["message"])

    def test_shutdown_saves_into_the_api_folder(self):
        self.api.create_database(self.fields)
        self.api.add_transaction({"name": "x", "date": "2025-01-01", "amount": "1", "debit_account": "10002", "credit_account": "14001"})
        self.assertTrue(self.api.shutdown()["ok"])
        self.assertFalse(self.api.status()["unsaved"])
        self.assertTrue(os.path.isfile(os.path.join(self.folder, "sessions.icbs")))   # written next to the database, never in the cwd


class TestBooks(unittest.TestCase):
    def test_chart_of_accounts_year_semantics(self):
        from fixtures import LEDGER, make_database, seed_sample_books
        import accounting
        from repository import AccountRepository
        conn = seed_sample_books(make_database())
        rows = accounting.read_ledger(conn, LEDGER)
        accounts = AccountRepository(conn).get_all()
        chart = {a["id"]: a for a in books.chart_of_accounts(rows, accounts)}
        self.assertEqual(chart["10002"]["balance"], 1000000 - 120000 - 4218 - 120000 + 250000 - 120000 - 50000 - 500000 + 10000)
        self.assertEqual(chart["13002"]["balance"], 20000)
        expenses_2024 = books.chart_of_accounts(rows, accounts, "11", "2024")
        self.assertTrue(all(a["balance"] == 0 for a in expenses_2024))      # temporary: that year only
        assets_2024 = books.chart_of_accounts(rows, accounts, "10", "2024")
        self.assertTrue(all(a["balance"] == 0 for a in assets_2024))        # nothing posted before 2025
        summary = books.dashboard_summary(rows, accounts)
        self.assertTrue(summary["in_balance"])
        self.assertEqual(summary["business_income"], 280000 - 384218)
        self.assertEqual(books.ledger_years(rows), ["2025"])
        found = books.search_ledger(rows, "rent", None, accounting.account_name_map(accounts))
        self.assertEqual(len(found), 3)
        self.assertEqual(found[0]["Transaction_Date"], "2025-03-01")


if __name__ == "__main__":
    unittest.main()

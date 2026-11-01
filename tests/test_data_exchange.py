import csv
import os
import shutil
import sys
import tempfile
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import accounting
import data_exchange
import reports
from fixtures import LEDGER, make_database, seed_sample_books
from repository import AccountRepository


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


class TestExports(unittest.TestCase):
    def setUp(self):
        self.conn = seed_sample_books(make_database())
        self.accounts = AccountRepository(self.conn).get_all()
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp)

    def test_export_ledger_has_names_and_dollars(self):
        path, count = data_exchange.export_ledger(self.conn, LEDGER, self.accounts, os.path.join(self.temp, "ledger.csv"))
        rows = read_csv(path)
        self.assertEqual(count, 11)
        self.assertEqual(rows[0][:6], ["Transaction_ID", "Transaction_Date", "Name", "Amount", "Debit_Account", "Debit_Account_Name"])
        self.assertEqual(rows[1][1:6], ["2025-01-02", "Owner investment", "10000.00", "10002", "Checking"])

    def test_export_ledger_period(self):
        _, count = data_exchange.export_ledger(self.conn, LEDGER, self.accounts, os.path.join(self.temp, "feb.csv"), "2025-02-01", "2025-02-28")
        self.assertEqual(count, 2)

    def test_export_table_converts_money_columns(self):
        self.conn.execute(
            "INSERT INTO tbl_Invoices (Invoice_ID, Customer_ID, Tracking_Code, Line_Items, Due_Date, Created_Time, Edited_Time, Subtotal, Sales_Tax, Total, Status, Payment_Method, Location) "
            "VALUES (10001, 1, 'X', '[]', '2025-02-01', '2025-01-15T12:00:00+00:00', '2025-01-15T12:00:00+00:00', 10000, 625, 10625, 'Due', '', '')"
        )
        self.conn.commit()
        path, count = data_exchange.export_table(self.conn, "tbl_Invoices", os.path.join(self.temp, "inv.csv"))
        rows = read_csv(path)
        header = rows[0]
        self.assertEqual(count, 1)
        self.assertEqual(rows[1][header.index("Total")], "106.25")
        self.assertIn("(UTC", rows[1][header.index("Created_Time")])

    def test_export_empty_table_writes_header_only(self):
        path, count = data_exchange.export_table(self.conn, "tbl_Customers", os.path.join(self.temp, "c.csv"))
        self.assertEqual(count, 0)
        self.assertEqual(read_csv(path)[0][0], "Customer_ID")

    def test_export_report(self):
        rows = accounting.read_ledger(self.conn, LEDGER)
        report = reports.income_statement(rows, self.accounts, "2025-01-01", "2025-03-31")
        path = data_exchange.export_report(report, os.path.join(self.temp, "pl.csv"))
        content = read_csv(path)
        self.assertEqual(content[0], ["Section", "Line", "Amount"])
        self.assertIn(["Summary", "Net Loss", "-1042.18"], content)
        monthly = reports.income_statement_by_month(rows, self.accounts, "2025-01-01", "2025-02-28")
        content = read_csv(data_exchange.export_report(monthly, os.path.join(self.temp, "m.csv")))
        self.assertEqual(content[3][1:], ["Account", "Jan 2025", "Feb 2025", "Total"])

    def test_export_all(self):
        written = data_exchange.export_all(self.conn, LEDGER, self.accounts, os.path.join(self.temp, "out"))
        self.assertIn("ledger", written)
        self.assertIn("accounts", written)
        self.assertNotIn("reconciliations", written)  # optional table not present
        self.assertTrue(all(os.path.isfile(p) for p, _ in written.values()))


class TestImports(unittest.TestCase):
    def setUp(self):
        self.conn = seed_sample_books(make_database())
        self.ids = [str(a["Account_ID"]) for a in AccountRepository(self.conn).get_all()]
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp)

    def write(self, name, text):
        path = os.path.join(self.temp, name)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return path

    def test_template_round_trips(self):
        path = data_exchange.write_import_template(os.path.join(self.temp, "template.csv"))
        result = data_exchange.import_transactions(self.conn, LEDGER, path, self.ids)
        self.assertEqual(result["imported"], 2)
        self.assertEqual(result["transaction_ids"], [12, 13])
        rows = accounting.read_ledger(self.conn, LEDGER)
        self.assertEqual(rows[-1]["Name"], "Client payment")
        self.assertEqual(rows[-1]["Amount"], 150000)

    def test_header_aliases_and_bom(self):
        path = self.write("alias.csv", "\ufeffdate,description,amount,debit,credit,memo\n12/21/2025,Lunch,$12.50,11001 Office,10004,client\n")
        result = data_exchange.import_transactions(self.conn, LEDGER, path, self.ids)
        self.assertEqual(result["imported"], 1)
        row = accounting.read_ledger(self.conn, LEDGER)[-1]
        self.assertEqual((row["Transaction_Date"], row["Amount"], row["Debit_Acct"], row["Credit_Acct"], row["Notes"]), ("2025-12-21", 1250, "11001", "10004", "client"))

    def test_missing_column(self):
        path = self.write("bad.csv", "Date,Name,Amount\n2025-01-01,x,1\n")
        with self.assertRaises(data_exchange.ImportError_) as raised:
            data_exchange.import_transactions(self.conn, LEDGER, path, self.ids)
        self.assertIn("Debit_Account", str(raised.exception))

    def test_invalid_rows_block_whole_import(self):
        path = self.write(
            "mixed.csv",
            "Date,Name,Amount,Debit_Account,Credit_Account\n"
            "2025-01-01,Good,10.00,11001,10002\n"
            "2025-13-01,Bad date,10.00,11001,10002\n"
            "2025-01-03,Bad account,10.00,19999,10002\n"
            "2025-01-04,Same account,10.00,10002,10002\n",
        )
        before = len(accounting.read_ledger(self.conn, LEDGER))
        with self.assertRaises(data_exchange.ImportError_) as raised:
            data_exchange.import_transactions(self.conn, LEDGER, path, self.ids)
        self.assertEqual(len(raised.exception.errors), 3)
        self.assertTrue(raised.exception.errors[0].startswith("Line 3:"))
        self.assertEqual(len(accounting.read_ledger(self.conn, LEDGER)), before)

    def test_dry_run_and_duplicate_warnings(self):
        existing = accounting.read_ledger(self.conn, LEDGER)
        path = self.write(
            "dup.csv",
            "Date,Name,Amount,Debit_Account,Credit_Account\n"
            "2025-01-10,Printer paper,42.18,11001,10002\n"
            "2025-05-01,New,1.00,11001,10002\n"
            "2025-05-01,New,1.00,11001,10002\n",
        )
        result = data_exchange.import_transactions(self.conn, LEDGER, path, self.ids, existing_rows=existing, dry_run=True)
        self.assertEqual(result["imported"], 0)
        self.assertEqual(len(result["warnings"]), 2)
        self.assertIn("already exists", result["warnings"][0])
        self.assertIn("duplicate of an earlier line", result["warnings"][1])
        self.assertEqual(len(accounting.read_ledger(self.conn, LEDGER)), len(existing))

    def test_empty_file(self):
        path = self.write("empty.csv", "Date,Name,Amount,Debit_Account,Credit_Account\n\n")
        with self.assertRaises(data_exchange.ImportError_):
            data_exchange.import_transactions(self.conn, LEDGER, path, self.ids)

    def test_missing_file(self):
        with self.assertRaises(data_exchange.ImportError_):
            data_exchange.import_transactions(self.conn, LEDGER, os.path.join(self.temp, "nope.csv"), self.ids)


if __name__ == "__main__":
    unittest.main()

import datetime
import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import accounting
import reports
from fixtures import LEDGER, make_database, seed_sample_books
from repository import AccountRepository


class TestPeriods(unittest.TestCase):
    def test_presets(self):
        today = datetime.date(2025, 5, 14)
        self.assertEqual(reports.period_bounds("This Year", today), ("2025-01-01", "2025-12-31"))
        self.assertEqual(reports.period_bounds("Last Year", today), ("2024-01-01", "2024-12-31"))
        self.assertEqual(reports.period_bounds("This Month", today), ("2025-05-01", "2025-05-31"))
        self.assertEqual(reports.period_bounds("Last Month", today), ("2025-04-01", "2025-04-30"))
        self.assertEqual(reports.period_bounds("This Quarter", today), ("2025-04-01", "2025-06-30"))
        self.assertEqual(reports.period_bounds("Last Quarter", today), ("2025-01-01", "2025-03-31"))
        self.assertEqual(reports.period_bounds("Year to Date", today), ("2025-01-01", "2025-05-14"))
        self.assertEqual(reports.period_bounds("Last Quarter", datetime.date(2025, 2, 1)), ("2024-10-01", "2024-12-31"))
        with self.assertRaises(ValueError):
            reports.period_bounds("Whenever", today)


class TestReports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = seed_sample_books(make_database())
        cls.rows = accounting.read_ledger(cls.conn, LEDGER)
        cls.accounts = AccountRepository(cls.conn).get_all()

    def section(self, report, title):
        return next(s for s in report["sections"] if s["title"] == title)

    def test_income_statement_for_quarter(self):
        report = reports.income_statement(self.rows, self.accounts, "2025-01-01", "2025-03-31")
        revenue = self.section(report, "Revenue")
        expenses = self.section(report, "Expenses")
        self.assertEqual(revenue["total"], 280000)
        self.assertEqual(expenses["total"], 3 * 120000 + 4218 + 20000)
        self.assertEqual(dict(expenses["lines"])["11010 Rent or Lease of Real Property"], 360000)
        self.assertEqual(report["summary"], [("Net Loss", 280000 - 384218)])
        self.assertEqual(report["transaction_count"], 10)

    def test_income_statement_excludes_other_periods(self):
        report = reports.income_statement(self.rows, self.accounts, "2025-02-01", "2025-02-28")
        self.assertEqual(self.section(report, "Revenue")["total"], 250000)
        self.assertEqual(self.section(report, "Expenses")["total"], 120000)
        self.assertEqual(report["summary"][0], ("Net Income", 130000))

    def test_income_statement_by_month(self):
        report = reports.income_statement_by_month(self.rows, self.accounts, "2025-01-01", "2025-03-31")
        self.assertEqual(report["columns"], ["Account", "Jan 2025", "Feb 2025", "Mar 2025", "Total"])
        net = report["table"][-1]
        self.assertEqual(net[0], "Net Income")
        self.assertEqual(net[1:], [-124218, 130000, 280000 - 250000 - 120000 - 20000, 280000 - 384218])
        rent = next(r for r in report["table"] if r[0].startswith("11010"))
        self.assertEqual(rent[1:], [120000, 120000, 120000, 360000])

    def test_balance_sheet_balances(self):
        report = reports.balance_sheet(self.rows, self.accounts, "2025-03-31")
        assets = self.section(report, "Assets")
        liabilities = self.section(report, "Liabilities")
        equity = self.section(report, "Equity")
        self.assertEqual(dict(assets["lines"])["10001 Fixed Asset Real Estate"], 500000)
        self.assertEqual(dict(assets["lines"])["10004 Cash"], 30000)
        self.assertEqual(liabilities["total"], 20000)
        self.assertEqual(dict(equity["lines"])["14001 Owner Equity Deposits"], 1000000)
        retained = dict(equity["lines"])["Retained Earnings (revenue - expenses - withdrawals)"]
        self.assertEqual(retained, 280000 - 384218 - 50000)
        self.assertTrue(report["balanced"])
        self.assertEqual(assets["total"], liabilities["total"] + equity["total"])

    def test_balance_sheet_as_of_earlier_date(self):
        report = reports.balance_sheet(self.rows, self.accounts, "2025-01-31")
        self.assertEqual(self.section(report, "Assets")["total"], 1000000 - 124218)
        self.assertTrue(report["balanced"])

    def test_cash_flow(self):
        report = reports.cash_flow(self.rows, self.accounts, "2025-01-01", "2025-03-31")
        self.assertEqual(report["cash_accounts"], ["10002", "10004"])
        operating = self.section(report, "Operating Activities")
        investing = self.section(report, "Investing Activities")
        financing = self.section(report, "Financing Activities")
        self.assertEqual(operating["total"], 280000 - 360000 - 4218)  # supplier on credit is not cash
        self.assertEqual(investing["total"], -500000)
        self.assertEqual(financing["total"], 1000000 - 50000)
        summary = dict(report["summary"])
        self.assertEqual(summary["Cash at Beginning of Period"], 0)
        self.assertEqual(summary["Net Change in Cash"], 280000 - 364218 - 500000 + 950000)
        self.assertEqual(summary["Cash at End of Period"], summary["Net Change in Cash"])

    def test_cash_flow_treats_receivables_and_payables_as_operating(self):
        from fixtures import add_transaction, make_database
        conn = make_database()
        add_transaction(conn, "2025-01-05", "Invoice 1", 10000, "10006", "15001")        # no cash yet
        add_transaction(conn, "2025-01-20", "Invoice 1 Paid", 10000, "10002", "10006")   # collection
        add_transaction(conn, "2025-01-25", "Pay supplier", 4000, "13002", "10002")      # A/P payment
        add_transaction(conn, "2025-01-26", "Refund", 500, "15001", "10002")
        add_transaction(conn, "2025-01-27", "Re-sale", 500, "10002", "15001")            # nets to zero with the refund
        rows = accounting.read_ledger(conn, LEDGER)
        accounts = AccountRepository(conn).get_all()
        report = reports.cash_flow(rows, accounts, "2025-01-01", "2025-01-31")
        operating = self.section(report, "Operating Activities")
        self.assertEqual(dict(operating["lines"]), {"10006 Accounts Receivable": 10000, "13002 Accounts Payable": -4000})
        self.assertEqual(self.section(report, "Investing Activities")["lines"], [])
        self.assertEqual(dict(report["summary"])["Net Change in Cash"], 6000)

    def test_cash_flow_ignores_transfers_between_cash_accounts(self):
        report = reports.cash_flow(self.rows, self.accounts, "2025-04-01", "2025-04-30")
        self.assertEqual(report["transfers_between_cash_accounts"], 10000)
        self.assertEqual(dict(report["summary"])["Net Change in Cash"], 0)
        self.assertEqual(dict(report["summary"])["Cash at Beginning of Period"], 280000 - 364218 - 500000 + 950000)

    def test_run_dispatch_and_render(self):
        for kind in reports.REPORT_TYPES:
            report = reports.run(kind, self.rows, self.accounts, "2025-01-01", "2025-03-31")
            text = reports.render_text(report)
            self.assertIn(report["title"], text)
            rows = reports.report_rows(report)
            self.assertEqual(rows[0][0], "Report")
        text = reports.render_text(reports.run("Income Statement", self.rows, self.accounts, "2025-01-01", "2025-03-31"))
        self.assertIn("Net Loss", text)
        self.assertIn("($1,042.18)", text)
        with self.assertRaises(ValueError):
            reports.run("Nope", self.rows, self.accounts, "2025-01-01", "2025-03-31")

    def test_render_flags_unbalanced_books(self):
        report = reports.balance_sheet(self.rows, self.accounts, "2025-03-31")
        report["balanced"] = False
        self.assertIn("WARNING", reports.render_text(report))

    def test_is_cash_account(self):
        self.assertTrue(reports.is_cash_account({"Account_ID": 10002, "Institution": ""}))
        self.assertTrue(reports.is_cash_account({"Account_ID": 10009, "Institution": "Credit Union"}))
        self.assertFalse(reports.is_cash_account({"Account_ID": 10001, "Institution": ""}))
        self.assertFalse(reports.is_cash_account({"Account_ID": 13001, "Institution": "Bank"}))


if __name__ == "__main__":
    unittest.main()

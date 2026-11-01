import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import accounting
import invoice_lifecycle as life
from fixtures import LEDGER, make_database
from repository import InvoiceRepository


def make_invoice(conn, invoice_id=10001, status="Due", subtotal=10000, tax=625):
    repo = InvoiceRepository(conn)
    repo.insert(
        invoice_id=invoice_id, customer_id=1, tracking_code=f"CODE{invoice_id}", line_items='[["S1","Thing","$100.00","1","$100.00"]]',
        due_date="2025-02-01", created_time="2025-01-15T12:00:00+00:00", edited_time="2025-01-15T12:00:00+00:00",
        subtotal=subtotal, sales_tax=tax, total=subtotal + tax, status=status, payment_method="", location="/tmp/x.pdf",
    )
    return repo.get_by_id(invoice_id)


def ledger(conn):
    return accounting.read_ledger(conn, LEDGER)


class TestTransitions(unittest.TestCase):
    def test_allowed_and_rejected(self):
        self.assertIsNone(life.check_transition("Due", "Paid"))
        self.assertIsNone(life.check_transition("Overdue", "Canceled"))
        self.assertIsNone(life.check_transition("Paid", "Refunded"))
        self.assertIn("already", life.check_transition("Due", "Due"))
        self.assertIn("refund it instead", life.check_transition("Paid", "Canceled"))
        self.assertIn("Only a paid invoice", life.check_transition("Due", "Refunded"))
        self.assertIn("can only change to", life.check_transition("Refunded", "Paid"))
        self.assertIn("not an invoice status", life.check_transition("Due", "Lost"))
        self.assertEqual(life.allowed_transitions("Canceled"), set())


class TestPosting(unittest.TestCase):
    def setUp(self):
        self.conn = make_database()

    def test_post_due_invoice_debits_receivable(self):
        invoice = make_invoice(self.conn)
        ids = life.post_invoice(self.conn, LEDGER, invoice, date="2025-01-15")
        rows = ledger(self.conn)
        self.assertEqual(ids, [1, 2])
        self.assertEqual((rows[0]["Debit_Acct"], rows[0]["Credit_Acct"], rows[0]["Amount"], rows[0]["Name"]), ("10006", "15001", 10000, "Invoice 10001"))
        self.assertEqual((rows[1]["Debit_Acct"], rows[1]["Credit_Acct"], rows[1]["Amount"], rows[1]["Name"]), ("10006", "13003", 625, "Invoice 10001 Sales Tax"))
        self.assertEqual(rows[0]["Notes"], "CODE10001")
        history = life.history(self.conn, 10001)
        self.assertEqual(len(history), 1)
        self.assertEqual((history[0]["Event"], history[0]["To_Status"], history[0]["Amount"], history[0]["Transaction_IDs"]), ("Invoice created", "Due", 10625, "1,2"))

    def test_post_paid_invoice_uses_deposit_account_and_skips_zero_tax(self):
        invoice = make_invoice(self.conn, status="Paid", tax=0)
        ids = life.post_invoice(self.conn, LEDGER, invoice, deposit_account="10002", date="2025-01-15")
        self.assertEqual(ids, [1])
        row = ledger(self.conn)[0]
        self.assertEqual((row["Debit_Acct"], row["Credit_Acct"]), ("10002", "15001"))
        with self.assertRaises(life.InvoiceError):
            life.post_invoice(self.conn, LEDGER, make_invoice(self.conn, 10002, status="Paid"))

    def test_full_lifecycle_due_paid_refunded(self):
        invoice = make_invoice(self.conn)
        life.post_invoice(self.conn, LEDGER, invoice, date="2025-01-15")
        repo = InvoiceRepository(self.conn)

        overdue = life.change_status(self.conn, LEDGER, invoice, "Overdue", date="2025-02-05", invoice_repo=repo)
        self.assertTrue(overdue["ok"], overdue["message"])
        self.assertEqual(overdue["transaction_ids"], [])
        self.assertEqual(repo.get_by_id(10001)["Status"], "Overdue")

        paid = life.change_status(self.conn, LEDGER, invoice, "Paid", account="10002", date="2025-02-10", invoice_repo=repo)
        self.assertTrue(paid["ok"])
        self.assertEqual(paid["transaction_ids"], [3, 4])
        rows = ledger(self.conn)
        self.assertEqual((rows[2]["Debit_Acct"], rows[2]["Credit_Acct"], rows[2]["Amount"]), ("10002", "10006", 10000))
        self.assertEqual((rows[3]["Debit_Acct"], rows[3]["Credit_Acct"], rows[3]["Amount"]), ("10002", "10006", 625))
        balances = accounting.balances(rows, ["10006", "10002", "15001", "13003"])
        self.assertEqual(balances, {"10006": 0, "10002": 10625, "15001": 10000, "13003": 625})

        refunded = life.change_status(self.conn, LEDGER, invoice, "Refunded", account="10002", date="2025-02-20", invoice_repo=repo)
        self.assertTrue(refunded["ok"])
        rows = ledger(self.conn)
        self.assertEqual((rows[4]["Debit_Acct"], rows[4]["Credit_Acct"], rows[4]["Amount"]), ("15001", "10002", 10000))
        self.assertEqual((rows[5]["Debit_Acct"], rows[5]["Credit_Acct"], rows[5]["Amount"]), ("13003", "10002", 625))
        balances = accounting.balances(rows, ["10006", "10002", "15001", "13003"])
        self.assertEqual(balances, {"10006": 0, "10002": 0, "15001": 0, "13003": 0})

        events = [(h["Event"], h["From_Status"], h["To_Status"]) for h in life.history(self.conn, 10001)]
        self.assertEqual(events, [
            ("Invoice created", None, "Due"),
            ("Marked overdue", "Due", "Overdue"),
            ("Payment received", "Overdue", "Paid"),
            ("Refund issued", "Paid", "Refunded"),
        ])
        final = life.change_status(self.conn, LEDGER, invoice, "Paid", account="10002", invoice_repo=repo)
        self.assertFalse(final["ok"])
        self.assertEqual(len(ledger(self.conn)), 6)

    def test_cancel_reverses_receivable(self):
        invoice = make_invoice(self.conn)
        life.post_invoice(self.conn, LEDGER, invoice, date="2025-01-15")
        result = life.change_status(self.conn, LEDGER, invoice, "Canceled", date="2025-01-20")
        self.assertTrue(result["ok"], result["message"])
        balances = accounting.balances(ledger(self.conn), ["10006", "15001", "13003"])
        self.assertEqual(balances, {"10006": 0, "15001": 0, "13003": 0})
        self.assertEqual(self.conn.execute("SELECT Status FROM tbl_Invoices WHERE Invoice_ID = 10001").fetchone()[0], "Canceled")

    def test_paid_requires_account_and_writes_nothing_otherwise(self):
        invoice = make_invoice(self.conn)
        life.post_invoice(self.conn, LEDGER, invoice, date="2025-01-15")
        result = life.change_status(self.conn, LEDGER, invoice, "Paid")
        self.assertFalse(result["ok"])
        self.assertIn("deposit account", result["message"])
        self.assertEqual(len(ledger(self.conn)), 2)
        self.assertEqual(len(life.history(self.conn, 10001)), 1)
        self.assertEqual(invoice["Status"], "Due")

    def test_rejected_transition_writes_nothing(self):
        invoice = make_invoice(self.conn)
        life.post_invoice(self.conn, LEDGER, invoice, date="2025-01-15")
        result = life.change_status(self.conn, LEDGER, invoice, "Refunded", account="10002")
        self.assertFalse(result["ok"])
        self.assertEqual(len(ledger(self.conn)), 2)


class TestTimeline(unittest.TestCase):
    def setUp(self):
        self.conn = make_database()
        self.names = {"10002": "Checking", "10006": "Accounts Receivable", "15001": "Sales", "13003": "Sales Tax Payable"}

    def test_timeline_merges_history_and_ledger(self):
        invoice = make_invoice(self.conn)
        life.post_invoice(self.conn, LEDGER, invoice, date="2025-01-15")
        life.change_status(self.conn, LEDGER, invoice, "Paid", account="10002", date="2025-02-10")
        items = life.timeline(self.conn, LEDGER, invoice, self.names)
        self.assertEqual([i["event"] for i in items], ["Invoice created", "Payment received"])
        self.assertEqual(items[1]["account"], "10002 Checking")
        self.assertEqual(items[1]["transactions"], [3, 4])
        rows = life.timeline_rows(items)
        self.assertEqual(rows[1][1:], ["Payment received", "Due -> Paid", "$106.25", "10002 Checking", "3, 4"])

    def test_legacy_invoice_without_history_is_derived_from_ledger(self):
        invoice = make_invoice(self.conn)
        # Entries written by an older version: same tracking code in Notes, no history rows.
        self.conn.execute(
            f"INSERT INTO {LEDGER} (Credit_Acct, Debit_Acct, Amount, Name, Notes, Created_Time, Edited_Time, Transaction_Date, Record_Image, Vendor, Customer) "
            f"VALUES ('15001','10006',10000,'Invoice 10001','CODE10001','Sunday, 12/21/2025  -  17:47 EDT','x','2025-12-21','','','1')"
        )
        self.conn.execute(
            f"INSERT INTO {LEDGER} (Credit_Acct, Debit_Acct, Amount, Name, Notes, Created_Time, Edited_Time, Transaction_Date, Record_Image, Vendor, Customer) "
            f"VALUES ('10006','10002',10000,'Invoice 10001 Paid','CODE10001','Sunday, 12/22/2025  -  09:00 EDT','x','2025-12-22','','','1')"
        )
        self.conn.commit()
        items = life.timeline(self.conn, LEDGER, invoice, self.names)
        self.assertEqual([i["source"] for i in items], ["invoice", "ledger", "ledger"])
        self.assertEqual(items[1]["event"], "Ledger: Invoice 10001")
        self.assertEqual(items[2]["account"], "Dr 10002 Checking / Cr 10006 Accounts Receivable")


if __name__ == "__main__":
    unittest.main()

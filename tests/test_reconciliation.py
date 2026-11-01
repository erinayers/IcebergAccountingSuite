import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import accounting
import reconciliation
from fixtures import LEDGER, add_transaction, make_database, seed_sample_books


class TestAccountingCore(unittest.TestCase):
    def test_signed_effect_follows_normal_balance(self):
        deposit = {"Amount": 100, "Debit_Acct": "10002", "Credit_Acct": "15001"}
        self.assertEqual(accounting.signed_effect("10002", deposit), 100)   # asset grows
        self.assertEqual(accounting.signed_effect("15001", deposit), 100)   # revenue grows
        self.assertEqual(accounting.signed_effect("11001", deposit), 0)
        payable = {"Amount": 50, "Debit_Acct": "11001", "Credit_Acct": "13002"}
        self.assertEqual(accounting.signed_effect("13002", payable), 50)    # liability grows on credit
        self.assertEqual(accounting.signed_effect("11001", payable), 50)

    def test_balances_and_next_id(self):
        conn = seed_sample_books(make_database())
        rows = accounting.read_ledger(conn, LEDGER)
        totals = accounting.balances(rows, ["10002", "10004", "15001"])
        self.assertEqual(totals["10002"], 1000000 - 120000 - 4218 - 120000 + 250000 - 120000 - 50000 - 500000 + 10000)
        self.assertEqual(totals["10004"], 30000 - 10000)
        self.assertEqual(totals["15001"], 280000)
        self.assertEqual(accounting.next_transaction_id(conn, LEDGER), 12)
        self.assertEqual(len(accounting.read_ledger(conn, LEDGER, "2025-02-01", "2025-02-28")), 2)


class TestReconciliation(unittest.TestCase):
    def setUp(self):
        self.conn = seed_sample_books(make_database())

    def test_schema_migration_is_idempotent(self):
        reconciliation.ensure_schema(self.conn, LEDGER)
        reconciliation.ensure_schema(self.conn, LEDGER)
        self.assertIn("Reconciled_Date", accounting.ledger_columns(self.conn, LEDGER))

    def test_start_lists_unreconciled_transactions_through_date(self):
        session = reconciliation.start(self.conn, LEDGER, "10002", "2025-02-28")
        ids = [c["Transaction_ID"] for c in session["candidates"]]
        self.assertEqual(ids, [1, 2, 3, 4, 5])
        self.assertEqual(session["candidates"][0]["Amount"], 1000000)
        self.assertEqual(session["candidates"][1]["Amount"], -120000)
        self.assertEqual(session["candidates"][1]["Counter_Account"], "11010")
        self.assertEqual(session["reconciled_balance"], 0)

    def test_summary_and_unmatched(self):
        session = reconciliation.start(self.conn, LEDGER, "10002", "2025-02-28")
        # Statement shows everything except the February rent (not yet cleared by the bank).
        statement_balance = 1000000 - 120000 - 4218 + 250000
        summary = reconciliation.summarize(session, [1, 2, 3, 5], statement_balance)
        self.assertTrue(summary["balanced"])
        self.assertEqual(summary["difference"], 0)
        self.assertEqual(summary["cleared_count"], 4)
        self.assertEqual([u["Transaction_ID"] for u in summary["unmatched"]], [4])
        self.assertEqual(summary["unmatched_total"], -120000)
        off = reconciliation.summarize(session, [1, 2, 3], statement_balance)
        self.assertFalse(off["balanced"])
        self.assertEqual(off["difference"], 250000)

    def test_complete_marks_transactions_and_records_statement(self):
        session = reconciliation.start(self.conn, LEDGER, "10002", "2025-02-28")
        balance = 1000000 - 120000 - 4218 + 250000
        summary = reconciliation.complete(self.conn, LEDGER, session, [1, 2, 3, 5], balance)
        self.assertEqual(summary["cleared_balance"], balance)
        flagged = self.conn.execute(f"SELECT Transaction_ID FROM {LEDGER} WHERE Reconciled_Date = '2025-02-28' ORDER BY 1").fetchall()
        self.assertEqual([r[0] for r in flagged], [1, 2, 3, 5])
        history = reconciliation.history(self.conn, "10002")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["Statement_Balance"], balance)
        self.assertEqual(history[0]["Transaction_IDs"], "1,2,3,5")

        # Next statement starts from the reconciled balance and only offers what is left.
        nxt = reconciliation.start(self.conn, LEDGER, "10002", "2025-03-31")
        self.assertEqual(nxt["reconciled_balance"], balance)
        self.assertEqual([c["Transaction_ID"] for c in nxt["candidates"]], [4, 6, 8, 9])
        march_balance = balance - 120000 - 120000 - 50000 - 500000
        self.assertTrue(reconciliation.summarize(nxt, [4, 6, 8, 9], march_balance)["balanced"])

    def test_complete_refuses_unbalanced(self):
        session = reconciliation.start(self.conn, LEDGER, "10002", "2025-02-28")
        with self.assertRaises(reconciliation.ReconciliationError) as raised:
            reconciliation.complete(self.conn, LEDGER, session, [1], 5)
        self.assertIn("differs from the cleared balance", str(raised.exception))
        self.assertEqual(self.conn.execute(f"SELECT COUNT(*) FROM {LEDGER} WHERE Reconciled_Date IS NOT NULL").fetchone()[0], 0)

    def test_later_reconciled_flagged_when_statement_date_is_earlier(self):
        session = reconciliation.start(self.conn, LEDGER, "10002", "2025-03-31")
        reconciliation.complete(self.conn, LEDGER, session, [1, 2, 3, 4, 5, 6, 8, 9], 1000000 - 120000 - 4218 - 120000 + 250000 - 120000 - 50000 - 500000)
        earlier = reconciliation.start(self.conn, LEDGER, "10002", "2025-01-31")
        self.assertEqual(len(earlier["later_reconciled"]), 5)
        self.assertEqual(earlier["candidates"], [])

    def test_undo_last(self):
        session = reconciliation.start(self.conn, LEDGER, "10002", "2025-02-28")
        reconciliation.complete(self.conn, LEDGER, session, [1, 2, 3, 5], 1000000 - 120000 - 4218 + 250000)
        record = reconciliation.undo_last(self.conn, LEDGER, "10002")
        self.assertEqual(record["Transaction_IDs"], "1,2,3,5")
        self.assertEqual(reconciliation.history(self.conn, "10002"), [])
        self.assertEqual(self.conn.execute(f"SELECT COUNT(*) FROM {LEDGER} WHERE Reconciled_Date IS NOT NULL").fetchone()[0], 0)
        with self.assertRaises(reconciliation.ReconciliationError):
            reconciliation.undo_last(self.conn, LEDGER, "10002")

    def test_credit_card_style_liability_account(self):
        add_transaction(self.conn, "2025-04-10", "Card purchase", 7500, "11001", "13002")
        add_transaction(self.conn, "2025-04-20", "Card payment", 20000, "13002", "10002")
        session = reconciliation.start(self.conn, LEDGER, "13002", "2025-04-30")
        amounts = {c["Transaction_ID"]: c["Amount"] for c in session["candidates"]}
        self.assertEqual(amounts[10], 20000)   # supplier on credit raises the balance owed
        self.assertEqual(amounts[12], 7500)
        self.assertEqual(amounts[13], -20000)  # payment lowers it
        self.assertTrue(reconciliation.summarize(session, [10, 12, 13], 7500)["balanced"])


if __name__ == "__main__":
    unittest.main()

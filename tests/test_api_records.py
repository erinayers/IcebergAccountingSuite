"""API coverage for accounts, vendors, customers, services, invoices,
reconciliation, properties, backups, import/export, preferences."""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import accounting
from test_api import make_api

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ApiCase(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.keys = os.path.join(self.folder, "keys")
        self.receipts = os.path.join(self.folder, "receipts")
        os.makedirs(self.keys)
        os.makedirs(self.receipts)
        shutil.copytree(os.path.join(ROOT, "fonts"), os.path.join(self.folder, "fonts"))
        self.api = make_api(self.folder)
        created = self.api.create_database({"business_name": "O'Brien & Sons", "address": "1 Main St", "sales_tax": "6.25",
                                            "save_location": self.keys, "receipts_location": self.receipts, "owner_name": "Pat O'Brien",
                                            "phone": "555-0100", "email": "pat@example.com"})
        self.assertTrue(created["ok"], created)

    def tearDown(self):
        if self.api.session.connection:
            self.api.session.connection.close()
        shutil.rmtree(self.folder)

    def ledger_rows(self):
        return accounting.read_ledger(self.api.session.connection, self.api.session.ledger_name)


class TestAccounts(ApiCase):
    def test_add_update_and_validate(self):
        form = self.api.account_form()
        self.assertEqual(form["types"][0]["prefix"], "10")
        added = self.api.add_account({"type_prefix": "11", "name": "Software subscriptions", "notes": "SaaS"})
        self.assertTrue(added["ok"], added)
        self.assertEqual(added["id"], "11019")
        self.assertEqual(self.api.add_account({"type_prefix": "14", "name": "Investor capital"})["id"], "14002")
        dup = self.api.add_account({"type_prefix": "11", "name": " software SUBSCRIPTIONS "})
        self.assertFalse(dup["ok"])
        self.assertEqual(dup["errors"][0]["field"], "name")
        self.assertFalse(self.api.add_account({"type_prefix": "", "name": "x"})["ok"])
        updated = self.api.update_account("11019", {"name": "Software", "institution": "", "notes": "renamed"})
        self.assertTrue(updated["ok"])
        self.assertEqual(self.api.account("11019")["account"]["name"], "Software")
        self.assertFalse(self.api.update_account("11019", {"name": "Advertising"})["ok"])  # clashes with a default account
        self.assertFalse(self.api.account("19999")["ok"])


class TestVendorsCustomersServices(ApiCase):
    def test_vendors(self):
        self.assertEqual(self.api.vendors()["vendors"], [])
        added = self.api.save_vendor({"name": "O'Reilly Supplies", "email": "shop@example.com", "phone": "555-1234", "phone_type": "Office"})
        self.assertTrue(added["ok"], added)
        vid = added["id"]
        self.assertFalse(self.api.save_vendor({"name": "o'reilly supplies"})["ok"])
        self.assertEqual(self.api.save_vendor({"name": "x", "email": "nope"})["errors"][0]["field"], "email")
        self.assertEqual(self.api.vendors("reilly")["vendors"][0]["name"], "O'Reilly Supplies")
        self.assertTrue(self.api.save_vendor({"name": "O'Reilly Supplies Ltd", "phone_type": "Mobile"}, vid)["ok"])
        self.assertEqual(self.api.vendor(vid)["vendor"]["name"], "O'Reilly Supplies Ltd")
        self.assertFalse(self.api.save_vendor({"name": "z"}, "999")["ok"])
        self.assertIn("1", self.api.transaction_form()["vendors"][0]["id"])

    def test_customers(self):
        added = self.api.save_customer({"company": "Globex", "first_name": "Hank", "last_name": "Scorpio", "address": "1 Volcano Ln", "email": "h@globex.com"})
        self.assertTrue(added["ok"], added)
        cid = added["id"]
        self.assertFalse(self.api.save_customer({"company": "globex", "first_name": "hank", "last_name": "scorpio", "address": "x"})["ok"])
        self.assertEqual(self.api.save_customer({"company": "NoAddress"})["errors"][0]["field"], "address")
        listed = self.api.customers("glob")["customers"]
        self.assertEqual(listed[0]["display_name"], "Globex")
        self.assertEqual(listed[0]["balance"], 0)
        self.assertTrue(self.api.save_customer({"company": "Globex Corp", "first_name": "Hank", "last_name": "Scorpio", "address": "2 Volcano Ln"}, cid)["ok"])
        one = self.api.customer(cid)
        self.assertEqual(one["customer"]["company"], "Globex Corp")
        self.assertEqual(one["invoices"], [])

    def test_services(self):
        added = self.api.save_service({"description": "Consulting hour", "price": "150", "taxable": "False"})
        self.assertTrue(added["ok"], added)
        self.assertEqual(added["id"], "10001")
        self.assertEqual(self.api.save_service({"description": "Parts", "price": "$19.99", "taxable": True})["id"], "10002")
        self.assertFalse(self.api.save_service({"description": "consulting HOUR", "price": "1", "taxable": "True"})["ok"])
        self.assertEqual(self.api.save_service({"description": "x", "price": "abc", "taxable": "True"})["errors"][0]["field"], "price")
        services = self.api.services()["services"]
        self.assertEqual(services[1]["price"], 1999)
        self.assertTrue(services[1]["taxable"])
        self.assertTrue(self.api.save_service({"description": "Consulting hour", "price": "175", "taxable": "False"}, "10001")["ok"])
        self.assertEqual(self.api.services("consult")["services"][0]["price"], 17500)


class TestInvoices(ApiCase):
    def setUp(self):
        super().setUp()
        self.cid = self.api.save_customer({"company": "Globex", "first_name": "Hank", "last_name": "Scorpio", "address": "1 Volcano Ln"})["id"]
        self.api.save_service({"description": "Consulting hour", "price": "100", "taxable": "False"})
        self.api.save_service({"description": "Widget", "price": "10", "taxable": "True"})

    def test_form_line_items_and_totals(self):
        form = self.api.invoice_form()
        self.assertEqual(form["next_id"], 10001)
        self.assertEqual(form["sales_tax_rate"], "0.0625")
        self.assertEqual(len(form["services"]), 2)
        self.assertTrue(all(a["id"] != "10006" for a in form["asset_accounts"]))
        item = self.api.invoice_line_item("10002", "3")
        self.assertTrue(item["ok"], item)
        self.assertEqual(item["line_item"], ["10002", "Widget", "$10.00", "3", "$30.00"])
        self.assertFalse(self.api.invoice_line_item("10002", "0")["ok"])
        self.assertFalse(self.api.invoice_line_item("99999", "1")["ok"])
        hours = self.api.invoice_line_item("10001", "1.5")["line_item"]
        totals = self.api.invoice_totals([item["line_item"], hours])
        self.assertEqual((totals["subtotal"], totals["sales_tax"], totals["total"]), (18000, 188, 18188))
        self.assertEqual(self.api.invoice_totals([item["line_item"]], "0")["sales_tax"], 0)

    def test_create_due_invoice_posts_ledger_and_pdf(self):
        item = self.api.invoice_line_item("10002", "2")["line_item"]
        result = self.api.create_invoice({"customer_id": self.cid, "status": "Due", "due_date": "2025-02-01"}, [item])
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["id"], 10001)
        self.assertEqual(result["ledger_entries"], [1, 2])
        self.assertTrue(os.path.isfile(result["pdf"]), result)
        self.assertTrue(result["pdf"].endswith(os.path.join("Invoices", "10001", "10001.pdf")))
        rows = self.ledger_rows()
        self.assertEqual((rows[0]["Debit_Acct"], rows[0]["Credit_Acct"], rows[0]["Amount"]), ("10006", "15001", 2000))
        self.assertEqual((rows[1]["Debit_Acct"], rows[1]["Credit_Acct"], rows[1]["Amount"]), ("10006", "13003", 125))
        detail = self.api.invoice(10001)
        self.assertEqual(detail["invoice"]["status"], "Due")
        self.assertEqual(detail["invoice"]["customer_name"], "Globex")
        self.assertEqual(detail["invoice"]["line_items"], [item])
        self.assertEqual(detail["history"][0][1], "Invoice created")
        self.assertEqual(detail["invoice"]["allowed_transitions"], ["Canceled", "Overdue", "Paid"])
        self.assertEqual(self.api.customers()["customers"][0]["balance"], 2125)
        self.assertEqual(self.api.customer(self.cid)["invoices"][0]["id"], 10001)
        self.assertEqual(self.api.invoices("glob")["invoices"][0]["id"], 10001)
        self.assertEqual(self.api.invoice_pdf_path(10001)["path"], result["pdf"])

    def test_create_validation(self):
        self.assertFalse(self.api.create_invoice({"customer_id": "", "status": "Due", "due_date": ""}, [])["ok"])
        bad = self.api.create_invoice({"customer_id": self.cid, "status": "Paid", "due_date": "2025-02-01", "deposit_account": "10006"}, [self.api.invoice_line_item("10001", "1")["line_item"]])
        self.assertEqual(bad["errors"][0]["field"], "deposit_account")
        self.assertEqual(len(self.ledger_rows()), 0)

    def test_paid_invoice_then_refund_through_status_change(self):
        item = self.api.invoice_line_item("10001", "2")["line_item"]
        result = self.api.create_invoice({"customer_id": self.cid, "status": "Paid", "due_date": "2025-02-01", "deposit_account": "10002"}, [item])
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["ledger_entries"], [1])   # no tax entry for a non-taxable service
        self.assertEqual(self.ledger_rows()[0]["Debit_Acct"], "10002")
        refused = self.api.change_invoice_status(10001, "Canceled")
        self.assertFalse(refused["ok"])
        self.assertIn("refund it instead", refused["message"])
        needs_account = self.api.change_invoice_status(10001, "Refunded")
        self.assertFalse(needs_account["ok"])
        refunded = self.api.change_invoice_status(10001, "Refunded", "10002")
        self.assertTrue(refunded["ok"], refunded)
        self.assertEqual(refunded["status"], "Refunded")
        balances = accounting.balances(self.ledger_rows(), ["10002", "15001"])
        self.assertEqual(balances, {"10002": 0, "15001": 0})
        history = self.api.invoice(10001)["history"]
        self.assertEqual([h[1] for h in history], ["Invoice created", "Refund issued"])
        self.assertFalse(self.api.change_invoice_status(99999, "Paid")["ok"])

    def test_pdf_failure_is_reported_not_fatal(self):
        self.api.update_properties({"business_name": "O'Brien & Sons", "address": "1 Main St", "sales_tax": "6.25", "receipts_location": self.folder})
        shutil.rmtree(self.receipts)
        self.api.properties["receipts_location"] = self.receipts
        item = self.api.invoice_line_item("10001", "1")["line_item"]
        result = self.api.create_invoice({"customer_id": self.cid, "status": "Due", "due_date": "2025-02-01"}, [item])
        self.assertTrue(result["ok"])
        self.assertIn("PDF not written", result["message"])
        self.assertEqual(result["pdf"], "")
        self.assertFalse(self.api.invoice_pdf_path(10001)["ok"])


class TestReconciliation(ApiCase):
    def setUp(self):
        super().setUp()
        for date, name, amount, debit, credit in [("2025-01-02", "Owner investment", "10000", "10002", "14001"), ("2025-01-05", "Rent", "1200", "11010", "10002"),
                                                  ("2025-02-01", "Rent Feb", "1200", "11010", "10002")]:
            self.api.add_transaction({"name": name, "date": date, "amount": amount, "debit_account": debit, "credit_account": credit})

    def test_full_cycle(self):
        self.assertFalse(self.api.reconcile_start("10002", "bad", "1")["ok"])
        self.assertFalse(self.api.reconcile_start("19999", "2025-01-31", "1")["ok"])
        started = self.api.reconcile_start("10002", "2025-01-31", "8,800.00")
        self.assertTrue(started["ok"], started)
        self.assertEqual([c["Transaction_ID"] for c in started["candidates"]], [1, 2])
        self.assertFalse(started["summary"]["balanced"])
        summary = self.api.reconcile_summary([1, 2])
        self.assertTrue(summary["summary"]["balanced"])
        self.assertEqual(summary["summary"]["difference"], 0)
        self.assertFalse(self.api.reconcile_finish([1])["ok"])
        finished = self.api.reconcile_finish([1, 2])
        self.assertTrue(finished["ok"], finished)
        self.assertEqual(finished["cleared_count"], 2)
        self.assertFalse(self.api.status()["unsaved"])  # finishing saves
        history = self.api.reconcile_history("10002")["history"]
        self.assertEqual(history[0]["statement_balance"], 880000)
        self.assertEqual(self.api.ledger()["rows"][-1]["reconciled"], "2025-01-31")
        nxt = self.api.reconcile_start("10002", "2025-02-28", "7,600.00")
        self.assertEqual([c["Transaction_ID"] for c in nxt["candidates"]], [3])
        self.assertTrue(self.api.reconcile_undo("10002")["ok"])
        self.assertEqual(self.api.reconcile_history("10002")["history"], [])
        self.assertFalse(self.api.reconcile_undo("10002")["ok"])
        self.assertFalse(self.api.reconcile_summary([])["ok"])


class TestPropertiesBackupsExchange(ApiCase):
    def test_properties(self):
        self.assertEqual(self.api.properties_summary()["business_name"], "O'Brien & Sons")
        bad = self.api.update_properties({"business_name": "", "address": "x", "sales_tax": "1", "receipts_location": self.receipts})
        self.assertEqual(bad["errors"][0]["field"], "business_name")
        good = self.api.update_properties({"business_name": "O'Brien & Daughters", "address": "2 Main St", "sales_tax": "7%", "receipts_location": self.receipts, "email": "new@example.com"})
        self.assertTrue(good["ok"], good)
        self.assertEqual(good["properties"]["business_name"], "O'Brien & Daughters")
        self.assertEqual(good["properties"]["sales_tax"], "0.07")
        self.assertEqual(self.api.status()["business_name"], "O'Brien & Daughters")
        self.assertEqual(self.api.invoice_form()["sales_tax_rate"], "0.07")

    def test_backups_and_restore(self):
        self.api.add_transaction({"name": "Keep me", "date": "2025-01-01", "amount": "1", "debit_account": "10002", "credit_account": "14001"})
        self.api.save()
        listed = self.api.backups()
        self.assertEqual(len(listed["backups"]), 1)
        backup = listed["backups"][0]["path"]
        self.api.add_transaction({"name": "Mistake", "date": "2025-01-02", "amount": "5", "debit_account": "10002", "credit_account": "14001"})
        self.api.save()
        self.assertEqual(len(self.api.ledger()["rows"]), 2)
        restored = self.api.restore_backup(backup)
        self.assertTrue(restored["ok"], restored)
        self.assertEqual([r["name"] for r in self.api.ledger()["rows"]], ["Keep me"])
        self.assertTrue(os.path.isfile(restored["safety_copy"]))
        self.assertFalse(self.api.restore_backup(os.path.join(self.folder, "nope.icb"))["ok"])

    def test_import_export(self):
        self.api.add_transaction({"name": "Sale", "date": "2025-02-01", "amount": "250", "debit_account": "10002", "credit_account": "15001"})
        out = os.path.join(self.folder, "ledger.csv")
        self.assertEqual(self.api.export_ledger(out)["count"], 1)
        everything = self.api.export_all(os.path.join(self.folder, "all"))
        self.assertTrue(everything["ok"])
        self.assertIn("ledger", everything["files"])
        self.assertFalse(self.api.export_report(os.path.join(self.folder, "r.csv"))["ok"])
        self.api.report("Income Statement", "2025-01-01", "2025-12-31")
        self.assertTrue(self.api.export_report(os.path.join(self.folder, "r.csv"))["ok"])
        template = os.path.join(self.folder, "template.csv")
        self.assertTrue(self.api.import_template(template)["ok"])
        preview = self.api.import_transactions(template)
        self.assertTrue(preview["ok"], preview)
        self.assertTrue(preview["needs_confirmation"])
        self.assertEqual(preview["preview"], 2)
        done = self.api.import_transactions(template, confirm=True)
        self.assertEqual(done["imported"], 2)
        self.assertEqual(len(self.api.ledger()["rows"]), 3)
        with open(os.path.join(self.folder, "bad.csv"), "w") as handle:
            handle.write("Date,Name,Amount,Debit_Account,Credit_Account\n2025-01-01,x,abc,11001,10002\n")
        bad = self.api.import_transactions(os.path.join(self.folder, "bad.csv"))
        self.assertFalse(bad["ok"])
        self.assertEqual(len(bad["problems"]), 1)

    def test_preferences_and_console(self):
        prefs = self.api.preferences()
        self.assertEqual(prefs["preferences"]["theme"], "light")
        saved = self.api.save_preferences({"theme": "dark", "text_scale": 1.3, "compact": True})
        self.assertTrue(saved["ok"])
        self.assertEqual(self.api.preferences()["preferences"]["theme"], "dark")
        self.assertTrue(os.path.isfile(os.path.join(self.folder, "preferences.json")))
        self.assertTrue(any("Database created" in line for line in self.api.console()["lines"]))


if __name__ == "__main__":
    unittest.main()

import datetime
import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import validation

ACCOUNTS = ["10002", "10004", "11001", "15001"]


class TestPrimitives(unittest.TestCase):
    def test_parse_amount_accepts_common_formats(self):
        self.assertEqual(validation.parse_amount("125"), 12500)
        self.assertEqual(validation.parse_amount("$1,234.50"), 123450)
        self.assertEqual(validation.parse_amount(" 0.05 "), 5)
        self.assertEqual(validation.parse_amount("(12.00)"), -1200)
        self.assertEqual(validation.parse_amount("-12.00"), -1200)
        self.assertEqual(validation.parse_amount(10.5), 1050)

    def test_parse_amount_rejects_bad_input(self):
        for bad in ["", None, "abc", "12.345", "1e3x"]:
            with self.assertRaises(ValueError):
                validation.parse_amount(bad)
        with self.assertRaises(ValueError):
            validation.parse_amount("0")
        self.assertEqual(validation.parse_amount("0", allow_zero=True), 0)
        with self.assertRaises(ValueError):
            validation.parse_amount("999999999999999")

    def test_parse_date(self):
        self.assertEqual(validation.parse_date("2025-12-21"), "2025-12-21")
        self.assertEqual(validation.parse_date("12/21/2025"), "2025-12-21")
        self.assertEqual(validation.parse_date("2025/12/21"), "2025-12-21")
        for bad in ["", "2025-13-01", "31/12/2025", "yesterday-ish", "1850-01-01", "2025-02-30"]:
            with self.assertRaises(ValueError, msg=bad):
                validation.parse_date(bad)

    def test_parse_account_id(self):
        self.assertEqual(validation.parse_account_id("10002"), "10002")
        self.assertEqual(validation.parse_account_id("10002 - Checking"), "10002")
        self.assertEqual(validation.parse_account_id("15001 Sales"), "15001")
        for bad in ["", "1002", "20001", "abc"]:
            with self.assertRaises(ValueError):
                validation.parse_account_id(bad)


class TestTransaction(unittest.TestCase):
    def good(self, **overrides):
        fields = {"name": "Rent", "date": "2025-03-01", "amount": "1,200.00", "debit_account": "11001 - Office", "credit_account": "10002 - Checking"}
        fields.update(overrides)
        return fields

    def test_valid_transaction_is_cleaned(self):
        result = validation.validate_transaction(self.good(), ACCOUNTS)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.cleaned["amount"], 120000)
        self.assertEqual(result.cleaned["debit_account"], "11001")
        self.assertEqual(result.cleaned["credit_account"], "10002")
        self.assertEqual(result.cleaned["date"], "2025-03-01")

    def test_missing_required_fields(self):
        result = validation.validate_transaction({"name": "", "date": "", "amount": "", "debit_account": "", "credit_account": ""}, ACCOUNTS)
        self.assertFalse(result.ok)
        self.assertEqual(len(result.errors), 5)
        self.assertIn("Transaction name is required.", result.errors)

    def test_same_accounts(self):
        result = validation.validate_transaction(self.good(credit_account="11001"), ACCOUNTS)
        self.assertIn("Debit and credit accounts must be different.", result.errors)

    def test_unknown_account(self):
        result = validation.validate_transaction(self.good(debit_account="11999"), ACCOUNTS)
        self.assertIn("Debit account 11999 does not exist in the chart of accounts.", result.errors)

    def test_negative_amount_has_helpful_message(self):
        result = validation.validate_transaction(self.good(amount="-5"), ACCOUNTS)
        self.assertTrue(any("swap the debit and credit" in e for e in result.errors))

    def test_invalid_date(self):
        result = validation.validate_transaction(self.good(date="03/45/2025"), ACCOUNTS)
        self.assertTrue(any("not a valid date" in e for e in result.errors))

    def test_duplicate_is_a_warning_not_an_error(self):
        existing = [{"Transaction_ID": 7, "Name": "rent", "Transaction_Date": "2025-03-01", "Amount": 120000, "Debit_Acct": "11001", "Credit_Acct": "10002"}]
        result = validation.validate_transaction(self.good(), ACCOUNTS, existing=existing)
        self.assertTrue(result.ok)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("Transaction 7", result.warnings[0])

    def test_far_future_date_warning(self):
        future = (datetime.date.today() + datetime.timedelta(days=800)).isoformat()
        result = validation.validate_transaction(self.good(date=future), ACCOUNTS)
        self.assertTrue(result.ok)
        self.assertTrue(result.warnings)

    def test_message_formatting(self):
        result = validation.ValidationResult(errors=["a"], warnings=["b"])
        self.assertEqual(result.message(), "- a\n- Warning: b")


class TestOtherRecords(unittest.TestCase):
    def test_account(self):
        self.assertTrue(validation.validate_account("Petty Cash", ["Cash"]).ok)
        self.assertFalse(validation.validate_account("  cash ", ["Cash"]).ok)
        self.assertFalse(validation.validate_account("", []).ok)

    def test_vendor(self):
        self.assertTrue(validation.validate_vendor({"name": "Acme", "email": "a@b.co"}, ["Other"]).ok)
        self.assertIn("already exists", validation.validate_vendor({"name": "ACME"}, ["Acme"]).errors[0])
        self.assertIn("Email", validation.validate_vendor({"name": "Acme", "email": "nope"}, []).errors[0])
        self.assertIn("required", validation.validate_vendor({"name": " "}, []).errors[0])

    def test_customer(self):
        existing = [{"Customer_Company_Name": "Globex", "Customer_First_Name": "Hank", "Customer_Last_Name": "Scorpio"}]
        good = {"company": "Globex", "first_name": "Hank", "last_name": "Scorpio", "address": "1 Volcano Ln"}
        self.assertTrue(validation.validate_customer(good, []).ok)
        self.assertIn("already exists", validation.validate_customer(good, existing).errors[0])
        self.assertFalse(validation.validate_customer({"address": "x"}, []).ok)
        self.assertFalse(validation.validate_customer({"company": "Globex"}, []).ok)

    def test_service(self):
        good = {"description": "Consulting hour", "price": "150.00", "taxable": "False"}
        result = validation.validate_service(good, ["Other"])
        self.assertTrue(result.ok)
        self.assertEqual(result.cleaned["price"], 15000)
        self.assertFalse(validation.validate_service(dict(good, price="abc"), []).ok)
        self.assertFalse(validation.validate_service(dict(good, taxable=""), []).ok)
        self.assertFalse(validation.validate_service(good, ["consulting hour"]).ok)
        self.assertTrue(validation.validate_service(dict(good, price="0"), []).ok)

    def test_line_item(self):
        self.assertTrue(validation.validate_line_item("2").ok)
        self.assertTrue(validation.validate_line_item("1.5").ok)
        self.assertFalse(validation.validate_line_item("0").ok)
        self.assertFalse(validation.validate_line_item("two").ok)
        self.assertFalse(validation.validate_line_item("").ok)
        self.assertFalse(validation.validate_line_item("2", sku_selected=False).ok)

    def test_invoice(self):
        fields = {"customer_id": 3, "status": "Due", "due_date": "2025-12-31"}
        self.assertTrue(validation.validate_invoice(fields, [["S1", "x", "$1.00", "1", "$1.00"]]).ok)
        self.assertFalse(validation.validate_invoice(fields, []).ok)
        self.assertFalse(validation.validate_invoice(dict(fields, customer_id=""), [[1]]).ok)
        self.assertFalse(validation.validate_invoice(dict(fields, due_date="soon"), [[1]]).ok)
        paid = dict(fields, status="Paid")
        self.assertIn("Deposit account is required.", validation.validate_invoice(paid, [[1]]).errors)
        self.assertFalse(validation.validate_invoice(dict(paid, deposit_account="15001 Sales"), [[1]], asset_account_ids=["10002"]).ok)
        ar = validation.validate_invoice(dict(paid, deposit_account="10006 Accounts Receivable"), [[1]], asset_account_ids=["10002", "10006"])
        self.assertIn("not a deposit account", ar.errors[0])
        ok = validation.validate_invoice(dict(paid, deposit_account="10002 Checking"), [[1]], asset_account_ids=["10002"])
        self.assertTrue(ok.ok)
        self.assertEqual(ok.cleaned["deposit_account"], "10002")
        self.assertFalse(validation.validate_invoice(fields, [[1]] * 11).ok)

    def test_parse_percent(self):
        from decimal import Decimal
        self.assertEqual(validation.parse_percent("6.25"), Decimal("0.0625"))
        self.assertEqual(validation.parse_percent("6.25%"), Decimal("0.0625"))
        self.assertEqual(validation.parse_percent(""), Decimal("0"))
        self.assertEqual(validation.parse_percent("0.00"), Decimal("0"))
        for bad in ["abc", "6,25", "101", "-1", "6.25 percent"]:
            with self.assertRaises(ValueError, msg=bad):
                validation.parse_percent(bad)

    def test_database_properties(self):
        import tempfile
        folder = tempfile.mkdtemp()
        good = {"business_name": "Alpha Corp.", "address": "1 Main St", "sales_tax": "6.25", "save_location": folder, "receipts_location": folder}
        result = validation.validate_database_properties(good)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.cleaned["db_name"], "Alpha_Corp.icb")
        self.assertEqual(str(result.cleaned["sales_tax"]), "0.0625")
        bad = validation.validate_database_properties(dict(good, sales_tax="6.25 percent", business_name="", save_location="/no/such/dir"))
        self.assertEqual(len(bad.errors), 3)
        self.assertTrue(any("not a number" in e for e in bad.errors))
        self.assertTrue(any("filekey folder does not exist" in e for e in bad.errors))
        existing = os.path.join(folder, "Alpha_Corp_.icb")
        open(existing, "w").close()
        dup = validation.validate_database_properties(good, existing_file=existing)
        self.assertIn("already exists", dup.errors[0])
        self.assertTrue(validation.validate_database_properties(good, new_database=False, existing_file=existing).ok)
        self.assertFalse(validation.validate_database_properties(dict(good, business_name="&&&"), existing_file=None).ok)
        self.assertEqual(validation.database_file_stem("O'Brien & Sons"), "O_Brien_Sons")
        self.assertEqual(validation.database_file_stem("  Café 24/7 "), "Caf_24_7")
        self.assertEqual(validation.database_file_stem("123 Main"), "B_123_Main")
        self.assertEqual(validation.database_file_stem("a:b"), "a_b")

    def test_reconciliation_inputs(self):
        result = validation.validate_reconciliation_inputs("2025-03-31", "$8,057.82")
        self.assertTrue(result.ok)
        self.assertEqual(result.cleaned, {"statement_date": "2025-03-31", "statement_balance": 805782})
        self.assertFalse(validation.validate_reconciliation_inputs("", "").ok)
        self.assertTrue(validation.validate_reconciliation_inputs("2025-03-31", "0").ok)


if __name__ == "__main__":
    unittest.main()

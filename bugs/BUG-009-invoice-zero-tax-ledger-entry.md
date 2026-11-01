# BUG-009 — Invoices with no sales tax tried to post a zero-amount ledger entry

- **Status:** Resolved in 1.3 (ST-008)
- **Priority:** P1
- **Area:** Invoicing / ledger
- **Affected environment:** Databases with sales tax set to 0.00

## Description

Every invoice status change inserted a "Sales Tax Payable" ledger entry even when the tax
was zero. The ledger has `CHECK (Amount > 0)`, so the insert failed; the error was only
printed to the terminal and the status change carried on. Related: the check for an
existing payment used `Name LIKE 'Invoice 10001%'`, which also matched invoices
10010-10019, and cancel entries reused the original entry names, making the ledger hard
to audit.

## Resolution

`invoice_lifecycle.py` owns all transitions. Tax entries are skipped when the tax is zero,
transitions are checked by a state machine instead of name matching, cancel/refund entries
are named "Invoice N Canceled" / "Invoice N Refunded", and every change is recorded in
`tbl_Invoice_History`. Tests: `tests/test_invoice_lifecycle.py`.

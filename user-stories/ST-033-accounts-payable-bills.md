# ST-033 — Accounts payable / bills

- **Status:** Proposed, not started
- **Priority:** P3
- **Area:** Accounts Payable

## User story

As a business owner, I want to track vendor bills (amount, due date, status, payment)
the same way invoices track customer receivables, so my payables and receivables are
both visible and I can see what I owe, not just what I'm owed.

## Acceptance criteria

- [ ] A Bill entity exists with its own status machine (e.g. Due/Overdue/Paid/
      Canceled), modeled on `invoice_lifecycle.TRANSITIONS`.
- [ ] Creating a bill posts a ledger entry crediting Accounts Payable (13002) and
      debiting the relevant expense account(s); paying a bill posts the offsetting
      entry from a chosen asset account.
- [ ] Every bill status transition is recorded in a history table (mirroring
      `tbl_Invoice_History`) with the event, from/to status, amount, account, and
      ledger transaction IDs.
- [ ] A Bills tab/list exists parallel to the Invoices tab, showing outstanding and
      paid bills with due dates.
- [ ] The dashboard's liabilities figure reflects open bills via Accounts Payable,
      consistent with existing balance-sheet behavior.
- [ ] Bills are included in CSV export/import alongside the other exportable tables.
- [ ] Covered by a new test module mirroring `tests/test_invoice_lifecycle.py`'s
      structure and coverage.

## Scope notes

Mirrors `invoice_lifecycle.py`/`invoices.py` for vendor bills end-to-end.

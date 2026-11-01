# ST-008 — Invoice lifecycle clarity

- **Status:** Implemented
- **Priority:** P1
- **Area:** Invoicing

## User story

As a business owner, I want invoice status changes, payment recording, refunds, and
their ledger entries shown as a clear history so I can audit what happened.

## Acceptance criteria

- [x] A single state machine (`invoice_lifecycle.py`) owns every allowed status
      transition (Due/Overdue → Paid/Canceled, Paid → Refunded) and its ledger
      postings.
- [x] Every transition writes a row to `tbl_Invoice_History` recording the event,
      from/to status, amount, account used, and the ledger transaction IDs it created.
- [x] The Invoices/Point of Sale screen shows this history as a timeline for each
      invoice.
- [x] Invoices created before this table existed still show a derived timeline built
      from matching ledger entries by tracking code.
- [x] An invalid transition (e.g. Canceled → Paid) is refused with an explanation
      rather than silently applied.
- [x] Covered by `tests/test_invoice_lifecycle.py`.

## Implementation evidence

`invoice_lifecycle.py`, `tests/test_invoice_lifecycle.py`.

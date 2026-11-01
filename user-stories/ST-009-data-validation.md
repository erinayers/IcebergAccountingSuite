# ST-009 — Data validation

- **Status:** Implemented
- **Priority:** P1
- **Area:** Validation

## User story

As a user, I want invalid dates, amounts, missing required fields, and duplicate
records flagged before saving so errors are prevented at entry time.

## Acceptance criteria

- [x] `validation.py` checks transactions (including edits and CSV imports), accounts,
      vendors, customers, services, invoice line items, and invoices before anything is
      written.
- [x] Checks include required fields, valid dates, positive amounts, existing and
      distinct accounts, and duplicate names/records.
- [x] A probable duplicate transaction (same name, date, amount, and accounts) prompts
      for confirmation instead of blocking or silently saving.
- [x] Validation errors are field-level (not just a generic message) and shown inline
      next to the offending field; the form stays open with entered data intact.
- [x] Covered by `tests/test_validation.py`.

## Implementation evidence

`validation.py`, `tests/test_validation.py`.

# ST-019 — Focused data-entry forms

- **Status:** Implemented
- **Priority:** P2
- **Area:** Forms

## User story

As a user entering transactions or invoices, I want forms grouped into logical
sections with visible required fields and inline validation so I can complete them
with fewer mistakes.

## Acceptance criteria

- [x] The New Transaction form is grouped into logical sections (Details / Accounts /
      Notes / Receipt) with a legend explaining required-field markers.
- [x] Validation errors are shown inline, above or next to the offending field, with
      the field itself highlighted — not just in a generic dialog.
- [x] Vendor, customer, service, and account forms share the same
      legend/inline-message/focus/Enter-to-submit conventions.
- [x] Covered by the forms test suite (`TestForms`) and `tests/test_validation.py`.

## Implementation evidence

`validation.py` (`ValidationResult.error_fields()`), `tests/test_validation.py`.

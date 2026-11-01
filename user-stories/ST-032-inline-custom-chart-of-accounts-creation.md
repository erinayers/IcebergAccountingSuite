# ST-032 — Inline custom chart-of-accounts creation

- **Status:** Proposed, not started
- **Priority:** P3
- **Area:** Chart of Accounts

## User story

As a bookkeeper, I want to create a new custom account directly from the New
Transaction form and the vendor form (not only from the Dashboard's "+ New account"),
so I can record a ledger entry or set up a vendor against an account that doesn't
exist yet without losing my place or re-entering data.

## Acceptance criteria

- [ ] The account picker on the New Transaction form (both debit and credit account
      fields) offers an explicit "+ Add new account" option alongside existing
      accounts.
- [ ] Choosing it opens the same account-creation form used by the Dashboard's
      "+ New account" (same fields, same validation via `validation.validate_account`,
      same numbering via `records.add_account`) — not a second, divergent
      implementation.
- [ ] On successful creation, the new account is selected immediately in the field the
      user opened it from, and any other in-progress field values on the transaction
      form are preserved (not cleared).
- [ ] The vendor form gains the same "+ Add new account" affordance wherever an
      account is selected (if/when a vendor-linked account field exists).
- [ ] Attempting to create a duplicate-named account from either entry point produces
      the same validation error as doing so from the Dashboard.
- [ ] Covered by new tests mirroring `tests/test_api_records.py`'s existing
      account-creation coverage, exercised through the transaction/vendor flow rather
      than only the direct API call.

## Scope notes

Reuses `records.add_account`/`validation.validate_account` instead of duplicating
them, so the behavior stays identical to the Dashboard's "+ New account".

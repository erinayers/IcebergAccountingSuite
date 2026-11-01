# ST-006 — Reconciliation

- **Status:** Implemented
- **Priority:** P1
- **Area:** Reconciliation

## User story

As a bookkeeper, I want to reconcile an account against a statement and see unmatched
transactions so I can confirm balances.

## Acceptance criteria

- [x] A Reconcile Account flow is reachable from the Ledger tab and from an account's
      register.
- [x] The user enters a statement date and ending balance, then selects (clears)
      transactions from a candidate list.
- [x] The cleared balance, the difference from the statement balance, and the
      still-unmatched list update live as transactions are toggled.
- [x] The reconciliation can only be completed when the cleared balance matches the
      statement balance exactly.
- [x] Cleared transactions are flagged with a `Reconciled_Date`; completed statements
      are stored in `tbl_Reconciliations` with history.
- [x] A completed reconciliation can be undone, unflagging its transactions.
- [x] Documented in `docs/RECONCILIATION.md`; covered by `tests/test_reconciliation.py`.

## Implementation evidence

`reconciliation.py`, `docs/RECONCILIATION.md`, `tests/test_reconciliation.py`.

# ST-038 — Ledger and record change history with undo

- **Status:** Proposed, not started
- **Priority:** P3
- **Area:** Audit Trail

## User story

As a user, I want edits to ledger entries, accounts, vendors, and customers tracked
with an old/new value history and an "undo last change" action (matching the pattern
reconciliation already uses), so mistakes are visible and recoverable.

## Acceptance criteria

- [ ] A shared change-log table records, for each edit to a ledger entry, account,
      vendor, or customer: which record, which fields changed, their old and new
      values, who/when (timestamp), and what kind of change (create/update/delete).
- [ ] An "undo last change" action is available per record type, modeled on
      `reconciliation.undo_last`, that reverts the most recent change and
      removes/marks its log entry.
- [ ] The change log itself is visible to the user (e.g. in the console log or a
      dedicated history view), not just stored silently in the database.
- [ ] Undoing a change that has downstream dependencies (e.g. an account edit after
      transactions reference it) either safely no-ops the dependent parts or clearly
      explains why it can't be undone — it never leaves the books in an inconsistent
      state.
- [ ] Covered by tests for each of the four record types, including an
      undo-after-multiple-edits case (undo only reverts the single most recent
      change).

## Scope notes

Generalizes `reconciliation.undo_last`'s pattern into a shared mechanism; do not
re-invent a second undo implementation per record type.

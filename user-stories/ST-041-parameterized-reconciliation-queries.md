# ST-041 — Parameterized reconciliation queries

- **Status:** Implemented
- **Priority:** P4
- **Area:** SQL Safety

## User story

As a maintainer, I want `reconciliation.py`'s SQL to use parameters instead of string
interpolation, consistent with the "SQL takes parameters, never f-strings" rule
already followed in `records.py`/`invoices.py`/`books.py`, so the module can't be
misused with unexpected input and the codebase has one consistent pattern.

## Acceptance criteria

- [x] `start`, `complete`, `history`, and `undo_last` build every value (account IDs,
      dates, statement balances, transaction ID lists) using `?` placeholders, never
      f-string-interpolated values.
- [x] `IN (...)` clauses are built from the correct number of `?` placeholders bound
      to actual parameters, not a joined string of IDs embedded in the query text.
- [x] Table/column identifiers that cannot be parameterized (`ledger_name`, the
      `Reconciled_Date` column name) are documented in code as to why they remain
      string-built and why that's safe (internally derived/sanitized, not raw user
      text).
- [x] No behavior change: `tests/test_reconciliation.py`, `tests/test_api.py`, and
      `tests/test_api_records.py` all pass unchanged.
- [x] The full test suite passes (279/281; the 2 pre-existing failures are unrelated —
      one needed this exact commit to land, the other is an unrelated macOS
      path-separator test issue on Windows).

## Implementation evidence

Implemented in commit `0c089f9`. `reconciliation.py` now defines local `_rows`/`_one`
helpers mirroring `records.py`'s style instead of using
`db_calls.execute_read_query_dict`, which had the side effect of globally setting
`connection.row_factory`.

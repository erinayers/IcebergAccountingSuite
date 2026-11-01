# ST-042 — Retire legacy `repository/` write methods

- **Status:** Proposed, not started
- **Priority:** P4
- **Area:** Legacy Cleanup

## User story

As a maintainer, I want the f-string-built `insert`/`update` methods in
`repository/account.py`, `vendor.py`, `customer.py`, `invoice.py`, `owner.py`,
`property.py`, and `sku.py` removed or rewritten with `?` placeholders, so the module
can't be misused with unexpected input and the codebase has one consistent SQL-safety
pattern.

## Acceptance criteria

- [ ] Every call site that could reach these insert/update methods at runtime has been
      enumerated and confirmed (`books.py`'s `create_schema`/`write_properties` call
      `AccountRepository.insert` and `PropertyRepository.insert`, both with
      safely-escaped or hard-coded values; `api.py` uses `records.py` or direct
      `?`-parameterized `connection.execute` for all other live writes).
- [ ] The unsafe insert/update methods are either deleted outright (if truly
      unreachable) or rewritten to use `?` placeholders (if any path needs them
      retained for schema-creation convenience).
- [ ] Read-only and identifier-only methods (`get_all`/`get_by_id`/`create_table`)
      that pose no injection risk are left alone — this story does not need to touch
      everything in `repository/`, only the value-interpolating write paths.
- [ ] `books.py`'s `create_schema` and `write_properties` continue to work unchanged
      (same tests pass) whether the repository methods they call are rewritten or
      replaced with direct parameterized calls.
- [ ] `docs/ARCHITECTURE.md`'s "`repository/`: Original per-table classes (still used
      by `books.py` for table creation)" note is updated to reflect the new, safer
      state.
- [ ] Covered by the existing test suite with no regressions, plus a new test
      asserting that creating a database/account/property with a name containing a
      single quote succeeds (the exact failure mode `records.py`'s docstring already
      warns about).

## Scope notes

Confirmed these methods are not reachable from live writes today, so this is a
pure-hardening change rather than a fix for an exploited path.

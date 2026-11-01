# BUG-004 — Ledger tab crashes for transactions without a customer

- **Status:** Resolved in 1.3
- **Priority:** P0
- **Area:** Ledger tab / repositories
- **Affected environment:** All platforms

## Description

`load_ledger_tab` looked up the customer of every transaction. For a transaction with no
customer (every hand-entered transaction, and every imported one), `CustomerRepository.get_by_id("")`
built the query `WHERE Customer_ID = ;`, SQLite returned an error, and `execute_read_query_dict`
returned that error *as a string*. The repository's `if result and len(result) > 0: return result[0]`
then returned the first character of the error message (`"A"`), and the ledger code failed with
`TypeError: string indices must be integers`.

## Reproduction

1. Open a database and record a transaction from *Ledger → New Transaction* (no customer field).
2. Select *Ledger → View Ledger*.

## Resolution

- `CustomerRepository.get_by_id` returns `None` for empty/`None` ids without querying.
- Every repository `get_by_*` now checks `isinstance(result, list)` before indexing, so an SQL
  error can never be mistaken for a row.

Found while smoke-testing the CSV importer (ST-010); covered by the headless run in the
development notes and by `tests/test_data_exchange.py` (imported rows have no customer).

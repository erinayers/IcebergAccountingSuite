# BUG-007 — Invoice dates used the time Iceberg was started, not the current time

- **Status:** Resolved in 1.2 (ST-005)
- **Priority:** P1
- **Area:** Invoicing
- **Affected environment:** All platforms

## Description

`now = datetime.datetime.now()` was evaluated once at module import and reused for invoice
`Created_Time`, the paid date printed on invoices, transaction dates of invoice ledger entries,
and the default due date. An invoice created the day after launching Iceberg was dated the
previous day.

## Resolution

Every use now calls `iceberg_time.storage_timestamp()` / `iceberg_time.local_date_string()`
at the moment of the action; `icb_session.current_date` became a property.

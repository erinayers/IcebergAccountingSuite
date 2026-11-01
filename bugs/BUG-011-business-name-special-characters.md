# BUG-011 — Business names with punctuation produced an invalid ledger table

- **Status:** Resolved in 2.0
- **Priority:** P1
- **Area:** New Database
- **Affected environment:** All platforms

## Description

The database file stem was derived from the business name by replacing only spaces,
periods, commas, slashes, hyphens, and apostrophes with underscores. Any other character
(`&`, `:`, accented letters, …) survived into the ledger table name
`tbl_ledger_<stem>_CY<year>`, so a business called "O'Brien & Sons" got the table
`tbl_ledger_O_Brien_&_Sons_CY2026` and every ledger query failed with
`near "&": syntax error`. The new-database form accepted the name because it only checked
a handful of Windows-reserved characters.

## Resolution

`validation.database_file_stem` keeps letters, digits, and underscores only, collapses
runs of underscores, and prefixes a stem that starts with a digit (`B_123_Main`), so the
stem is always a valid SQL identifier and file name. The form shows "Business name must
contain at least one letter or digit" when nothing survives. Found by the API tests,
which create a database named "O'Brien & Sons" (`tests/test_api_records.py`).

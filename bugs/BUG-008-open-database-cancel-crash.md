# BUG-008 — Cancelling the Open Database dialog crashed the application

- **Status:** Resolved in 1.2 (ST-002)
- **Priority:** P1
- **Area:** Open Database
- **Affected environment:** All platforms

## Description

Selecting *Open* without choosing a file (or closing the dialog) ran
`fileloc[::-1].index("/")` on an empty string and raised `ValueError: substring not found`,
ending the session. A wrong key file raised `cryptography.fernet.InvalidToken`.

## Resolution

`open_database_from_key` validates the selection, and `db_calls.open_encrypted_database`
raises `DatabaseError` with a specific message (missing database, missing key, key does not
match, file damaged) that is shown in a dialog and the console. Tests:
`tests/test_db_calls.py::TestOpenDatabase`.

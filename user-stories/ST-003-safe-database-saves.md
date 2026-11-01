# ST-003 — Safe database saves

- **Status:** Implemented
- **Priority:** P0
- **Area:** Database Integrity

## User story

As a business owner, I want saves to be atomic and report success or failure so an
interrupted save does not silently leave my books incomplete.

## Acceptance criteria

- [x] `db_calls.save_encrypted_database()` writes to a temporary file in the same
      folder, flushes, and `fsync`s before replacing the live file.
- [x] The temp file is verified (decrypted and checked for a valid SQLite header)
      before it replaces the original via `os.replace` (atomic on Windows and POSIX).
- [x] Every save returns a `SaveResult` object stating success/failure, which is logged
      to the console/session log and surfaced to the user on failure.
- [x] Opening a database never writes decrypted/plaintext bytes to disk.
- [x] Closing the app saves and prompts for confirmation if the save fails, rather than
      discarding changes silently.
- [x] Covered by `tests/test_db_calls.py::TestSafeSaves` and `::TestOpenDatabase`.

## Implementation evidence

`db_calls.py` (`save_encrypted_database`, `SaveResult`), `tests/test_db_calls.py`.

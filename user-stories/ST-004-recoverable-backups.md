# ST-004 — Recoverable backups

- **Status:** Implemented
- **Priority:** P0
- **Area:** Backups

## User story

As a business owner, I want timestamped backups and a documented restore flow so I can
recover accounting data after accidental edits or file damage.

## Acceptance criteria

- [x] Every successful save writes a timestamped backup to
      `backups/<business>/<business>_<UTC stamp>.icb`.
- [x] The 20 newest backups per business are retained; older ones are pruned
      automatically.
- [x] Tools → Restore from Backup lists available backups in local time, newest first.
- [x] Restoring takes a safety copy of the current file before overwriting it, so a bad
      restore choice is itself recoverable.
- [x] The manual/offline restore procedure is documented in
      `docs/BACKUP_AND_RESTORE.md` for cases outside the app.
- [x] Covered by `tests/test_backups.py`.

## Implementation evidence

`backups.py`, `docs/BACKUP_AND_RESTORE.md`, `tests/test_backups.py`.

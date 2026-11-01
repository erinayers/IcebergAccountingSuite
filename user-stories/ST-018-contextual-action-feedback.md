# ST-018 — Contextual action feedback

- **Status:** Implemented
- **Priority:** P2
- **Area:** Feedback

## User story

As a user, I want clear success, error, loading, and unsaved-change feedback near the
action I just performed so I know whether a transaction or edit was saved.

## Acceptance criteria

- [x] A status indicator reports the outcome (success/error/warning/info) of the last
      action: saves, records added, validation failures, sorts, imports.
- [x] A save-state indicator distinguishes "Unsaved changes · autosave in mm:ss" from
      "All changes saved HH:MM".
- [x] Unsaved-change tracking is based on whether bookkeeping data actually changed
      (e.g. SQLite `total_changes`), excluding console-only writes, so autosave doesn't
      fire for no-op activity.
- [x] Covered by the feedback test suite (`TestFeedback`) and `tests/test_session.py`.

## Implementation evidence

`session.py` (unsaved-change tracking), `tests/test_session.py`.

# ST-002 — Clear startup errors

- **Status:** Implemented
- **Priority:** P0
- **Area:** Setup & Installation

## User story

As a user, I want actionable messages when GUI dependencies, Tcl/Tk, or data files are
unavailable so I can fix setup problems without interpreting a traceback.

## Acceptance criteria

- [x] `startup_checks.py` runs before any GUI import and checks: interpreter version,
      Tcl/Tk availability (with automatic `TCL_LIBRARY`/`TK_LIBRARY` repair), required
      third-party packages, poppler, data files, and session-log consistency.
- [x] Every failed check prints a plain-language description of the problem and a
      concrete fix, not a raw traceback.
- [x] `python startup_checks.py` can be run standalone to reproduce the same checks
      outside the full app.
- [x] Open Database failures (missing file, wrong key, damaged file) are reported in the
      status line/console rather than crashing.
- [x] Covered by `tests/test_startup_checks.py`.

## Implementation evidence

`startup_checks.py`, `tests/test_startup_checks.py`.

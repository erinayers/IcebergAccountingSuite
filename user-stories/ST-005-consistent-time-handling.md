# ST-005 — Consistent time handling

- **Status:** Implemented; BUG-001 awaiting Windows launch verification
- **Priority:** P0
- **Area:** Time & Scheduling

## User story

As a user in any timezone, I want timestamps and scheduled saves to work independently
of localized timezone names and daylight-saving changes.

## Acceptance criteria

- [x] Every stored timestamp is UTC in ISO 8601 format.
- [x] Displayed timestamps are converted to local time with a numeric `UTC±hh:mm`
      offset — never a localized timezone name string.
- [x] Legacy timestamp formats written by older versions still parse correctly.
- [x] Autosave scheduling and the on-screen clock use `time.monotonic()` rather than
      wall-clock deltas, so DST transitions and clock changes can't skip or double-fire
      a save.
- [x] Covered by `tests/test_iceberg_time.py` and `tests/test_iceberg_utils.py`.
- [ ] BUG-001 (startup timer crash with localized timezone names) is resolved in code;
      a real Windows launch has not yet re-confirmed it in the field.

## Implementation evidence

`iceberg_time.py`, `tests/test_iceberg_time.py`, `tests/test_iceberg_utils.py`,
`bugs/BUG-001-startup-timezone.md`.

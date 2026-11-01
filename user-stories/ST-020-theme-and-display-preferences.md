# ST-020 — Theme and display preferences

- **Status:** Implemented
- **Priority:** P2
- **Area:** Preferences

## User story

As a user, I want to choose comfortable text scaling and light or dark appearance so
the interface suits my display and working environment.

## Acceptance criteria

- [x] Light, Dark, and High-contrast appearance options are available.
- [x] At least five text-size options are available.
- [x] A "compact rows" density option is available.
- [x] Preferences are stored in `preferences.json`, validated on load, and fall back
      safely to defaults if the file is missing or invalid.
- [x] Covered by the preferences test suite (`TestPreferences`).

## Implementation evidence

`preferences.py`, `tests/test_preferences.py`.

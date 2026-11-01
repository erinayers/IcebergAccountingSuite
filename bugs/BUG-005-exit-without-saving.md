# BUG-005 — Closing the window skipped saving the open database

- **Status:** Resolved in 1.2 (ST-003)
- **Priority:** P0
- **Area:** Main event loop
- **Affected environment:** All platforms

## Description

Closing Iceberg with the window's X button hit an inner `if event == sg.WIN_CLOSED: break`
that bypassed the exit handling at the top of the loop, so neither the database nor the
session log was saved. *File → Exit Iceberg* saved the session log but never the database;
any work since the last 5-minute autosave was lost silently.

## Resolution

Both exit paths now run the same handler: the database is saved atomically with a
result shown in the console, a failed save asks whether to exit anyway, and the session
log is written afterwards (`iceberg.py`, main loop).

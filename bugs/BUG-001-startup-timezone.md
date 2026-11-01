# BUG-001 — Startup timer crashes with localized timezone names

- **Status:** Resolved in 1.2 (ST-005). The timer code was removed; clock and autosave use `iceberg_time` with monotonic scheduling and numeric offsets. Verified by `tests/test_iceberg_time.py` and a headless run of `iceberg.py`; a launch on the original Windows machine is still welcome as confirmation.
- **Priority:** P0
- **Area:** Startup and timer synchronization
- **Affected environment:** Windows, Python 3.13; timezone displayed as `Eastern Daylight Time`

## Description

The startup loop extracted seconds and minutes from fixed character positions in a formatted timestamp. On Windows the timezone name can be longer than the three-letter abbreviation assumed by those slices.

## Reproduction

1. Launch with `python iceberg.py` in an environment where the timestamp ends in `Eastern Daylight Time`.
2. Wait for the first GUI timer timeout.

Observed exception: `ValueError: invalid literal for int() with base 10: 't '`, at the startup timer initialization in `iceberg.py`.

## Expected

The timer initializes and the GUI remains open regardless of the localized timezone name.

## Resolution notes

`iceberg.py` was changed to read seconds and minutes from `datetime` rather than slicing timestamp strings. Relaunch the app on the reported setup to confirm the GUI stays open and autosave timing still behaves as intended.

## Fix (version 1.2)

- The `guitimer` / `synchronize_time` logic that compared seconds and minutes was removed. `refresh_clock_and_autosave()` in `iceberg.py` now refreshes the clock whenever the displayed minute changes and autosaves every 5 minutes using `time.monotonic()`, so the behaviour is independent of the timezone, its name, and daylight-saving changes.
- `iceberg_utils.get_current_time_info()` no longer uses `time.tzname[time.daylight]` (which printed "EDT" in December and produced localized names on Windows). Display strings now come from `iceberg_time.format_display()` and end with a numeric offset such as `(UTC-05:00)`.
- Timestamps written to the database are UTC ISO 8601 (`iceberg_time.storage_timestamp()`); legacy values are still parsed and displayed (`tests/test_iceberg_time.py`).

**Verification needed:** launch on the reporting machine, leave the window open past a minute boundary, confirm the clock updates and that an autosave entry appears in the console after 5 minutes with a database open.

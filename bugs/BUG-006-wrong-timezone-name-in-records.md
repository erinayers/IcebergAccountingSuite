# BUG-006 — Timestamps stored with the wrong zone name and in three different formats

- **Status:** Resolved in 1.2 (ST-005)
- **Priority:** P1
- **Area:** Timestamps
- **Affected environment:** All platforms

## Description

`get_current_time_info` used `time.tzname[time.daylight]`. `time.daylight` only says whether
the zone *has* DST, so every record was stamped with the daylight name all year: the sample
database shows "Sunday, 12/21/2025 - 17:47 EDT". Invoices stored `str(datetime.now())`
("2025-12-21 18:09:15.208771") while other tables stored the display string, so timestamps
could not be compared or sorted.

## Resolution

All `Created_Time`/`Edited_Time` values are written as UTC ISO 8601
(`iceberg_time.storage_timestamp()`); display converts to local time with a numeric offset.
Legacy strings are parsed and displayed correctly (`tests/test_iceberg_time.py`).

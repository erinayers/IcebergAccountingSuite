import datetime
import os
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import iceberg_time

EASTERN_STANDARD = datetime.timezone(datetime.timedelta(hours=-5))
INDIA = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


class TestStorageTimestamp(unittest.TestCase):
    def test_storage_timestamp_is_utc_iso_8601(self):
        moment = datetime.datetime(2025, 12, 21, 17, 47, 3, 999, tzinfo=EASTERN_STANDARD)
        self.assertEqual(iceberg_time.storage_timestamp(moment), "2025-12-21T22:47:03+00:00")

    def test_storage_timestamp_uses_utc_now_by_default(self):
        fixed = datetime.datetime(2024, 3, 10, 6, 59, 59, tzinfo=iceberg_time.UTC)
        with patch("iceberg_time.utc_now", return_value=fixed):
            self.assertEqual(iceberg_time.storage_timestamp(), "2024-03-10T06:59:59+00:00")

    def test_naive_moment_is_treated_as_local(self):
        with patch("iceberg_time.local_timezone", return_value=INDIA):
            naive = datetime.datetime(2025, 1, 1, 0, 30)
            self.assertEqual(iceberg_time.storage_timestamp(naive), "2024-12-31T19:00:00+00:00")

    def test_round_trip(self):
        stored = iceberg_time.storage_timestamp()
        parsed = iceberg_time.parse_timestamp(stored)
        self.assertEqual(iceberg_time.storage_timestamp(parsed), stored)


class TestParseTimestamp(unittest.TestCase):
    def test_parses_current_format(self):
        parsed = iceberg_time.parse_timestamp("2025-12-21T22:47:03+00:00")
        self.assertEqual(parsed, datetime.datetime(2025, 12, 21, 22, 47, 3, tzinfo=iceberg_time.UTC))

    def test_parses_legacy_display_strings_ignoring_wrong_zone_name(self):
        # Older versions wrote "EDT" in December because they used
        # time.tzname[time.daylight]; the name must not shift the time.
        with patch("iceberg_time.local_timezone", return_value=EASTERN_STANDARD):
            parsed = iceberg_time.parse_timestamp("Sunday, 12/21/2025  -  17:47 EDT")
            self.assertEqual(parsed, datetime.datetime(2025, 12, 21, 17, 47, tzinfo=EASTERN_STANDARD))
            with_seconds = iceberg_time.parse_timestamp("Sunday, 12/21/2025  -  17:49:24 EDT")
            self.assertEqual(with_seconds.second, 24)

    def test_parses_legacy_str_datetime(self):
        with patch("iceberg_time.local_timezone", return_value=EASTERN_STANDARD):
            parsed = iceberg_time.parse_timestamp("2025-12-21 18:09:15.208771")
            self.assertEqual(parsed.hour, 18)
            self.assertEqual(parsed.utcoffset(), datetime.timedelta(hours=-5))

    def test_parses_windows_style_zone_name(self):
        with patch("iceberg_time.local_timezone", return_value=EASTERN_STANDARD):
            parsed = iceberg_time.parse_timestamp("Sunday, 12/21/2025  -  17:47 Eastern Daylight Time")
            self.assertEqual((parsed.hour, parsed.minute), (17, 47))

    def test_empty_and_garbage(self):
        self.assertIsNone(iceberg_time.parse_timestamp(None))
        self.assertIsNone(iceberg_time.parse_timestamp(""))
        self.assertIsNone(iceberg_time.parse_timestamp("not a date"))


class TestDisplay(unittest.TestCase):
    def test_display_is_local_with_numeric_offset(self):
        with patch("iceberg_time.local_timezone", return_value=EASTERN_STANDARD):
            text = iceberg_time.display_timestamp("2025-12-21T22:47:03+00:00")
        self.assertEqual(text, "Sunday, 12/21/2025  -  17:47:03 (UTC-05:00)")

    def test_display_in_another_zone_for_same_record(self):
        with patch("iceberg_time.local_timezone", return_value=INDIA):
            text = iceberg_time.display_timestamp("2025-12-21T22:47:03+00:00", seconds=False)
        self.assertEqual(text, "Monday, 12/22/2025  -  04:17 (UTC+05:30)")

    def test_display_leaves_unparseable_values_visible(self):
        self.assertEqual(iceberg_time.display_timestamp("n/a"), "n/a")
        self.assertEqual(iceberg_time.display_timestamp(None), "")

    def test_format_display_without_seconds(self):
        moment = datetime.datetime(2023, 10, 27, 14, 30, 5, tzinfo=EASTERN_STANDARD)
        with patch("iceberg_time.local_timezone", return_value=EASTERN_STANDARD):
            self.assertEqual(iceberg_time.format_display(moment), "Friday, 10/27/2023  -  14:30 (UTC-05:00)")

    def test_utc_offset_label(self):
        self.assertEqual(iceberg_time.utc_offset_label(datetime.datetime(2025, 1, 1, tzinfo=iceberg_time.UTC)), "UTC+00:00")
        self.assertEqual(iceberg_time.utc_offset_label(datetime.datetime(2025, 1, 1, tzinfo=INDIA)), "UTC+05:30")
        self.assertEqual(iceberg_time.utc_offset_label(datetime.datetime(2025, 1, 1, tzinfo=EASTERN_STANDARD)), "UTC-05:00")


class TestDates(unittest.TestCase):
    def test_local_date_from_timestamp_crosses_midnight_correctly(self):
        # 23:30 UTC on the 21st is already the 22nd in India.
        with patch("iceberg_time.local_timezone", return_value=INDIA):
            self.assertEqual(iceberg_time.local_date_from_timestamp("2025-12-21T23:30:00+00:00"), "2025-12-22")
        with patch("iceberg_time.local_timezone", return_value=EASTERN_STANDARD):
            self.assertEqual(iceberg_time.local_date_from_timestamp("2025-12-21T23:30:00+00:00"), "2025-12-21")

    def test_local_date_from_timestamp_falls_back_to_today(self):
        fixed = datetime.datetime(2025, 6, 1, 12, 0, tzinfo=iceberg_time.UTC)
        with patch("iceberg_time.utc_now", return_value=fixed), patch("iceberg_time.local_timezone", return_value=iceberg_time.UTC):
            self.assertEqual(iceberg_time.local_date_from_timestamp("garbage"), "2025-06-01")
        self.assertEqual(iceberg_time.local_date_from_timestamp("garbage", default="2000-01-01"), "2000-01-01")

    def test_file_timestamp(self):
        moment = datetime.datetime(2025, 12, 21, 17, 47, 3, tzinfo=EASTERN_STANDARD)
        self.assertEqual(iceberg_time.file_timestamp(moment), "20251221T224703Z")


if __name__ == "__main__":
    unittest.main()

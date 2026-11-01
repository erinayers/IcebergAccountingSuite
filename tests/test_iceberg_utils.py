import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import datetime

# Add parent directory to path to import iceberg
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from iceberg_utils import get_current_time_info, format_currency, convert_dollars_to_cents, id_generator
import string


class TestIcebergUtils(unittest.TestCase):
    def test_get_current_time_info(self):
        # The display strings come from iceberg_time: local time with a neutral
        # numeric offset instead of a (possibly localized or wrong) zone name.
        zone = datetime.timezone(datetime.timedelta(hours=-4))
        fixed = datetime.datetime(2023, 10, 27, 14, 30, 5, tzinfo=zone)
        with patch('iceberg_time.local_timezone', return_value=zone), \
             patch('iceberg_time.utc_now', return_value=fixed):
            result_time, result_timestamp = get_current_time_info()

        self.assertEqual(result_time, "Friday, 10/27/2023  -  14:30 (UTC-04:00)")
        self.assertEqual(result_timestamp, "Friday, 10/27/2023  -  14:30:05 (UTC-04:00)")

    def test_format_currency(self):
        # Test zero
        self.assertEqual(format_currency(0), "$0.00")
        self.assertEqual(format_currency("0"), "$0.00")
        
        # Test positive integers
        self.assertEqual(format_currency(12345), "$123.45")
        self.assertEqual(format_currency(5), "$0.05")
        self.assertEqual(format_currency(50), "$0.50")
        self.assertEqual(format_currency(100), "$1.00")
        self.assertEqual(format_currency(100000), "$1,000.00")
        
        # Test negative integers
        self.assertEqual(format_currency(-12345), "($123.45)")
        self.assertEqual(format_currency(-5), "($0.05)")
        self.assertEqual(format_currency(-50), "($0.50)")
        self.assertEqual(format_currency(-100), "($1.00)")
        self.assertEqual(format_currency(-100000), "($1,000.00)")

        # Test custom symbol
        self.assertEqual(format_currency(100, symbol='€'), "€1.00")

    def test_convert_dollars_to_cents(self):
        # Test valid inputs
        self.assertEqual(convert_dollars_to_cents("1.00"), 100)
        self.assertEqual(convert_dollars_to_cents("0.05"), 5)
        self.assertEqual(convert_dollars_to_cents("123.45"), 12345)
        self.assertEqual(convert_dollars_to_cents(10.50), 1050)
        
        # Test zero
        self.assertEqual(convert_dollars_to_cents("0"), 0)
        self.assertEqual(convert_dollars_to_cents(0), 0)
        
        # Test invalid inputs (should return None based on current implementation returning None implicitly via pass)
        self.assertIsNone(convert_dollars_to_cents("invalid"))

    def test_id_generator(self):
        # Test default length (30)
        id1 = id_generator()
        self.assertEqual(len(id1), 30)
        
        # Test custom length
        id2 = id_generator(size=10)
        self.assertEqual(len(id2), 10)
        
        # Test default characters (uppercase + digits)
        allowed_chars = string.ascii_uppercase + string.digits
        for char in id1:
            self.assertIn(char, allowed_chars)
            
        # Test custom characters
        custom_chars = "ABC"
        id3 = id_generator(size=5, chars=custom_chars)
        self.assertEqual(len(id3), 5)
        for char in id3:
            self.assertIn(char, custom_chars)


if __name__ == '__main__':
    unittest.main()

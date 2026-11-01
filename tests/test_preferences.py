import os
import shutil
import sys
import tempfile
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import preferences


class TestPreferences(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp)

    def test_defaults_when_missing(self):
        self.assertEqual(preferences.load(self.temp), preferences.DEFAULTS)

    def test_round_trip(self):
        saved = preferences.save({"theme": "dark", "text_scale": 1.3, "compact": True}, self.temp)
        self.assertEqual(saved, {"theme": "dark", "text_scale": 1.3, "compact": True})
        self.assertEqual(preferences.load(self.temp), saved)
        self.assertTrue(os.path.isfile(os.path.join(self.temp, "preferences.json")))

    def test_invalid_values_are_normalized(self):
        self.assertEqual(preferences.normalize({"theme": "neon", "text_scale": "huge", "compact": 1}), {"theme": "light", "text_scale": 1.0, "compact": True})
        self.assertEqual(preferences.normalize({"text_scale": 1.2})["text_scale"], 1.15)
        self.assertEqual(preferences.normalize("garbage"), preferences.DEFAULTS)

    def test_damaged_file_does_not_raise(self):
        with open(os.path.join(self.temp, "preferences.json"), "w") as handle:
            handle.write("{not json")
        self.assertEqual(preferences.load(self.temp), preferences.DEFAULTS)

    def test_scale_labels(self):
        self.assertEqual(preferences.scale_label(1.0), "Default")
        self.assertEqual(preferences.scale_from_label("Extra large"), 1.5)
        self.assertEqual(preferences.scale_from_label("nonsense"), 1.0)


if __name__ == "__main__":
    unittest.main()
